# Changelog

Semua perubahan penting pada Jaga Hutan dicatat di berkas ini.

## [1.0.0] - 2026-08-25

Rilis publik pertama yang siap digunakan sebagai fondasi sistem peringatan dini
hotspot berbiaya rendah.

### Ditambahkan

- Integrasi data hotspot NASA FIRMS VIIRS dan MODIS.
- Pemantauan banyak wilayah dengan filter radius Haversine dan confidence.
- Notifikasi Telegram dan webhook WhatsApp dengan cooldown anti-spam.
- Dashboard FastAPI dan Leaflet dengan ekspor GeoJSON/CSV.
- Mode simulasi eksplisit dengan banner peringatan.
- Healthcheck, Docker Compose, persistent SQLite volume, dan GitHub Actions CI.
- Perlindungan token pada pemicu monitoring manual.
- Dukungan satu hotspot pada beberapa wilayah pantau.

### Keamanan dan keandalan

- SQLite WAL, busy timeout, foreign keys, dan lock monitoring lintas proses.
- Escape konten dinamis dashboard untuk mengurangi risiko XSS.
- Validasi koordinat dan radius lokasi.
- Dashboard Docker hanya bind ke localhost untuk digunakan di balik reverse proxy.

### Batasan

- Hotspot satelit bukan konfirmasi kebakaran; hasil wajib diverifikasi di lapangan.
- WhatsApp memerlukan gateway eksternal yang dikelola pengguna.
- Sistem belum menyediakan prediksi cuaca atau klasifikasi kamera berbasis AI.

[1.0.0]: https://github.com/angganzcool/Jaga-Hutan/releases/tag/v1.0.0
