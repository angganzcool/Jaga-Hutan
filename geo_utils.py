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

def is_within_radius(lat1: float, lon1: float, center_lat: float, center_lon: float, radius_km: float) -> Tuple[bool, float]:
    """
    Memeriksa apakah koordinat (lat1, lon1) berada dalam radius tertentu dari (center_lat, center_lon).
    Mengembalikan (is_in_range, distance_km).
    """
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
