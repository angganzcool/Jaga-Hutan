"""
geo_resolver.py
Modul resolusi spasial cerdas untuk menentukan nama Kabupaten/Kota dan Provinsi
berdasarkan koordinat titik api (latitude, longitude) di seluruh Nusantara.
Bekerja 100% offline tanpa dependensi eksternal.
"""

import math
from typing import Dict, Any, Optional

# Basis data titik referensi Kabupaten / Kota strategis se-Indonesia
INDONESIA_CENTERS = [
    # --- RIAU (Area Rawan Karhutla) ---
    {"name": "Kab. Pelalawan", "province": "Riau", "lat": 0.2833, "lon": 101.9500},
    {"name": "Kab. Rokan Hilir", "province": "Riau", "lat": 1.7000, "lon": 100.8000},
    {"name": "Kab. Bengkalis", "province": "Riau", "lat": 1.4833, "lon": 102.1333},
    {"name": "Kab. Siak", "province": "Riau", "lat": 0.9833, "lon": 101.9833},
    {"name": "Kota Dumai", "province": "Riau", "lat": 1.6667, "lon": 101.4500},
    {"name": "Kota Pekanbaru", "province": "Riau", "lat": 0.5071, "lon": 101.4478},
    {"name": "Kab. Indragiri Hilir", "province": "Riau", "lat": -0.3333, "lon": 103.1500},
    {"name": "Kab. Indragiri Hulu", "province": "Riau", "lat": -0.5500, "lon": 102.3000},
    {"name": "Kab. Kampar", "province": "Riau", "lat": 0.3333, "lon": 101.0500},
    {"name": "Kab. Rokan Hulu", "province": "Riau", "lat": 0.9000, "lon": 100.4500},
    {"name": "Kab. Kepulauan Meranti", "province": "Riau", "lat": 0.9833, "lon": 102.7000},
    {"name": "Kab. Kuantan Singingi", "province": "Riau", "lat": -0.5333, "lon": 101.5500},

    # --- SUMATERA SELATAN (Area Gambut & Karhutla) ---
    {"name": "Kab. Ogan Komering Ilir (OKI)", "province": "Sumatera Selatan", "lat": -3.4000, "lon": 105.2000},
    {"name": "Kab. Banyuasin", "province": "Sumatera Selatan", "lat": -2.8833, "lon": 104.3833},
    {"name": "Kab. Musi Banyuasin (Sekayu)", "province": "Sumatera Selatan", "lat": -2.6000, "lon": 103.7000},
    {"name": "Kab. Ogan Ilir", "province": "Sumatera Selatan", "lat": -3.4333, "lon": 104.6500},
    {"name": "Kab. Muara Enim", "province": "Sumatera Selatan", "lat": -3.6500, "lon": 103.7833},
    {"name": "Kab. Musi Rawas", "province": "Sumatera Selatan", "lat": -3.1000, "lon": 103.0000},
    {"name": "Kab. Lahat", "province": "Sumatera Selatan", "lat": -3.7833, "lon": 103.5333},
    {"name": "Kota Palembang", "province": "Sumatera Selatan", "lat": -2.9909, "lon": 104.7565},
    {"name": "Kota Lubuklinggau", "province": "Sumatera Selatan", "lat": -3.2961, "lon": 102.8614},

    # --- JAMBI ---
    {"name": "Kota Jambi", "province": "Jambi", "lat": -1.6101, "lon": 103.6131},
    {"name": "Kab. Muaro Jambi", "province": "Jambi", "lat": -1.5833, "lon": 103.8000},
    {"name": "Kab. Tanjung Jabung Barat", "province": "Jambi", "lat": -1.0000, "lon": 103.2000},
    {"name": "Kab. Tanjung Jabung Timur", "province": "Jambi", "lat": -1.1500, "lon": 103.6000},
    {"name": "Kab. Batanghari", "province": "Jambi", "lat": -1.7500, "lon": 103.2500},
    {"name": "Kab. Sarolangun", "province": "Jambi", "lat": -2.3000, "lon": 102.6500},
    {"name": "Kab. Tebo", "province": "Jambi", "lat": -1.4500, "lon": 102.4000},
    {"name": "Kab. Bungo", "province": "Jambi", "lat": -1.5000, "lon": 101.9500},
    {"name": "Kab. Kerinci", "province": "Jambi", "lat": -2.0833, "lon": 101.4667},

    # --- SUMATERA UTARA, ACEH, SUMBAR, BENGKULU, LAMPUNG, BABEL, KEPRI ---
    {"name": "Kota Banda Aceh", "province": "Aceh", "lat": 5.5483, "lon": 95.3238},
    {"name": "Kab. Aceh Barat (Meulaboh)", "province": "Aceh", "lat": 4.1500, "lon": 96.1333},
    {"name": "Kab. Nagan Raya", "province": "Aceh", "lat": 4.2833, "lon": 96.4833},
    {"name": "Kab. Aceh Singkil", "province": "Aceh", "lat": 2.3000, "lon": 97.8000},
    {"name": "Kab. Aceh Timur", "province": "Aceh", "lat": 4.6333, "lon": 97.6333},
    {"name": "Kota Medan", "province": "Sumatera Utara", "lat": 3.5952, "lon": 98.6722},
    {"name": "Kab. Deli Serdang", "province": "Sumatera Utara", "lat": 3.4167, "lon": 98.6833},
    {"name": "Kab. Asahan", "province": "Sumatera Utara", "lat": 2.9833, "lon": 99.6333},
    {"name": "Kab. Labuhanbatu", "province": "Sumatera Utara", "lat": 2.1833, "lon": 100.0833},
    {"name": "Kab. Mandailing Natal", "province": "Sumatera Utara", "lat": 0.8667, "lon": 99.5667},
    {"name": "Kota Padang", "province": "Sumatera Barat", "lat": -0.9471, "lon": 100.4172},
    {"name": "Kab. Pesisir Selatan", "province": "Sumatera Barat", "lat": -1.3500, "lon": 100.5667},
    {"name": "Kab. Dharmasraya", "province": "Sumatera Barat", "lat": -1.0500, "lon": 101.6167},
    {"name": "Kota Bengkulu", "province": "Bengkulu", "lat": -3.8004, "lon": 102.2655},
    {"name": "Kab. Mukomuko", "province": "Bengkulu", "lat": -2.5833, "lon": 101.1167},
    {"name": "Kota Bandar Lampung", "province": "Lampung", "lat": -5.4500, "lon": 105.2667},
    {"name": "Kab. Lampung Selatan", "province": "Lampung", "lat": -5.6000, "lon": 105.5833},
    {"name": "Kab. Tulang Bawang", "province": "Lampung", "lat": -4.4500, "lon": 105.4167},
    {"name": "Kab. Mesuji", "province": "Lampung", "lat": -4.0500, "lon": 105.3833},
    {"name": "Kab. Way Kanan", "province": "Lampung", "lat": -4.6833, "lon": 104.7500},
    {"name": "Kota Pangkal Pinang", "province": "Bangka Belitung", "lat": -2.1316, "lon": 106.1169},
    {"name": "Kab. Belitung", "province": "Bangka Belitung", "lat": -2.8500, "lon": 107.9167},
    {"name": "Kota Batam", "province": "Kepulauan Riau", "lat": 1.1301, "lon": 104.0529},
    {"name": "Kota Tanjungpinang", "province": "Kepulauan Riau", "lat": 0.9167, "lon": 104.4500},
    {"name": "Kab. Natuna", "province": "Kepulauan Riau", "lat": 3.9000, "lon": 108.2500},

    # --- KALIMANTAN TENGAH (Gambut & Karhutla) ---
    {"name": "Kota Palangka Raya", "province": "Kalimantan Tengah", "lat": -2.2161, "lon": 113.9139},
    {"name": "Kab. Kotawaringin Timur (Sampit)", "province": "Kalimantan Tengah", "lat": -2.5333, "lon": 112.9500},
    {"name": "Kab. Kotawaringin Barat (Pangkalan Bun)", "province": "Kalimantan Tengah", "lat": -2.6833, "lon": 111.6167},
    {"name": "Kab. Pulang Pisau", "province": "Kalimantan Tengah", "lat": -2.7500, "lon": 114.2500},
    {"name": "Kab. Kapuas", "province": "Kalimantan Tengah", "lat": -3.0000, "lon": 114.3833},
    {"name": "Kab. Katingan (Kasongan)", "province": "Kalimantan Tengah", "lat": -1.9000, "lon": 113.3833},
    {"name": "Kab. Seruyan", "province": "Kalimantan Tengah", "lat": -2.5000, "lon": 112.3000},
    {"name": "Kab. Barito Selatan (Buntok)", "province": "Kalimantan Tengah", "lat": -1.7333, "lon": 114.8333},
    {"name": "Kab. Barito Utara (Muara Teweh)", "province": "Kalimantan Tengah", "lat": -0.9500, "lon": 114.9000},
    {"name": "Kab. Sukamara", "province": "Kalimantan Tengah", "lat": -2.6333, "lon": 111.2333},
    {"name": "Kab. Lamandau", "province": "Kalimantan Tengah", "lat": -1.8333, "lon": 111.2833},
    {"name": "Kab. Gunung Mas", "province": "Kalimantan Tengah", "lat": -1.1333, "lon": 113.8667},
    {"name": "Kab. Murung Raya", "province": "Kalimantan Tengah", "lat": -0.0167, "lon": 114.3333},

    # --- KALIMANTAN BARAT (Gambut & Karhutla) ---
    {"name": "Kota Pontianak", "province": "Kalimantan Barat", "lat": -0.0263, "lon": 109.3425},
    {"name": "Kab. Kubu Raya", "province": "Kalimantan Barat", "lat": -0.3000, "lon": 109.4000},
    {"name": "Kab. Ketapang", "province": "Kalimantan Barat", "lat": -1.8333, "lon": 109.9667},
    {"name": "Kab. Kayong Utara (Sukadana)", "province": "Kalimantan Barat", "lat": -1.2500, "lon": 109.9500},
    {"name": "Kab. Mempawah", "province": "Kalimantan Barat", "lat": 0.2500, "lon": 109.1833},
    {"name": "Kab. Sambas", "province": "Kalimantan Barat", "lat": 1.3667, "lon": 109.3000},
    {"name": "Kota Singkawang", "province": "Kalimantan Barat", "lat": 0.9069, "lon": 108.9868},
    {"name": "Kab. Landak (Ngabang)", "province": "Kalimantan Barat", "lat": 0.3833, "lon": 109.9667},
    {"name": "Kab. Sanggau", "province": "Kalimantan Barat", "lat": 0.1200, "lon": 110.5800},
    {"name": "Kab. Sekadau", "province": "Kalimantan Barat", "lat": 0.0333, "lon": 110.9500},
    {"name": "Kab. Sintang", "province": "Kalimantan Barat", "lat": 0.0700, "lon": 111.4900},
    {"name": "Kab. Melawi (Nanga Pinoh)", "province": "Kalimantan Barat", "lat": -0.3333, "lon": 111.7000},
    {"name": "Kab. Kapuas Hulu (Putussibau)", "province": "Kalimantan Barat", "lat": 0.8667, "lon": 112.9333},

    # --- KALIMANTAN SELATAN, TIMUR, UTARA ---
    {"name": "Kota Banjarmasin", "province": "Kalimantan Selatan", "lat": -3.3194, "lon": 114.5908},
    {"name": "Kota Banjarbaru", "province": "Kalimantan Selatan", "lat": -3.4500, "lon": 114.8333},
    {"name": "Kab. Banjar (Martapura)", "province": "Kalimantan Selatan", "lat": -3.4167, "lon": 114.8500},
    {"name": "Kab. Tanah Laut (Pelaihari)", "province": "Kalimantan Selatan", "lat": -3.8000, "lon": 114.7667},
    {"name": "Kab. Tanah Bumbu (Batulicin)", "province": "Kalimantan Selatan", "lat": -3.4500, "lon": 115.9833},
    {"name": "Kab. Kotabaru", "province": "Kalimantan Selatan", "lat": -3.2333, "lon": 116.2167},
    {"name": "Kab. Barito Kuala (Marabahan)", "province": "Kalimantan Selatan", "lat": -2.9833, "lon": 114.7667},
    {"name": "Kab. Tabalong (Tanjung)", "province": "Kalimantan Selatan", "lat": -2.1833, "lon": 115.3833},
    {"name": "Kota Samarinda", "province": "Kalimantan Timur", "lat": -0.5022, "lon": 117.1537},
    {"name": "Kota Balikpapan", "province": "Kalimantan Timur", "lat": -1.2654, "lon": 116.8312},
    {"name": "Kab. Kutai Kartanegara (Tenggarong)", "province": "Kalimantan Timur", "lat": -0.4167, "lon": 116.9833},
    {"name": "Kab. Kutai Timur (Sangatta)", "province": "Kalimantan Timur", "lat": 0.5000, "lon": 117.5500},
    {"name": "Kab. Kutai Barat (Sendawar)", "province": "Kalimantan Timur", "lat": -0.2333, "lon": 115.7000},
    {"name": "Kab. Berau (Tanjung Redeb)", "province": "Kalimantan Timur", "lat": 2.1558, "lon": 117.4917},
    {"name": "Kab. Paser (Tanah Grogot)", "province": "Kalimantan Timur", "lat": -1.9000, "lon": 116.2000},
    {"name": "Kota Bontang", "province": "Kalimantan Timur", "lat": 0.1333, "lon": 117.5000},
    {"name": "Kota Tarakan", "province": "Kalimantan Utara", "lat": 3.3270, "lon": 117.5925},
    {"name": "Kab. Bulungan (Tanjung Selor)", "province": "Kalimantan Utara", "lat": 2.8500, "lon": 117.3667},
    {"name": "Kab. Nunukan", "province": "Kalimantan Utara", "lat": 4.1333, "lon": 117.6667},
    {"name": "Kab. Malinau", "province": "Kalimantan Utara", "lat": 3.5833, "lon": 116.6333},

    # --- JAWA TIMUR, JAWA TENGAH, JAWA BARAT, DIY, BANTEN, BALI ---
    {"name": "Kab. Banyuwangi", "province": "Jawa Timur", "lat": -8.2192, "lon": 114.3692},
    {"name": "Kab. Bondowoso (Gn. Ijen)", "province": "Jawa Timur", "lat": -7.9135, "lon": 113.8214},
    {"name": "Kab. Situbondo", "province": "Jawa Timur", "lat": -7.7000, "lon": 114.0000},
    {"name": "Kab. Lumajang (Bromo-Semeru)", "province": "Jawa Timur", "lat": -8.1333, "lon": 113.2167},
    {"name": "Kab. Probolinggo (Bromo)", "province": "Jawa Timur", "lat": -7.7500, "lon": 113.2167},
    {"name": "Kab. Jember", "province": "Jawa Timur", "lat": -8.1724, "lon": 113.7007},
    {"name": "Kab. Malang", "province": "Jawa Timur", "lat": -7.9797, "lon": 112.6304},
    {"name": "Kab. Pasuruan", "province": "Jawa Timur", "lat": -7.6500, "lon": 112.9000},
    {"name": "Kota Surabaya", "province": "Jawa Timur", "lat": -7.2575, "lon": 112.7521},
    {"name": "Kab. Bojonegoro", "province": "Jawa Timur", "lat": -7.1500, "lon": 111.8833},
    {"name": "Kab. Tuban", "province": "Jawa Timur", "lat": -6.9000, "lon": 112.0500},
    {"name": "Kab. Madiun", "province": "Jawa Timur", "lat": -7.6333, "lon": 111.5333},
    {"name": "Kota Semarang", "province": "Jawa Tengah", "lat": -6.9667, "lon": 110.4167},
    {"name": "Kota Surakarta (Solo)", "province": "Jawa Tengah", "lat": -7.5667, "lon": 110.8167},
    {"name": "Kab. Magelang", "province": "Jawa Tengah", "lat": -7.4833, "lon": 110.2167},
    {"name": "Kab. Cilacap", "province": "Jawa Tengah", "lat": -7.7167, "lon": 109.0167},
    {"name": "Kab. Banyumas (Purwokerto)", "province": "Jawa Tengah", "lat": -7.4333, "lon": 109.2333},
    {"name": "Kab. Brebes", "province": "Jawa Tengah", "lat": -6.8667, "lon": 109.0333},
    {"name": "Kab. Blora", "province": "Jawa Tengah", "lat": -7.0000, "lon": 111.4167},
    {"name": "Kota Yogyakarta", "province": "DIY", "lat": -7.7956, "lon": 110.3695},
    {"name": "Kab. Gunungkidul", "province": "DIY", "lat": -7.9667, "lon": 110.6000},
    {"name": "Kota Bandung", "province": "Jawa Barat", "lat": -6.9175, "lon": 107.6191},
    {"name": "Kab. Bogor", "province": "Jawa Barat", "lat": -6.5833, "lon": 106.8000},
    {"name": "Kab. Sukabumi", "province": "Jawa Barat", "lat": -6.9167, "lon": 106.9167},
    {"name": "Kab. Cianjur", "province": "Jawa Barat", "lat": -6.8167, "lon": 107.1333},
    {"name": "Kab. Garut", "province": "Jawa Barat", "lat": -7.2167, "lon": 107.9000},
    {"name": "Kab. Cirebon", "province": "Jawa Barat", "lat": -6.7500, "lon": 108.5500},
    {"name": "Kab. Indramayu", "province": "Jawa Barat", "lat": -6.3333, "lon": 108.3167},
    {"name": "DKI Jakarta", "province": "DKI Jakarta", "lat": -6.2088, "lon": 106.8456},
    {"name": "Kab. Lebak", "province": "Banten", "lat": -6.5500, "lon": 106.2500},
    {"name": "Kota Serang", "province": "Banten", "lat": -6.1167, "lon": 106.1500},
    {"name": "Kota Denpasar", "province": "Bali", "lat": -8.6705, "lon": 115.2126},
    {"name": "Kab. Buleleng (Singaraja)", "province": "Bali", "lat": -8.1167, "lon": 115.0833},
    {"name": "Kab. Karangasem", "province": "Bali", "lat": -8.4500, "lon": 115.6167},

    # --- NUSA TENGGARA BARAT & TIMUR ---
    {"name": "Kota Mataram", "province": "NTB", "lat": -8.5833, "lon": 116.1167},
    {"name": "Kab. Lombok Timur (Rinjani)", "province": "NTB", "lat": -8.6500, "lon": 116.5333},
    {"name": "Kab. Sumbawa", "province": "NTB", "lat": -8.5000, "lon": 117.4167},
    {"name": "Kab. Sumbawa Barat", "province": "NTB", "lat": -8.7500, "lon": 116.8500},
    {"name": "Kab. Dompu", "province": "NTB", "lat": -8.5333, "lon": 118.4500},
    {"name": "Kota Bima", "province": "NTB", "lat": -8.4608, "lon": 118.7267},
    {"name": "Kota Kupang", "province": "NTT", "lat": -10.1772, "lon": 123.6070},
    {"name": "Kab. Manggarai Barat (Labuan Bajo)", "province": "NTT", "lat": -8.4964, "lon": 119.8877},
    {"name": "Kab. Manggarai (Ruteng)", "province": "NTT", "lat": -8.6167, "lon": 120.4667},
    {"name": "Kab. Ngada (Bajawa)", "province": "NTT", "lat": -8.7833, "lon": 120.9667},
    {"name": "Kab. Ende", "province": "NTT", "lat": -8.8432, "lon": 121.6623},
    {"name": "Kab. Sikka (Maumere)", "province": "NTT", "lat": -8.6200, "lon": 122.2133},
    {"name": "Kab. Flores Timur (Larantuka)", "province": "NTT", "lat": -8.3000, "lon": 122.9500},
    {"name": "Kab. Lembata", "province": "NTT", "lat": -8.4500, "lon": 123.5500},
    {"name": "Kab. Alor (Kalabahi)", "province": "NTT", "lat": -8.2833, "lon": 124.5667},
    {"name": "Kab. Sumba Timur (Waingapu)", "province": "NTT", "lat": -9.6567, "lon": 120.2641},
    {"name": "Kab. Sumba Barat", "province": "NTT", "lat": -9.6333, "lon": 119.3333},
    {"name": "Kab. Rote Ndao", "province": "NTT", "lat": -10.7333, "lon": 123.0833},
    {"name": "Kab. Belu (Atambua)", "province": "NTT", "lat": -9.1000, "lon": 124.8833},

    # --- SULAWESI ---
    {"name": "Kota Makassar", "province": "Sulawesi Selatan", "lat": -5.1477, "lon": 119.4327},
    {"name": "Kab. Gowa", "province": "Sulawesi Selatan", "lat": -5.3333, "lon": 119.5833},
    {"name": "Kab. Maros", "province": "Sulawesi Selatan", "lat": -5.0000, "lon": 119.6000},
    {"name": "Kab. Bone", "province": "Sulawesi Selatan", "lat": -4.5333, "lon": 120.3333},
    {"name": "Kab. Luwu (Belopa)", "province": "Sulawesi Selatan", "lat": -3.3333, "lon": 120.3000},
    {"name": "Kota Palopo", "province": "Sulawesi Selatan", "lat": -3.0000, "lon": 120.2000},
    {"name": "Kab. Tana Toraja", "province": "Sulawesi Selatan", "lat": -3.1000, "lon": 119.8667},
    {"name": "Kab. Bulukumba", "province": "Sulawesi Selatan", "lat": -5.5500, "lon": 120.2000},
    {"name": "Kab. Mamuju", "province": "Sulawesi Barat", "lat": -2.6770, "lon": 118.8890},
    {"name": "Kab. Majene", "province": "Sulawesi Barat", "lat": -3.5500, "lon": 118.9833},
    {"name": "Kota Palu", "province": "Sulawesi Tengah", "lat": -0.9003, "lon": 119.8780},
    {"name": "Kab. Donggala", "province": "Sulawesi Tengah", "lat": -0.6667, "lon": 119.7500},
    {"name": "Kab. Sigi", "province": "Sulawesi Tengah", "lat": -1.3833, "lon": 119.9667},
    {"name": "Kab. Poso", "province": "Sulawesi Tengah", "lat": -1.4000, "lon": 120.7500},
    {"name": "Kab. Morowali", "province": "Sulawesi Tengah", "lat": -2.5000, "lon": 121.9000},
    {"name": "Kab. Banggai (Luwuk)", "province": "Sulawesi Tengah", "lat": -0.9516, "lon": 122.7875},
    {"name": "Kab. Tolitoli", "province": "Sulawesi Tengah", "lat": 1.0500, "lon": 120.8167},
    {"name": "Kota Kendari", "province": "Sulawesi Tenggara", "lat": -3.9972, "lon": 122.5128},
    {"name": "Kab. Kolaka", "province": "Sulawesi Tenggara", "lat": -4.0500, "lon": 121.6000},
    {"name": "Kota Baubau", "province": "Sulawesi Tenggara", "lat": -5.4667, "lon": 122.6000},
    {"name": "Kab. Muna (Raha)", "province": "Sulawesi Tenggara", "lat": -4.8500, "lon": 122.7167},
    {"name": "Kota Gorontalo", "province": "Gorontalo", "lat": 0.5435, "lon": 123.0568},
    {"name": "Kab. Pohuwato", "province": "Gorontalo", "lat": 0.5000, "lon": 121.8000},
    {"name": "Kota Manado", "province": "Sulawesi Utara", "lat": 1.4748, "lon": 124.8428},
    {"name": "Kota Bitung", "province": "Sulawesi Utara", "lat": 1.4500, "lon": 125.1833},
    {"name": "Kota Kotamobagu", "province": "Sulawesi Utara", "lat": 0.7410, "lon": 124.3142},
    {"name": "Kab. Minahasa", "province": "Sulawesi Utara", "lat": 1.2500, "lon": 124.8500},

    # --- MALUKU & MALUKU UTARA ---
    {"name": "Kota Ambon", "province": "Maluku", "lat": -3.6954, "lon": 128.1814},
    {"name": "Kab. Maluku Tengah (Masohi)", "province": "Maluku", "lat": -3.3000, "lon": 128.9500},
    {"name": "Kab. Seram Bagian Barat", "province": "Maluku", "lat": -3.1000, "lon": 128.2500},
    {"name": "Kab. Buru (Namlea)", "province": "Maluku", "lat": -3.2500, "lon": 127.1000},
    {"name": "Kota Tual", "province": "Maluku", "lat": -5.6294, "lon": 132.7486},
    {"name": "Kab. Kepulauan Aru (Dobo)", "province": "Maluku", "lat": -5.7667, "lon": 134.2167},
    {"name": "Kab. Kepulauan Tanimbar (Saumlaki)", "province": "Maluku", "lat": -7.9786, "lon": 131.2981},
    {"name": "Kota Ternate", "province": "Maluku Utara", "lat": 0.7905, "lon": 127.3828},
    {"name": "Kota Tidore", "province": "Maluku Utara", "lat": 0.6974, "lon": 127.4429},
    {"name": "Kab. Halmahera Utara (Tobelo)", "province": "Maluku Utara", "lat": 1.7283, "lon": 128.0094},
    {"name": "Kab. Halmahera Selatan (Labuha)", "province": "Maluku Utara", "lat": -0.6333, "lon": 127.4833},
    {"name": "Kab. Pulau Morotai", "province": "Maluku Utara", "lat": 2.2000, "lon": 128.3333},

    # --- PAPUA (Semua Provinsi di Pulau Papua) ---
    {"name": "Kota Jayapura", "province": "Papua", "lat": -2.5489, "lon": 140.7181},
    {"name": "Kab. Keerom", "province": "Papua", "lat": -3.3000, "lon": 140.7000},
    {"name": "Kab. Sarmi", "province": "Papua", "lat": -2.2500, "lon": 139.1000},
    {"name": "Kab. Biak Numfor", "province": "Papua", "lat": -1.1764, "lon": 136.0820},
    {"name": "Kota Sorong", "province": "Papua Barat Daya", "lat": -0.8761, "lon": 131.2558},
    {"name": "Kab. Raja Ampat", "province": "Papua Barat Daya", "lat": -0.2333, "lon": 130.5000},
    {"name": "Kab. Manokwari", "province": "Papua Barat", "lat": -0.8615, "lon": 134.0620},
    {"name": "Kab. Fakfak", "province": "Papua Barat", "lat": -2.9333, "lon": 132.3000},
    {"name": "Kab. Kaimana", "province": "Papua Barat", "lat": -3.6500, "lon": 133.7667},
    {"name": "Kab. Teluk Bintuni", "province": "Papua Barat", "lat": -2.1333, "lon": 133.5167},
    {"name": "Kab. Nabire", "province": "Papua Tengah", "lat": -3.3667, "lon": 135.4833},
    {"name": "Kab. Mimika (Timika)", "province": "Papua Tengah", "lat": -4.5467, "lon": 136.8837},
    {"name": "Kab. Puncak Jaya", "province": "Papua Tengah", "lat": -3.7500, "lon": 137.9500},
    {"name": "Kab. Jayawijaya (Wamena)", "province": "Papua Pegunungan", "lat": -4.0975, "lon": 138.9442},
    {"name": "Kab. Tolikara", "province": "Papua Pegunungan", "lat": -3.5833, "lon": 138.5000},
    {"name": "Kab. Pegunungan Bintang", "province": "Papua Pegunungan", "lat": -4.7500, "lon": 140.5000},
    {"name": "Kab. Merauke", "province": "Papua Selatan", "lat": -8.4991, "lon": 140.4017},
    {"name": "Kab. Boven Digoel", "province": "Papua Selatan", "lat": -6.1000, "lon": 140.3000},
    {"name": "Kab. Mappi", "province": "Papua Selatan", "lat": -6.5000, "lon": 139.3000},
    {"name": "Kab. Asmat (Agats)", "province": "Papua Selatan", "lat": -5.5000, "lon": 138.1333},
]


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Menghitung jarak geodetik lingkaran besar dalam kilometer."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def resolve_hotspot_location(lat: float, lon: float, default_name: Optional[str] = None) -> str:
    """
    Menentukan nama lokasi spesifik (Kabupaten/Kota dan Provinsi) berdasarkan koordinat (lat, lon).
    Jika koordinat berada di sekitar wilayah Indonesia, menghasilkan nama area yang presisi.
    """
    try:
        lat = float(lat)
        lon = float(lon)
    except (ValueError, TypeError):
        return default_name or "Wilayah Indonesia"

    # Cari titik referensi terdekat
    closest = None
    min_dist = float('inf')

    for center in INDONESIA_CENTERS:
        dist = haversine_km(lat, lon, center["lat"], center["lon"])
        if dist < min_dist:
            min_dist = dist
            closest = center

    if not closest:
        return default_name or "Wilayah Indonesia"

    name = closest["name"]
    province = closest["province"]

    # Format deskripsi wilayah yang sangat alami & presisi
    if min_dist <= 25.0:
        return f"{name}, {province}"
    elif min_dist <= 65.0:
        return f"Sekitar {name}, {province} (±{round(min_dist)} km)"
    elif min_dist <= 150.0:
        return f"Wilayah {province} (Arah {name}, ±{round(min_dist)} km)"
    else:
        # Jika jaraknya cukup jauh dari pusat kota referensi, sebut provinsinya
        return f"Wilayah {province} (Sekitar {name})"
