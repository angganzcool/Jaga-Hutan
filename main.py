import argparse
import time
import sys
import os
import logging
from datetime import datetime, timezone

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from config import get_config
from firms_service import FirmsService
from geo_utils import is_within_radius, is_confidence_acceptable
from database import Database
from notifier import Notifier

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("jaga_hutan.monitor")

def _run_monitoring_cycle(cfg, db, firms, notifier, force_simulation: bool = False):
    print(f"\n==================================================")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Memulai Siklus Monitoring Jaga Hutan...")
    print(f"==================================================")

    locations = cfg.locations
    if not locations:
        print("[WARN] Tidak ada lokasi pantau yang terdaftar di locations.json!")
        return

    print(f"📍 Memantau {len(locations)} lokasi sasaran.")

    # 1. Ambil data dari NASA FIRMS (atau Simulasi)
    if force_simulation or cfg.simulation_enabled:
        raw_hotspots = firms.generate_mock_hotspots()
        logger.warning("MODE SIMULASI aktif; memuat %s titik simulasi", len(raw_hotspots))
    else:
        raw_hotspots = firms.fetch_country_hotspots()
        print(f"🛰️ Mengambil {len(raw_hotspots)} titik api dari satelit NASA FIRMS.")

    if not raw_hotspots:
        print("✅ Tidak ada data hotspot baru terdeteksi.")
        return

    # Simpan seluruh titik api se-Indonesia ke database untuk Web GIS Nasional
    db.save_hotspots_batch(raw_hotspots)
    print(f"🗺️ Disimpan ke database: {len(raw_hotspots)} titik api se-Indonesia (Web GIS Nasional).")

    total_matches = 0
    total_alerts_dispatched = 0

    # 2. Iterasi per area pantau
    for loc in locations:
        loc_records = []
        for spot in raw_hotspots:
            in_radius, dist_km = is_within_radius(
                spot["latitude"], spot["longitude"],
                loc.latitude, loc.longitude,
                loc.radius_km
            )

            if not in_radius:
                continue

            # Cek ambang batas keyakinan (confidence)
            if not is_confidence_acceptable(spot["confidence_code"], loc.min_confidence):
                continue

            spot_record = dict(spot)
            spot_record["location_id"] = loc.id
            spot_record["location_name"] = loc.name
            spot_record["distance_km"] = dist_km
            loc_records.append(spot_record)

        if not loc_records:
            continue

        total_matches += len(loc_records)
        # Batch insert seluruh titik ke database dalam 1 transaksi
        db.save_hotspots_batch(loc_records)

        print(f"🔥 {len(loc_records)} HOTSPOT DITEMUKAN di {loc.name}")

        # Saring titik yang belum pernah di-alert (cooldown check)
        unalerted_tg = [
            s for s in loc_records
            if not db.was_alerted_recently(s["hotspot_uid"], loc.id, "telegram", cfg.alert_cooldown_hours)
        ]
        unalerted_wa = [
            s for s in loc_records
            if not db.was_alerted_recently(s["hotspot_uid"], loc.id, "whatsapp", cfg.alert_cooldown_hours)
        ]

        # 3. Kirim Alert Telegram
        if cfg.telegram_enabled and loc.alert_telegram and unalerted_tg:
            if len(unalerted_tg) > 3:
                # Mode Kluster / Ringkasan untuk mencegah spam dan rate-limit
                tg_msg = notifier.format_telegram_cluster_message(unalerted_tg, loc.name, loc.radius_km)
                success, res_msg = notifier.send_telegram(tg_msg)
                status_str = "sent" if success else "failed"
                for s in unalerted_tg:
                    db.log_alert(s["hotspot_uid"], loc.id, "telegram", cfg.telegram_chat_id, status_str, res_msg)
                if success:
                    total_alerts_dispatched += 1
                    print(f"   [TELEGRAM] ✅ Alert Kluster ({len(unalerted_tg)} titik) terkirim ke chat {cfg.telegram_chat_id}")
                else:
                    print(f"   [TELEGRAM] ❌ Gagal kirim kluster: {res_msg}")
            else:
                # Kirim individual jika sedikit (<= 3 titik)
                for s in unalerted_tg:
                    tg_msg = notifier.format_telegram_message(s, loc.name, s["distance_km"], loc.radius_km)
                    success, res_msg = notifier.send_telegram(tg_msg)
                    status_str = "sent" if success else "failed"
                    db.log_alert(s["hotspot_uid"], loc.id, "telegram", cfg.telegram_chat_id, status_str, res_msg)
                    if success:
                        total_alerts_dispatched += 1
                        print(f"   [TELEGRAM] ✅ Alert terkirim ({s['hotspot_uid']})")
                    else:
                        print(f"   [TELEGRAM] ❌ Gagal kirim: {res_msg}")
                    time.sleep(0.5)

        # 4. Kirim Alert WhatsApp
        if cfg.whatsapp_enabled and loc.alert_whatsapp and unalerted_wa:
            if len(unalerted_wa) > 3:
                wa_msg = notifier.format_whatsapp_cluster_message(unalerted_wa, loc.name, loc.radius_km)
                success, res_msg = notifier.send_whatsapp(wa_msg)
                status_str = "sent" if success else "failed"
                for s in unalerted_wa:
                    db.log_alert(s["hotspot_uid"], loc.id, "whatsapp", cfg.whatsapp_target_number, status_str, res_msg)
                if success:
                    total_alerts_dispatched += 1
                    print(f"   [WHATSAPP] ✅ Alert Kluster ({len(unalerted_wa)} titik) terkirim ke {cfg.whatsapp_target_number}")
                else:
                    print(f"   [WHATSAPP] ❌ Gagal kirim kluster: {res_msg}")
            else:
                for s in unalerted_wa:
                    wa_msg = notifier.format_whatsapp_message(s, loc.name, s["distance_km"], loc.radius_km)
                    success, res_msg = notifier.send_whatsapp(wa_msg)
                    status_str = "sent" if success else "failed"
                    db.log_alert(s["hotspot_uid"], loc.id, "whatsapp", cfg.whatsapp_target_number, status_str, res_msg)
                    if success:
                        total_alerts_dispatched += 1
                        print(f"   [WHATSAPP] ✅ Alert terkirim ({s['hotspot_uid']})")
                    else:
                        print(f"   [WHATSAPP] ❌ Gagal kirim: {res_msg}")
                    time.sleep(0.5)

    print(f"🏁 Siklus selesai: {total_matches} titik masuk radius, {total_alerts_dispatched} notifikasi dikirim.")

