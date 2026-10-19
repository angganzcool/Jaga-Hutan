import requests
import time
from typing import List, Dict, Any

INDONESIA_CITIES = [
    # Kalimantan (Area Karhutla Utama)
    {"id": "palangkaraya", "name": "Palangka Raya", "province": "Kalimantan Tengah", "lat": -2.2161, "lon": 113.9139},
    {"id": "pontianak", "name": "Pontianak", "province": "Kalimantan Barat", "lat": -0.0263, "lon": 109.3425},
    {"id": "banjarmasin", "name": "Banjarmasin", "province": "Kalimantan Selatan", "lat": -3.3194, "lon": 114.5908},
    {"id": "samarinda", "name": "Samarinda", "province": "Kalimantan Timur", "lat": -0.5022, "lon": 117.1537},
    {"id": "tarakan", "name": "Tarakan", "province": "Kalimantan Utara", "lat": 3.3270, "lon": 117.5925},
    {"id": "sampit", "name": "Sampit (Kotawaringin)", "province": "Kalimantan Tengah", "lat": -2.5333, "lon": 112.9500},
    {"id": "ketapang", "name": "Ketapang", "province": "Kalimantan Barat", "lat": -1.8333, "lon": 109.9667},

    # Sumatera (Area Gambut & Karhutla)
    {"id": "pekanbaru", "name": "Pekanbaru", "province": "Riau", "lat": 0.5071, "lon": 101.4478},
    {"id": "dumai", "name": "Dumai", "province": "Riau", "lat": 1.6667, "lon": 101.4500},
    {"id": "jambi", "name": "Jambi", "province": "Jambi", "lat": -1.6101, "lon": 103.6131},
    {"id": "palembang", "name": "Palembang", "province": "Sumatera Selatan", "lat": -2.9909, "lon": 104.7565},
    {"id": "medan", "name": "Medan", "province": "Sumatera Utara", "lat": 3.5952, "lon": 98.6722},
    {"id": "padang", "name": "Padang", "province": "Sumatera Barat", "lat": -0.9471, "lon": 100.4172},
    {"id": "bandar_lampung", "name": "Bandar Lampung", "province": "Lampung", "lat": -5.4500, "lon": 105.2667},
    {"id": "banda_aceh", "name": "Banda Aceh", "province": "Aceh", "lat": 5.5483, "lon": 95.3238},

    # Jawa & Bali
    {"id": "jakarta", "name": "Jakarta", "province": "DKI Jakarta", "lat": -6.2088, "lon": 106.8456},
    {"id": "bandung", "name": "Bandung", "province": "Jawa Barat", "lat": -6.9175, "lon": 107.6191},
    {"id": "semarang", "name": "Semarang", "province": "Jawa Tengah", "lat": -6.9667, "lon": 110.4167},
    {"id": "surabaya", "name": "Surabaya", "province": "Jawa Timur", "lat": -7.2575, "lon": 112.7521},
    {"id": "yogyakarta", "name": "Yogyakarta", "province": "DIY", "lat": -7.7956, "lon": 110.3695},
    {"id": "denpasar", "name": "Denpasar", "province": "Bali", "lat": -8.6705, "lon": 115.2126},

    # Nusa Tenggara, Sulawesi, Maluku, Papua
    {"id": "mataram", "name": "Mataram", "province": "NTB", "lat": -8.5833, "lon": 116.1167},
    {"id": "kupang", "name": "Kupang", "province": "NTT", "lat": -10.1772, "lon": 123.6070},
    {"id": "makassar", "name": "Makassar", "province": "Sulawesi Selatan", "lat": -5.1477, "lon": 119.4327},
    {"id": "manado", "name": "Manado", "province": "Sulawesi Utara", "lat": 1.4748, "lon": 124.8428},
    {"id": "palu", "name": "Palu", "province": "Sulawesi Tengah", "lat": -0.9003, "lon": 119.8780},
    {"id": "kendari", "name": "Kendari", "province": "Sulawesi Tenggara", "lat": -3.9972, "lon": 122.5128},
    {"id": "ambon", "name": "Ambon", "province": "Maluku", "lat": -3.6954, "lon": 128.1814},
    {"id": "jayapura", "name": "Jayapura", "province": "Papua", "lat": -2.5489, "lon": 140.7181},
    {"id": "sorong", "name": "Sorong", "province": "Papua Barat Daya", "lat": -0.8761, "lon": 131.2558},
]

