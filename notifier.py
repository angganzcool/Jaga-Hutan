import requests
from typing import Dict, Any, Tuple
from geo_utils import generate_maps_links

class Notifier:
    def __init__(self, config):
        self.config = config

    def format_telegram_message(self, hotspot: Dict[str, Any], location_name: str, distance_km: float, radius_km: float) -> str:
        """
        Format pesan darurat untuk Telegram (HTML format).
        """
        maps = generate_maps_links(hotspot["latitude"], hotspot["longitude"])
        
        # Format scan time (UTC)
        time_str = hotspot.get("scan_time", "0000")
        if len(time_str) == 4:
            formatted_time = f"{time_str[:2]}:{time_str[2:]} UTC"
        else:
            formatted_time = f"{time_str} UTC"

        msg = (
            f"🚨 <b>PERINGATAN DINI HOTSPOT / TITIK API</b> 🚨\n\n"
            f"📍 <b>Area Pantau:</b> {location_name}\n"
            f"📏 <b>Jarak:</b> <b>{distance_km:.2f} km</b> dari titik pusat (Maks radius: {radius_km} km)\n"
            f"🎯 <b>Tingkat Keyakinan:</b> <code>{hotspot.get('confidence_label', 'Sedang')}</code>\n\n"
            f"🛰️ <b>Satelit:</b> {hotspot.get('satellite', 'VIIRS/MODIS')} ({hotspot.get('instrument', '-')})\n"
            f"📅 <b>Waktu Akuisisi:</b> {hotspot.get('scan_date')} {formatted_time}\n"
            f"🌡️ <b>Temperatur / Brightness:</b> {hotspot.get('brightness', 0):.1f} K\n"
            f"⚡ <b>Fire Radiative Power (FRP):</b> {hotspot.get('frp', 0):.1f} MW\n"
            f"🌐 <b>Koordinat:</b> <code>{hotspot['latitude']:.5f}, {hotspot['longitude']:.5f}</code>\n\n"
            f"🗺️ <b>Navigasi Lapangan:</b>\n"
            f"👉 <a href='{maps['google_maps']}'>Buka di Google Maps</a>\n"
            f"👉 <a href='{maps['osm']}'>Buka di OpenStreetMap</a>\n\n"
            f"⚠️ <i>Segera lakukan verifikasi lapangan ke tim patroli terdekat!</i>"
        )
        return msg

    def format_whatsapp_message(self, hotspot: Dict[str, Any], location_name: str, distance_km: float, radius_km: float) -> str:
        """
        Format pesan darurat untuk WhatsApp (*bold*, _italic_, `code`).
        """
        maps = generate_maps_links(hotspot["latitude"], hotspot["longitude"])
        time_str = hotspot.get("scan_time", "0000")
        if len(time_str) == 4:
            formatted_time = f"{time_str[:2]}:{time_str[2:]} UTC"
        else:
            formatted_time = f"{time_str} UTC"

        msg = (
            f"🚨 *PERINGATAN DINI HOTSPOT / TITIK API* 🚨\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📍 *Area Pantau:* {location_name}\n"
            f"📏 *Jarak:* {distance_km:.2f} km dari titik acuan (Radius pantau: {radius_km} km)\n"
            f"🎯 *Tingkat Keyakinan:* {hotspot.get('confidence_label', 'Sedang')}\n\n"
            f"🛰️ *Satelit:* {hotspot.get('satellite', 'VIIRS/MODIS')}\n"
            f"📅 *Waktu:* {hotspot.get('scan_date')} {formatted_time}\n"
            f"🌡️ *Suhu / Brightness:* {hotspot.get('brightness', 0):.1f} K\n"
            f"⚡ *FRP:* {hotspot.get('frp', 0):.1f} MW\n"
            f"🌐 *Koordinat:* `{hotspot['latitude']:.5f}, {hotspot['longitude']:.5f}`\n\n"
            f"🗺️ *Link Google Maps:*\n{maps['google_maps']}\n\n"
            f"⚠️ *Mohon tim patroli terdekat segera cek ke lokasi!*"
        )
        return msg

    def send_telegram(self, message: str) -> Tuple[bool, str]:
        """
        Mengirim notifikasi via Telegram Bot API.
        """
        token = self.config.telegram_bot_token
        chat_id = self.config.telegram_chat_id

        if not token or not chat_id:
            return False, "Token atau Chat ID Telegram belum dikonfigurasi"

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        }

        try:
            resp = requests.post(url, json=payload, timeout=15)
            if resp.status_code == 200:
                return True, "Success"
            return False, f"Telegram API Error ({resp.status_code}): {resp.text}"
        except Exception as e:
            return False, f"Telegram Connection Error: {e}"

    def send_whatsapp(self, message: str) -> Tuple[bool, str]:
        """
        Mengirim notifikasi ke WhatsApp melalui HTTP endpoint Baileys / WPPConnect / Evolution API.
        """
        endpoint = self.config.whatsapp_webhook_url
        target = self.config.whatsapp_target_number
        token = self.config.whatsapp_auth_token

        if not endpoint or not target:
            return False, "WhatsApp Webhook URL atau Target Number belum dikonfigurasi"

        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
            headers["apikey"] = token

        # Payload fleksibel yang didukung oleh berbagai engine Baileys / WPP
        payload = {
            "number": target,
            "target": target,
            "to": target,
            "jid": target,
            "message": message,
            "text": message
        }

        try:
            resp = requests.post(endpoint, json=payload, headers=headers, timeout=15)
            if resp.status_code in (200, 201, 202):
                return True, f"Success ({resp.status_code})"
            return False, f"WhatsApp Gateway Error ({resp.status_code}): {resp.text}"
        except Exception as e:
            return False, f"WhatsApp Connection Error: {e}"
