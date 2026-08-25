import sqlite3
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional

class Database:
    def __init__(self, db_path: str = "jaga_hutan.db"):
        self.db_path = db_path
        self._mem_conn = None
        if self.db_path == ":memory:":
            self._mem_conn = sqlite3.connect(":memory:")
            self._mem_conn.row_factory = sqlite3.Row
        self.init_db()

    def get_connection(self):
        if self._mem_conn:
            return self._mem_conn
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout = 30000")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Tabel Hotspots
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS hotspots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hotspot_uid TEXT UNIQUE,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                brightness REAL,
                scan_date TEXT NOT NULL,
                scan_time TEXT NOT NULL,
                satellite TEXT,
                instrument TEXT,
                confidence_code TEXT,
                confidence_label TEXT,
                frp REAL,
                daynight TEXT,
                location_id TEXT,
                location_name TEXT,
                distance_km REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # Tabel Log Pengiriman Notifikasi (Anti-Spam Deduplikasi)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS alert_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hotspot_uid TEXT NOT NULL,
                location_id TEXT NOT NULL,
                channel TEXT NOT NULL,
                recipient TEXT,
                status TEXT NOT NULL,
                response_info TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS hotspot_locations (
                hotspot_uid TEXT NOT NULL,
                location_id TEXT NOT NULL,
                location_name TEXT,
                distance_km REAL,
                PRIMARY KEY (hotspot_uid, location_id),
                FOREIGN KEY (hotspot_uid) REFERENCES hotspots(hotspot_uid) ON DELETE CASCADE
            );
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS monitoring_lock (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                locked_until TEXT NOT NULL
            );
            """)
            cursor.execute("""
            INSERT OR IGNORE INTO hotspot_locations (hotspot_uid, location_id, location_name, distance_km)
            SELECT hotspot_uid, location_id, location_name, distance_km
            FROM hotspots WHERE location_id IS NOT NULL AND location_id != ''
            """)

            # Indeks untuk query performa
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_hotspots_uid ON hotspots(hotspot_uid);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_hotspots_loc ON hotspots(location_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_hotspots_date ON hotspots(scan_date);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_hotspot_locations_loc ON hotspot_locations(location_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_alert_logs_dedup ON alert_logs(hotspot_uid, location_id, channel, sent_at);")
            
            conn.commit()

    def acquire_monitoring_lock(self, lease_minutes: int = 10) -> bool:
        now = datetime.now(timezone.utc)
        locked_until = (now + timedelta(minutes=lease_minutes)).strftime("%Y-%m-%d %H:%M:%S")
        now_text = now.strftime("%Y-%m-%d %H:%M:%S")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("BEGIN IMMEDIATE")
            cursor.execute(
                "INSERT OR IGNORE INTO monitoring_lock (id, locked_until) VALUES (1, ?)",
                (locked_until,),
            )
            if cursor.rowcount > 0:
                conn.commit()
                return True
            cursor.execute(
                "UPDATE monitoring_lock SET locked_until = ? WHERE id = 1 AND locked_until <= ?",
                (locked_until, now_text),
            )
            acquired = cursor.rowcount > 0
            conn.commit()
            return acquired

    def release_monitoring_lock(self):
        with self.get_connection() as conn:
            conn.execute("DELETE FROM monitoring_lock WHERE id = 1")
            conn.commit()

    def save_hotspot(self, data: Dict[str, Any]) -> bool:
        """
        Menyimpan data hotspot jika belum ada.
        Mengembalikan True jika data baru ditambahkan, False jika sudah ada.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                INSERT OR IGNORE INTO hotspots (
                    hotspot_uid, latitude, longitude, brightness,
                    scan_date, scan_time, satellite, instrument,
                    confidence_code, confidence_label, frp, daynight,
                    location_id, location_name, distance_km
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data["hotspot_uid"],
                    data["latitude"],
                    data["longitude"],
                    data.get("brightness", 0.0),
                    data["scan_date"],
                    data["scan_time"],
                    data.get("satellite", ""),
                    data.get("instrument", ""),
                    data.get("confidence_code", "nominal"),
                    data.get("confidence_label", "Sedang"),
                    data.get("frp", 0.0),
                    data.get("daynight", "D"),
                    data.get("location_id", ""),
                    data.get("location_name", ""),
                    data.get("distance_km", 0.0),
                ))
                cursor.execute("""
                INSERT OR IGNORE INTO hotspot_locations (
                    hotspot_uid, location_id, location_name, distance_km
                ) VALUES (?, ?, ?, ?)
                """, (
                    data["hotspot_uid"], data.get("location_id", ""),
                    data.get("location_name", ""), data.get("distance_km", 0.0)
                ))
                association_is_new = cursor.rowcount > 0
                conn.commit()
                return association_is_new
            except Exception as e:
                print(f"[DB ERROR] Gagal menyimpan hotspot: {e}")
                return False

    def was_alerted_recently(self, hotspot_uid: str, location_id: str, channel: str, cooldown_hours: int = 12) -> bool:
        """
        Mengecek apakah alert untuk hotspot & lokasi & channel tertentu sudah pernah dikirim
        dalam rentang waktu cooldown_hours terakhir.
        """
        cutoff_time = (datetime.now(timezone.utc) - timedelta(hours=cooldown_hours)).strftime("%Y-%m-%d %H:%M:%S")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT id FROM alert_logs
            WHERE hotspot_uid = ? AND location_id = ? AND channel = ? AND status = 'sent' AND sent_at >= ?
            LIMIT 1
            """, (hotspot_uid, location_id, channel, cutoff_time))
            row = cursor.fetchone()
            return row is not None

    def log_alert(self, hotspot_uid: str, location_id: str, channel: str, recipient: str, status: str, response_info: str = ""):
        """
        Mencatat pengiriman notifikasi ke dalam tabel alert_logs.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO alert_logs (hotspot_uid, location_id, channel, recipient, status, response_info)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (hotspot_uid, location_id, channel, recipient, status, response_info))
            conn.commit()

    def get_recent_hotspots(self, days: int = 7, location_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Mengambil daftar hotspot terkini untuk visualisasi di dashboard.
        """
        cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT h.id, h.hotspot_uid, h.latitude, h.longitude, h.brightness,
                       h.scan_date, h.scan_time, h.satellite, h.instrument,
                       h.confidence_code, h.confidence_label, h.frp, h.daynight,
                       hl.location_id, hl.location_name, hl.distance_km, h.created_at
                FROM hotspots h
                JOIN hotspot_locations hl ON hl.hotspot_uid = h.hotspot_uid
                WHERE h.scan_date >= ?
            """
            params = [cutoff_date]
            if location_id:
                query += " AND hl.location_id = ?"
                params.append(location_id)
            query += " ORDER BY h.scan_date DESC, h.scan_time DESC"
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_stats(self) -> Dict[str, Any]:
        """
        Statistik ringkas sistem Jaga Hutan.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM hotspots")
            total_hotspots = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM alert_logs WHERE status = 'sent'")
            total_alerts_sent = cursor.fetchone()[0]

            today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            cursor.execute("SELECT COUNT(*) FROM hotspots WHERE scan_date = ?", (today_str,))
            today_hotspots = cursor.fetchone()[0]

            return {
                "total_hotspots": total_hotspots,
                "today_hotspots": today_hotspots,
                "total_alerts_sent": total_alerts_sent
            }