def get_aqi_details(aqi: int) -> Dict[str, str]:
    """Mengembalikan level kategori, deskripsi, dan palet warna standar IQAir."""
    if aqi <= 50:
        return {
            "level": "Baik",
            "category": "Good",
            "color": "#84cc16",  # Hijau
            "textColor": "#0f172a",
            "desc": "Kualitas udara memuaskan dan berisiko sangat kecil."
        }
    elif aqi <= 100:
        return {
            "level": "Sedang",
            "category": "Moderate",
            "color": "#eab308",  # Kuning
            "textColor": "#0f172a",
            "desc": "Kualitas udara dapat diterima bagi sebagian besar orang."
        }
    elif aqi <= 150:
        return {
            "level": "Tidak Sehat (Sensitif)",
            "category": "Unhealthy for Sensitive Groups",
            "color": "#f97316",  # Oranye
            "textColor": "#ffffff",
            "desc": "Anak-anak dan penderita pernapasan rentan terganggu."
        }
    elif aqi <= 200:
        return {
            "level": "Tidak Sehat",
            "category": "Unhealthy",
            "color": "#ef4444",  # Merah
            "textColor": "#ffffff",
            "desc": "Setiap orang dapat mulai merasakan dampak buruk asap/polusi."
        }
    elif aqi <= 300:
        return {
            "level": "Sangat Tidak Sehat",
            "category": "Very Unhealthy",
            "color": "#a855f7",  # Ungu
            "textColor": "#ffffff",
            "desc": "Peringatan darurat kesehatan. Seluruh populasi terancam."
        }
    else:
        return {
            "level": "Berbahaya",
            "category": "Hazardous",
            "color": "#7f1d1d",  # Cokelat Marun
            "textColor": "#ffffff",
            "desc": "Kondisi darurat kabut asap parah. Hindari semua aktivitas luar!"
        }

_aqi_cache = {
    "data": [],
    "last_fetched": 0
}

def fetch_indonesia_air_quality() -> List[Dict[str, Any]]:
    """
    Mengambil data kualitas udara live se-Indonesia dari Open-Meteo Air Quality API
    dengan caching 15 menit agar loading instan dan hemat jaringan.
    """
    now = time.time()
    if _aqi_cache["data"] and (now - _aqi_cache["last_fetched"]) < 900:
        return _aqi_cache["data"]

    lats = [str(c["lat"]) for c in INDONESIA_CITIES]
    lons = [str(c["lon"]) for c in INDONESIA_CITIES]

    url = (
        f"https://air-quality-api.open-meteo.com/v1/air-quality"
        f"?latitude={','.join(lats)}&longitude={','.join(lons)}"
        f"&current=us_aqi,pm2_5,pm10"
    )

    results = []
    try:
        resp = requests.get(url, timeout=12)
        if resp.status_code == 200:
            payload = resp.json()
            # Open-Meteo returns a list when multiple coordinates are passed
            items = payload if isinstance(payload, list) else [payload]
            
            for idx, c in enumerate(INDONESIA_CITIES):
                city_data = items[idx] if idx < len(items) else {}
                current = city_data.get("current", {})
                raw_aqi = current.get("us_aqi") or 45
                aqi = int(raw_aqi)
                pm2_5 = float(current.get("pm2_5") or 0.0)
                pm10 = float(current.get("pm10") or 0.0)
                details = get_aqi_details(aqi)

                results.append({
                    "id": c["id"],
                    "city": c["name"],
                    "province": c["province"],
                    "latitude": c["lat"],
                    "longitude": c["lon"],
                    "aqi": aqi,
                    "pm2_5": round(pm2_5, 1),
                    "pm10": round(pm10, 1),
                    "level": details["level"],
                    "category": details["category"],
                    "color": details["color"],
                    "textColor": details["textColor"],
                    "desc": details["desc"],
                    "time": current.get("time", "")
                })

            _aqi_cache["data"] = results
            _aqi_cache["last_fetched"] = now
            return results
    except Exception as e:
        print(f"[AQI WARN] Gagal mengambil data live Open-Meteo: {e}")

    # Fallback jika offline / timeout API
    if _aqi_cache["data"]:
        return _aqi_cache["data"]

    fallback_results = []
    for c in INDONESIA_CITIES:
        fallback_aqi = 65 if "Kalimantan" in c["province"] or "Riau" in c["province"] else 40
        details = get_aqi_details(fallback_aqi)
        fallback_results.append({
            "id": c["id"],
            "city": c["name"],
            "province": c["province"],
            "latitude": c["lat"],
            "longitude": c["lon"],
            "aqi": fallback_aqi,
            "pm2_5": 18.0,
            "pm10": 25.0,
            "level": details["level"],
            "category": details["category"],
            "color": details["color"],
            "textColor": details["textColor"],
            "desc": details["desc"],
            "time": "Perkiraan"
        })
    return fallback_results