def run_monitoring_cycle(cfg, db, firms, notifier, force_simulation: bool = False):
    """Jalankan satu siklus dengan lock lintas proses web/worker."""
    if not db.acquire_monitoring_lock():
        raise RuntimeError("Siklus monitoring lain sedang berjalan")
    try:
        return _run_monitoring_cycle(cfg, db, firms, notifier, force_simulation)
    finally:
        db.release_monitoring_lock()

def send_test_alert(cfg, notifier):
    print("\n[TEST] Mengirim pesan pengujian notifikasi...")
    sample_spot = {
        "hotspot_uid": "test_spot_001",
        "latitude": -2.2161,
        "longitude": 113.9139,
        "brightness": 345.2,
        "scan_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "scan_time": "0630",
        "satellite": "Suomi NPP (Uji Coba)",
        "instrument": "VIIRS",
        "confidence_code": "high",
        "confidence_label": "Tinggi (High)",
        "frp": 32.5,
    }

    if cfg.telegram_enabled:
        msg = notifier.format_telegram_message(sample_spot, "Lokasi Uji Coba (Kalteng)", 5.2, 20.0)
        success, res = notifier.send_telegram(msg)
        print(f"Telegram Test Result: {'SUCCESS' if success else 'FAILED'} -> {res}")
    else:
        print("Telegram Alert dinonaktifkan di .env (TELEGRAM_ENABLED=false).")

    if cfg.whatsapp_enabled:
        msg = notifier.format_whatsapp_message(sample_spot, "Lokasi Uji Coba (Kalteng)", 5.2, 20.0)
        success, res = notifier.send_whatsapp(msg)
        print(f"WhatsApp Test Result: {'SUCCESS' if success else 'FAILED'} -> {res}")
    else:
        print("WhatsApp Alert dinonaktifkan di .env (WHATSAPP_ENABLED=false).")

def main():
    parser = argparse.ArgumentParser(description="Jaga Hutan - Sistem Monitoring & Notifikasi Hotspot Karhutla")
    parser.add_argument("--once", action="store_true", help="Jalankan 1 siklus monitoring lalu selesai (cocok untuk Linux cron job)")
    parser.add_argument("--daemon", action="store_true", help="Jalankan scheduler terus menerus di background")
    parser.add_argument("--simulate", action="store_true", help="Gunakan data simulasi titik api")
    parser.add_argument("--test-alert", action="store_true", help="Kirim sampel notifikasi uji coba ke Telegram & WhatsApp")
    parser.add_argument("--stats", action="store_true", help="Tampilkan statistik database hotspot")
    
    args = parser.parse_args()

    cfg = get_config()
    db = Database(cfg.db_path)
    firms = FirmsService(
        map_key=cfg.firms_map_key,
        source=cfg.firms_source,
        country=cfg.firms_country,
        day_range=cfg.firms_day_range
    )
    notifier = Notifier(cfg)

    if args.stats:
        stats = db.get_stats()
        print("\n📊 STATISTIK SISTEM JAGA HUTAN")
        print(f"- Total Hotspot Tersimpan: {stats['total_hotspots']}")
        print(f"- Hotspot Terdeteksi Hari Ini: {stats['today_hotspots']}")
        print(f"- Total Alert Terkirim: {stats['total_alerts_sent']}")
        return

    if args.test_alert:
        send_test_alert(cfg, notifier)
        return

    if args.daemon:
        print(f"[DAEMON] Mode loop aktif. Memeriksa data setiap {cfg.check_interval_minutes} menit.")
        try:
            while True:
                run_monitoring_cycle(cfg, db, firms, notifier, force_simulation=args.simulate)
                print(f"[DAEMON] Tidur selama {cfg.check_interval_minutes} menit...")
                time.sleep(cfg.check_interval_minutes * 60)
        except KeyboardInterrupt:
            print("\n[DAEMON] Dihentikan oleh pengguna.")
            sys.exit(0)
    else:
        # Default run once
        run_monitoring_cycle(cfg, db, firms, notifier, force_simulation=args.simulate)

if __name__ == "__main__":
    main()
