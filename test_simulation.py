import unittest
from fastapi.testclient import TestClient
from geo_utils import haversine_distance, is_within_radius, normalize_confidence, is_confidence_acceptable, generate_maps_links
from database import Database
from firms_service import FirmsService
from notifier import Notifier
from config import AppConfig, MonitoredLocation
from app import app as web_app

class TestJagaHutan(unittest.TestCase):
    def setUp(self):
        # Gunakan in-memory SQLite database untuk testing agar terisolasi & cepat
        self.db = Database(":memory:")
        self.cfg = AppConfig(
            db_path=":memory:",
            telegram_enabled=False,
            whatsapp_enabled=False,
            locations=[
                MonitoredLocation(
                    id="loc_test",
                    name="Area Uji Palangka Raya",
                    latitude=-2.2161,
                    longitude=113.9139,
                    radius_km=30.0,
                    min_confidence="nominal"
                )
            ]
        )
        self.notifier = Notifier(self.cfg)

    def test_haversine_distance(self):
        # Palangka Raya ke titik terdekat (~4 km)
        dist = haversine_distance(-2.2161, 113.9139, -2.2500, 113.9139)
        self.assertGreater(dist, 3.0)
        self.assertLess(dist, 5.0)

    def test_radius_filter(self):
        # Titik di dalam radius 30 km
        in_range, dist = is_within_radius(-2.2500, 113.8500, -2.2161, 113.9139, 30.0)
        self.assertTrue(in_range)
        self.assertLessEqual(dist, 30.0)

        # Titik di luar radius (Papua)
        out_range, dist_out = is_within_radius(-4.2000, 138.5000, -2.2161, 113.9139, 30.0)
        self.assertFalse(out_range)

    def test_confidence_normalization(self):
        self.assertEqual(normalize_confidence("h"), ("high", "Tinggi (High)"))
        self.assertEqual(normalize_confidence("n"), ("nominal", "Sedang (Nominal)"))
        self.assertEqual(normalize_confidence("l"), ("low", "Rendah (Low)"))
        self.assertEqual(normalize_confidence(85), ("high", "85% (Tinggi)"))
        self.assertTrue(is_confidence_acceptable("high", "nominal"))
        self.assertFalse(is_confidence_acceptable("low", "nominal"))

    def test_database_and_deduplication(self):
        sample_spot = {
            "hotspot_uid": "test_spot_100",
            "latitude": -2.2500,
            "longitude": 113.8500,
            "brightness": 340.0,
            "scan_date": "2026-08-25",
            "scan_time": "0600",
            "satellite": "VIIRS_SNPP",
            "instrument": "VIIRS",
            "confidence_code": "high",
            "confidence_label": "Tinggi",
            "frp": 15.0,
            "daynight": "D",
            "location_id": "loc_test",
            "location_name": "Area Uji",
            "distance_km": 8.5
        }

        # Simpan pertama kali
        is_new = self.db.save_hotspot(sample_spot)
        self.assertTrue(is_new)

        # Simpan kedua kali (harus diabaikan karena duplikat)
        is_new_again = self.db.save_hotspot(sample_spot)
        self.assertFalse(is_new_again)

        # Cek status alert (belum pernah dikirim)
        was_alerted = self.db.was_alerted_recently("test_spot_100", "loc_test", "telegram", 12)
        self.assertFalse(was_alerted)

        # Log alert pengiriman
        self.db.log_alert("test_spot_100", "loc_test", "telegram", "123456", "sent", "OK")

        # Cek status alert (sekarang harus True / cooldown aktif)
        was_alerted_now = self.db.was_alerted_recently("test_spot_100", "loc_test", "telegram", 12)
        self.assertTrue(was_alerted_now)

    def test_same_hotspot_can_belong_to_multiple_locations(self):
        sample_spot = {
            "hotspot_uid": "shared_spot_1", "latitude": -2.25, "longitude": 113.85,
            "scan_date": "2026-08-25", "scan_time": "0600",
            "location_id": "loc_a", "location_name": "Area A", "distance_km": 5.0,
        }
        self.assertTrue(self.db.save_hotspot(sample_spot))
        sample_spot.update(location_id="loc_b", location_name="Area B", distance_km=7.0)
        self.assertTrue(self.db.save_hotspot(sample_spot))
        self.assertEqual(len(self.db.get_recent_hotspots(days=30_000)), 2)

    def test_missing_firms_key_never_falls_back_to_simulation(self):
        service = FirmsService(map_key="")
        with self.assertRaises(RuntimeError):
            service.fetch_country_hotspots()

    def test_monitoring_lock_prevents_overlapping_cycles(self):
        self.assertTrue(self.db.acquire_monitoring_lock())
        self.assertFalse(self.db.acquire_monitoring_lock())
        self.db.release_monitoring_lock()
        self.assertTrue(self.db.acquire_monitoring_lock())
        self.db.release_monitoring_lock()

    def test_message_formatting(self):
        sample_spot = {
            "hotspot_uid": "test_spot_100",
            "latitude": -2.2500,
            "longitude": 113.8500,
            "brightness": 340.0,
            "scan_date": "2026-08-25",
            "scan_time": "0600",
            "satellite": "VIIRS_SNPP",
            "instrument": "VIIRS",
            "confidence_label": "Tinggi",
            "frp": 15.0,
        }
        tg_msg = self.notifier.format_telegram_message(sample_spot, "Area Uji", 8.5, 30.0)
        self.assertIn("PERINGATAN DINI", tg_msg)
        self.assertIn("google.com/maps", tg_msg)

        wa_msg = self.notifier.format_whatsapp_message(sample_spot, "Area Uji", 8.5, 30.0)
        self.assertIn("*PERINGATAN DINI HOTSPOT", wa_msg)

    def test_dashboard_and_health_endpoints(self):
        client = TestClient(web_app)
        dashboard = client.get("/")
        self.assertEqual(dashboard.status_code, 200)
        self.assertIn("Jaga Hutan", dashboard.text)
        self.assertEqual(client.get("/health/live").json(), {"status": "ok"})

if __name__ == "__main__":
    unittest.main()
