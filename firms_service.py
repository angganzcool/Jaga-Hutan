import csv
import io
import requests
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from geo_utils import normalize_confidence

class FirmsService:
    BASE_URL = "https://firms.modaps.eosdis.nasa.gov/api"
    # Bounding box Indonesia (west, south, east, north), used when the FIRMS
    # country endpoint is temporarily unavailable or rejects the request.
    INDONESIA_BBOX = (94.5, -11.5, 141.5, 6.5)

    def __init__(self, map_key: str, source: str = "VIIRS_SNPP_NRT", country: str = "IDN", day_range: int = 1):
        self.map_key = map_key.strip()
        self.source = source
        self.country = country
        # FIRMS currently accepts a maximum range of five days per API query.
        self.day_range = max(1, min(day_range, 5))

    def is_configured(self) -> bool:
        return bool(self.map_key) and self.map_key != "YOUR_NASA_FIRMS_MAP_KEY"

    def fetch_country_hotspots(self) -> List[Dict[str, Any]]:
        """
        Mengambil data hotspot dari NASA FIRMS API per negara (default: IDN/Indonesia).
        Endpoint: https://firms.modaps.eosdis.nasa.gov/api/country/csv/{MAP_KEY}/{SOURCE}/{COUNTRY}/{DAY_RANGE}
        """
        if not self.is_configured():
            raise RuntimeError(
                "FIRMS_MAP_KEY belum dikonfigurasi. Gunakan --simulate atau "
                "SIMULATION_MODE=true hanya untuk data simulasi."
            )

        url = f"{self.BASE_URL}/country/csv/{self.map_key}/{self.source}/{self.country}/{self.day_range}"
        print(f"[FIRMS API] Requesting data dari: {url.replace(self.map_key, '***MAP_KEY***')}")

        try:
            resp = requests.get(url, timeout=30)
            if resp.status_code == 200:
                return self._parse_csv_data(resp.text)
            elif resp.status_code == 403 or resp.status_code == 401:
                print(f"[FIRMS API ERROR] MAP_KEY tidak valid atau unauthorized (Status {resp.status_code}).")
                return []
            else:
                print(f"[FIRMS API WARN] Country query gagal (Status {resp.status_code}); mencoba area fallback.")
                if self.country.upper() == "IDN":
                    return self.fetch_area_hotspots(*self.INDONESIA_BBOX)
                print(f"[FIRMS API ERROR] Tidak ada area fallback untuk negara {self.country}.")
                return []
        except Exception as e:
            print(f"[FIRMS API ERROR] Exception saat request: {e}")
            return []

    def fetch_area_hotspots(self, min_lon: float, min_lat: float, max_lon: float, max_lat: float) -> List[Dict[str, Any]]:
        """
        Mengambil data hotspot berdasarkan Bounding Box area (W, S, E, N).
        Endpoint: https://firms.modaps.eosdis.nasa.gov/api/area/csv/{MAP_KEY}/{SOURCE}/{W,S,E,N}/{DAY_RANGE}
        """
        if not self.is_configured():
            raise RuntimeError(
                "FIRMS_MAP_KEY belum dikonfigurasi. Mode simulasi harus diaktifkan secara eksplisit."
            )

        bbox = f"{min_lon:.4f},{min_lat:.4f},{max_lon:.4f},{max_lat:.4f}"
        url = f"{self.BASE_URL}/area/csv/{self.map_key}/{self.source}/{bbox}/{self.day_range}"
        
        try:
            resp = requests.get(url, timeout=30)
            if resp.status_code == 200:
                return self._parse_csv_data(resp.text)
            else:
                print(f"[FIRMS API ERROR] Area query failed ({resp.status_code}): {resp.text[:200]}")
                return []
        except Exception as e:
            print(f"[FIRMS API ERROR] Exception: {e}")
            return []

    def _parse_csv_data(self, csv_text: str) -> List[Dict[str, Any]]:
        """
        Mengubah output CSV NASA FIRMS menjadi list of standardized dictionary.
        """
        hotspots = []
        if not csv_text or csv_text.strip().startswith("No data"):
            return hotspots

        f = io.StringIO(csv_text.strip())
        reader = csv.DictReader(f)

        for row in reader:
            try:
                lat = float(row.get("latitude", 0))
                lon = float(row.get("longitude", 0))
                scan_date = row.get("acq_date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
                scan_time = row.get("acq_time", "0000").zfill(4)
                satellite = row.get("satellite", self.source)
                instrument = row.get("instrument", "VIIRS/MODIS")
                
                # Brightness temperature (Kelvin)
                # VIIRS: bright_ti4, MODIS: brightness
                bright_val = row.get("bright_ti4") or row.get("brightness") or "0"
                brightness = float(bright_val)

                # Fire Radiative Power (MW)
                frp_val = row.get("frp", "0")
                frp = float(frp_val) if frp_val else 0.0

                # Confidence
                raw_conf = row.get("confidence", "nominal")
                conf_code, conf_label = normalize_confidence(raw_conf)

                daynight = row.get("daynight", "D")

                # Buat UID unik untuk deduplikasi
                # Format: lat_lon_date_time_sat
                hotspot_uid = f"{lat:.4f}_{lon:.4f}_{scan_date}_{scan_time}_{satellite}"

                hotspots.append({
                    "hotspot_uid": hotspot_uid,
                    "latitude": lat,
                    "longitude": lon,
                    "brightness": brightness,
                    "scan_date": scan_date,
                    "scan_time": scan_time,
                    "satellite": satellite,
                    "instrument": instrument,
                    "confidence_code": conf_code,
                    "confidence_label": conf_label,
                    "frp": frp,
                    "daynight": daynight,
                })
            except Exception as e:
                # Lewatkan baris rusak jika ada
                continue

        return hotspots

    def generate_mock_hotspots(self) -> List[Dict[str, Any]]:
        """
        Menghasilkan data simulasi titik api di sekitar wilayah Indonesia (Kalimantan & Sumatera)
        untuk pengujian lokal tanpa membutuhkan MAP_KEY aktif.
        """
        now = datetime.now(timezone.utc)
        today = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H%M")

        mock_data = [
            # Titik 1: Dekat Palangka Raya (~12 km dari pusat kota)
            {
                "hotspot_uid": f"-2.2500_113.8500_{today}_{time_str}_VIIRS_SIM",
                "latitude": -2.2500,
                "longitude": 113.8500,
                "brightness": 348.5,
                "scan_date": today,
                "scan_time": time_str,
                "satellite": "Suomi NPP (Simulasi)",
                "instrument": "VIIRS",
                "confidence_code": "high",
                "confidence_label": "Tinggi (High)",
                "frp": 24.8,
                "daynight": "D",
            },
            # Titik 2: Dekat Taman Nasional Sebangau (~18 km)
            {
                "hotspot_uid": f"-2.5200_113.8600_{today}_{time_str}_VIIRS_SIM",
                "latitude": -2.5200,
                "longitude": 113.8600,
                "brightness": 325.2,
                "scan_date": today,
                "scan_time": time_str,
                "satellite": "NOAA-20 (Simulasi)",
                "instrument": "VIIRS",
                "confidence_code": "nominal",
                "confidence_label": "Sedang (Nominal)",
                "frp": 12.3,
                "daynight": "D",
            },
            # Titik 3: Dekat Tesso Nilo Riau (~8 km dari batas)
            {
                "hotspot_uid": f"-0.1200_101.5500_{today}_{time_str}_MODIS_SIM",
                "latitude": -0.1200,
                "longitude": 101.5500,
                "brightness": 339.0,
                "scan_date": today,
                "scan_time": time_str,
                "satellite": "Terra (Simulasi)",
                "instrument": "MODIS",
                "confidence_code": "high",
                "confidence_label": "88% (Tinggi)",
                "frp": 45.1,
                "daynight": "D",
            },
            # Titik 4: Di Papua (Jauh dari lokasi pantau - harusnya terfilter keluar)
            {
                "hotspot_uid": f"-4.2000_138.5000_{today}_{time_str}_VIIRS_SIM",
                "latitude": -4.2000,
                "longitude": 138.5000,
                "brightness": 310.0,
                "scan_date": today,
                "scan_time": time_str,
                "satellite": "NOAA-21 (Simulasi)",
                "instrument": "VIIRS",
                "confidence_code": "low",
                "confidence_label": "Rendah (Low)",
                "frp": 4.5,
                "daynight": "D",
            }
        ]
        return mock_data
