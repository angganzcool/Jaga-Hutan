import requests
import time
from typing import List, Dict, Any

INDONESIA_CITIES = [
    # Kalimantan (Area Karhutla & Gambut)
    {"id": "palangkaraya", "name": "Palangka Raya", "province": "Kalimantan Tengah", "lat": -2.2161, "lon": 113.9139},
    {"id": "pontianak", "name": "Pontianak", "province": "Kalimantan Barat", "lat": -0.0263, "lon": 109.3425},
    {"id": "banjarmasin", "name": "Banjarmasin", "province": "Kalimantan Selatan", "lat": -3.3194, "lon": 114.5908},
    {"id": "samarinda", "name": "Samarinda", "province": "Kalimantan Timur", "lat": -0.5022, "lon": 117.1537},
    {"id": "balikpapan", "name": "Balikpapan", "province": "Kalimantan Timur", "lat": -1.2654, "lon": 116.8312},
    {"id": "tarakan", "name": "Tarakan", "province": "Kalimantan Utara", "lat": 3.3270, "lon": 117.5925},
    {"id": "sampit", "name": "Sampit", "province": "Kalimantan Tengah", "lat": -2.5333, "lon": 112.9500},
    {"id": "ketapang", "name": "Ketapang", "province": "Kalimantan Barat", "lat": -1.8333, "lon": 109.9667},
    {"id": "singkawang", "name": "Singkawang", "province": "Kalimantan Barat", "lat": 0.9069, "lon": 108.9868},
    {"id": "bontang", "name": "Bontang", "province": "Kalimantan Timur", "lat": 0.1333, "lon": 117.5000},
    {"id": "berau", "name": "Berau", "province": "Kalimantan Timur", "lat": 2.1558, "lon": 117.4917},

    # Sumatera (Area Gambut & Karhutla)
    {"id": "pekanbaru", "name": "Pekanbaru", "province": "Riau", "lat": 0.5071, "lon": 101.4478},
    {"id": "dumai", "name": "Dumai", "province": "Riau", "lat": 1.6667, "lon": 101.4500},
    {"id": "jambi", "name": "Jambi", "province": "Jambi", "lat": -1.6101, "lon": 103.6131},
    {"id": "palembang", "name": "Palembang", "province": "Sumatera Selatan", "lat": -2.9909, "lon": 104.7565},
    {"id": "medan", "name": "Medan", "province": "Sumatera Utara", "lat": 3.5952, "lon": 98.6722},
    {"id": "padang", "name": "Padang", "province": "Sumatera Barat", "lat": -0.9471, "lon": 100.4172},
    {"id": "bandar_lampung", "name": "Bandar Lampung", "province": "Lampung", "lat": -5.4500, "lon": 105.2667},
    {"id": "banda_aceh", "name": "Banda Aceh", "province": "Aceh", "lat": 5.5483, "lon": 95.3238},
    {"id": "batam", "name": "Batam", "province": "Kepulauan Riau", "lat": 1.1301, "lon": 104.0529},
    {"id": "bengkulu", "name": "Bengkulu", "province": "Bengkulu", "lat": -3.8004, "lon": 102.2655},
    {"id": "pangkalpinang", "name": "Pangkal Pinang", "province": "Bangka Belitung", "lat": -2.1316, "lon": 106.1169},

    # Jawa & Bali
    {"id": "jakarta", "name": "Jakarta", "province": "DKI Jakarta", "lat": -6.2088, "lon": 106.8456},
    {"id": "bandung", "name": "Bandung", "province": "Jawa Barat", "lat": -6.9175, "lon": 107.6191},
    {"id": "semarang", "name": "Semarang", "province": "Jawa Tengah", "lat": -6.9667, "lon": 110.4167},
    {"id": "surabaya", "name": "Surabaya", "province": "Jawa Timur", "lat": -7.2575, "lon": 112.7521},
    {"id": "yogyakarta", "name": "Yogyakarta", "province": "DIY", "lat": -7.7956, "lon": 110.3695},
    {"id": "denpasar", "name": "Denpasar", "province": "Bali", "lat": -8.6705, "lon": 115.2126},

    # Sulawesi (Utara, Tengah, Selatan, Tenggara, Barat, Gorontalo)
    {"id": "makassar", "name": "Makassar", "province": "Sulawesi Selatan", "lat": -5.1477, "lon": 119.4327},
    {"id": "manado", "name": "Manado", "province": "Sulawesi Utara", "lat": 1.4748, "lon": 124.8428},
    {"id": "palu", "name": "Palu", "province": "Sulawesi Tengah", "lat": -0.9003, "lon": 119.8780},
    {"id": "kendari", "name": "Kendari", "province": "Sulawesi Tenggara", "lat": -3.9972, "lon": 122.5128},
    {"id": "gorontalo", "name": "Gorontalo", "province": "Gorontalo", "lat": 0.5435, "lon": 123.0568},
    {"id": "mamuju", "name": "Mamuju", "province": "Sulawesi Barat", "lat": -2.6770, "lon": 118.8890},
    {"id": "baubau", "name": "Baubau", "province": "Sulawesi Tenggara", "lat": -5.4667, "lon": 122.6000},
    {"id": "luwuk", "name": "Luwuk", "province": "Sulawesi Tengah", "lat": -0.9516, "lon": 122.7875},
    {"id": "kotamobagu", "name": "Kotamobagu", "province": "Sulawesi Utara", "lat": 0.7410, "lon": 124.3142},

    # Nusa Tenggara
    {"id": "mataram", "name": "Mataram", "province": "NTB", "lat": -8.5833, "lon": 116.1167},
    {"id": "bima", "name": "Bima", "province": "NTB", "lat": -8.4608, "lon": 118.7267},
    {"id": "kupang", "name": "Kupang", "province": "NTT", "lat": -10.1772, "lon": 123.6070},
    {"id": "labuan_bajo", "name": "Labuan Bajo", "province": "NTT", "lat": -8.4964, "lon": 119.8877},
    {"id": "maumere", "name": "Maumere", "province": "NTT", "lat": -8.6200, "lon": 122.2133},
    {"id": "ende", "name": "Ende", "province": "NTT", "lat": -8.8432, "lon": 121.6623},
    {"id": "waingapu", "name": "Waingapu", "province": "NTT", "lat": -9.6567, "lon": 120.2641},

    # Maluku & Maluku Utara
    {"id": "ambon", "name": "Ambon", "province": "Maluku", "lat": -3.6954, "lon": 128.1814},
    {"id": "ternate", "name": "Ternate", "province": "Maluku Utara", "lat": 0.7905, "lon": 127.3828},
    {"id": "tidore", "name": "Tidore", "province": "Maluku Utara", "lat": 0.6974, "lon": 127.4429},
    {"id": "tual", "name": "Tual", "province": "Maluku", "lat": -5.6294, "lon": 132.7486},
    {"id": "tobelo", "name": "Tobelo", "province": "Maluku Utara", "lat": 1.7283, "lon": 128.0094},
    {"id": "saumlaki", "name": "Saumlaki", "province": "Maluku", "lat": -7.9786, "lon": 131.2981},

    # Papua (Papua, Papua Barat, Papua Tengah, Papua Selatan, Papua Pegunungan)
    {"id": "jayapura", "name": "Jayapura", "province": "Papua", "lat": -2.5489, "lon": 140.7181},
    {"id": "sorong", "name": "Sorong", "province": "Papua Barat Daya", "lat": -0.8761, "lon": 131.2558},
    {"id": "manokwari", "name": "Manokwari", "province": "Papua Barat", "lat": -0.8615, "lon": 134.0620},
    {"id": "merauke", "name": "Merauke", "province": "Papua Selatan", "lat": -8.4991, "lon": 140.4017},
    {"id": "timika", "name": "Timika", "province": "Papua Tengah", "lat": -4.5467, "lon": 136.8837},
    {"id": "nabire", "name": "Nabire", "province": "Papua Tengah", "lat": -3.3667, "lon": 135.4833},
    {"id": "biak", "name": "Biak", "province": "Papua", "lat": -1.1764, "lon": 136.0820},
    {"id": "wamena", "name": "Wamena", "province": "Papua Pegunungan", "lat": -4.0975, "lon": 138.9442},
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
