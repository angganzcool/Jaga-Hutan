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

    def test_firms_day_range_is_limited_to_api_maximum(self):
        service = FirmsService(map_key="test-key", day_range=10)
        self.assertEqual(service.day_range, 5)

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

    def test_bounding_box_prefilter(self):
        from geo_utils import is_within_bounding_box
        # Titik dekat (-2.25, 113.85) dari (-2.2161, 113.9139), radius 30 km -> True
        self.assertTrue(is_within_bounding_box(-2.25, 113.85, -2.2161, 113.9139, 30.0))
        # Titik jauh (Papua) -> False
        self.assertFalse(is_within_bounding_box(-4.2000, 138.5000, -2.2161, 113.9139, 30.0))

    def test_batch_saving_and_frp_filtering(self):
        batch = [
            {
                "hotspot_uid": "batch_spot_1", "latitude": -2.25, "longitude": 113.85,
                "scan_date": "2026-10-19", "scan_time": "0600", "frp": 45.0,
                "location_id": "loc_test", "location_name": "Area Uji", "distance_km": 5.0,
            },
            {
                "hotspot_uid": "batch_spot_2", "latitude": -2.26, "longitude": 113.86,
                "scan_date": "2026-10-19", "scan_time": "0605", "frp": 5.0,
                "location_id": "loc_test", "location_name": "Area Uji", "distance_km": 6.0,
            }
        ]
        saved_count = self.db.save_hotspots_batch(batch)
        self.assertEqual(saved_count, 2)

        # Ambil semua titik
        all_spots = self.db.get_recent_hotspots(days=7, location_id="loc_test")
        self.assertGreaterEqual(len(all_spots), 2)

        # Ambil hanya titik dengan FRP >= 30 MW (hanya batch_spot_1 yang harus muncul)
        high_frp_spots = self.db.get_recent_hotspots(days=7, location_id="loc_test", min_frp=30.0)
        self.assertEqual(len(high_frp_spots), 1)
        self.assertEqual(high_frp_spots[0]["hotspot_uid"], "batch_spot_1")

    def test_cluster_alert_formatting(self):
        spots = [
            {"latitude": -2.25, "longitude": 113.85, "frp": 50.0, "distance_km": 4.5, "satellite": "VIIRS", "confidence_label": "Tinggi", "brightness": 350.0},
            {"latitude": -2.26, "longitude": 113.86, "frp": 12.0, "distance_km": 8.0, "satellite": "VIIRS", "confidence_label": "Sedang", "brightness": 320.0},
            {"latitude": -2.27, "longitude": 113.87, "frp": 25.0, "distance_km": 10.0, "satellite": "VIIRS", "confidence_label": "Tinggi", "brightness": 335.0},
            {"latitude": -2.28, "longitude": 113.88, "frp": 8.0, "distance_km": 12.0, "satellite": "MODIS", "confidence_label": "Sedang", "brightness": 315.0},
        ]
        tg_cluster = self.notifier.format_telegram_cluster_message(spots, "Hutan Lindung Area A", 25.0)
        self.assertIn("KLUSTER HOTSPOT TERDETEKSI", tg_cluster)
        self.assertIn("4 TITIK API", tg_cluster)
        self.assertIn("50.0 MW", tg_cluster)

        wa_cluster = self.notifier.format_whatsapp_cluster_message(spots, "Hutan Lindung Area A", 25.0)
        self.assertIn("*KLUSTER HOTSPOT TERDETEKSI (4 TITIK API)*", wa_cluster)

    def test_dashboard_and_health_endpoints(self):
        client = TestClient(web_app)
        dashboard = client.get("/")
        self.assertEqual(dashboard.status_code, 200)
        self.assertIn("Jaga Hutan", dashboard.text)
        self.assertEqual(client.get("/health/live").json(), {"status": "ok"})
        
        # Test endpoint hotspots dengan filter min_frp
        res = client.get("/api/hotspots?days=7&min_frp=10")
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.json(), list)

        # Test favicon
        fav = client.get("/favicon.ico")
        self.assertEqual(fav.status_code, 200)

        # Test air quality endpoint
        aq = client.get("/api/air-quality")
        self.assertEqual(aq.status_code, 200)
        self.assertIsInstance(aq.json(), list)

    def test_national_hotspots_without_posko(self):
        national_spot = {
            "hotspot_uid": "national_spot_papua",
            "latitude": -4.2000,
            "longitude": 138.5000,
            "brightness": 320.0,
            "scan_date": "2026-10-19",
            "scan_time": "0800",
            "satellite": "VIIRS_SNPP",
            "instrument": "VIIRS",
            "confidence_code": "nominal",
            "confidence_label": "Sedang",
            "frp": 18.5,
            "daynight": "D"
        }
        # Simpan titik nasional tanpa location_id
        saved = self.db.save_hotspot(national_spot)
        self.assertTrue(saved)

        # Query seluruh Indonesia (tanpa filter location_id)
        all_spots = self.db.get_recent_hotspots(days=7)
        self.assertTrue(any(s["hotspot_uid"] == "national_spot_papua" for s in all_spots))
        papua_spot = next(s for s in all_spots if s["hotspot_uid"] == "national_spot_papua")
        self.assertEqual(papua_spot["location_name"], "Wilayah Teritorial Indonesia")

        # Query posko spesifik (tidak boleh memunculkan titik nasional luar posko)
        posko_spots = self.db.get_recent_hotspots(days=7, location_id="loc_test")
        self.assertFalse(any(s["hotspot_uid"] == "national_spot_papua" for s in posko_spots))

if __name__ == "__main__":
    unittest.main()
