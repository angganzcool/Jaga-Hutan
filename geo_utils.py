import math
from typing import Tuple

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Menghitung jarak lingkaran besar antara dua koordinat geografis
    menggunakan rumus Haversine dalam satuan kilometer (KM).
    """
    R = 6371.0  # Radius bumi dalam kilometer

    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)

    a = (math.sin(d_lat / 2.0) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(d_lon / 2.0) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    distance = R * c
    return round(distance, 2)

def is_within_bounding_box(lat1: float, lon1: float, center_lat: float, center_lon: float, radius_km: float) -> bool:
    """
    Penyaringan cepat berbasis Bounding Box sebelum menghitung rumus Haversine.
    1 derajat latitude ~ 111.0 km
    1 derajat longitude ~ 111.0 * cos(latitude) km
    """
    # 1 derajat lintang konstan ~111 km
    lat_delta = radius_km / 111.0
    if abs(lat1 - center_lat) > lat_delta:
        return False

    # 1 derajat bujur bervariasi sesuai lintang
    cos_lat = math.cos(math.radians(center_lat))
    lon_delta = radius_km / (111.0 * max(0.01, abs(cos_lat)))
    if abs(lon1 - center_lon) > lon_delta:
        return False

    return True

def is_within_radius(lat1: float, lon1: float, center_lat: float, center_lon: float, radius_km: float) -> Tuple[bool, float]:
    """
    Memeriksa apakah koordinat (lat1, lon1) berada dalam radius tertentu dari (center_lat, center_lon).
    Menggunakan Bounding Box Pre-filter untuk memangkas 95%+ kalkulasi trigonometri.
    Mengembalikan (is_in_range, distance_km).
    """
    # Pre-filter cepat: jika di luar bounding box, pasti di luar radius
    if not is_within_bounding_box(lat1, lon1, center_lat, center_lon, radius_km):
        # Hitung jarak Euclidean proyeksi cepat jika berada di luar kotak
        d_lat = (lat1 - center_lat) * 111.0
        d_lon = (lon1 - center_lon) * 111.0 * math.cos(math.radians(center_lat))
        rough_dist = math.hypot(d_lat, d_lon)
        return (False, round(max(rough_dist, radius_km + 1.0), 2))

    # Jika lolos bounding box, hitung jarak presisi dengan Haversine
    dist = haversine_distance(lat1, lon1, center_lat, center_lon)
    return (dist <= radius_km, dist)

def normalize_confidence(conf_val) -> Tuple[str, str]:
    """
    Menormalkan tingkat kepercayaan (confidence) satelit VIIRS/MODIS.
    Output: (kode: 'low'|'nominal'|'high', label_tampilan: 'Low'|'Nominal'|'High'|'xx%')
    """
    if conf_val is None:
        return ("nominal", "Nominal")
    
    val_str = str(conf_val).strip().lower()
    
    # VIIRS uses: 'l' (low), 'n' (nominal), 'h' (high)
    if val_str in ('l', 'low'):
        return ("low", "Rendah (Low)")
    elif val_str in ('n', 'nominal'):
        return ("nominal", "Sedang (Nominal)")
    elif val_str in ('h', 'high'):
        return ("high", "Tinggi (High)")
    
    # MODIS uses numbers: 0 - 100 (%)
    try:
        val_num = float(val_str)
        if val_num < 40:
            return ("low", f"{int(val_num)}% (Rendah)")
        elif val_num < 75:
            return ("nominal", f"{int(val_num)}% (Sedang)")
        else:
            return ("high", f"{int(val_num)}% (Tinggi)")
    except ValueError:
        return ("nominal", val_str.capitalize())

def is_confidence_acceptable(hotspot_conf: str, min_conf_required: str) -> bool:
    """
    Mengecek apakah tingkat confidence hotspot memenuhi syarat minimal.
    Ranking: low (1) < nominal (2) < high (3)
    """
    rank_map = {"low": 1, "nominal": 2, "high": 3}
    hotspot_rank = rank_map.get(hotspot_conf.lower(), 2)
    min_rank = rank_map.get(min_conf_required.lower(), 2)
    return hotspot_rank >= min_rank

def generate_maps_links(lat: float, lon: float) -> dict:
    """
    Menghasilkan tautan langsung ke Google Maps dan OpenStreetMap.
    """
    return {
        "google_maps": f"https://www.google.com/maps?q={lat:.5f},{lon:.5f}",
        "osm": f"https://www.openstreetmap.org/?mlat={lat:.5f}&mlon={lon:.5f}#map=14/{lat:.5f}/{lon:.5f}"
    }
