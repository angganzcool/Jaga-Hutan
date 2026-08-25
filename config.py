import os
import json
from dataclasses import dataclass, field
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

@dataclass
class MonitoredLocation:
    id: str
    name: str
    latitude: float
    longitude: float
    radius_km: float = 20.0
    min_confidence: str = "nominal"  # "low", "nominal", "high", or percentage for MODIS (e.g. 50)
    alert_telegram: bool = True
    alert_whatsapp: bool = True

@dataclass
class AppConfig:
    environment: str = os.getenv("APP_ENV", "development").lower()
    simulation_enabled: bool = os.getenv("SIMULATION_MODE", "false").lower() in ("true", "1", "yes")
    manual_trigger_token: str = os.getenv("MANUAL_TRIGGER_TOKEN", "")
    # NASA FIRMS
    firms_map_key: str = os.getenv("FIRMS_MAP_KEY", "")
    firms_source: str = os.getenv("FIRMS_SOURCE", "VIIRS_SNPP_NRT")
    firms_country: str = os.getenv("FIRMS_COUNTRY", "IDN")
    firms_day_range: int = int(os.getenv("FIRMS_DAY_RANGE", "1"))
    
    # Telegram
    telegram_enabled: bool = os.getenv("TELEGRAM_ENABLED", "false").lower() in ("true", "1", "yes")
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")
    
    # WhatsApp
    whatsapp_enabled: bool = os.getenv("WHATSAPP_ENABLED", "false").lower() in ("true", "1", "yes")
    whatsapp_webhook_url: str = os.getenv("WHATSAPP_WEBHOOK_URL", "http://localhost:3000/api/send-message")
    whatsapp_target_number: str = os.getenv("WHATSAPP_TARGET_NUMBER", "")
    whatsapp_auth_token: str = os.getenv("WHATSAPP_AUTH_TOKEN", "")
    
    # Storage & Monitoring
    db_path: str = os.getenv("DB_PATH", "jaga_hutan.db")
    locations_file: str = os.getenv("LOCATIONS_FILE", "locations.json")
    alert_cooldown_hours: int = int(os.getenv("ALERT_COOLDOWN_HOURS", "12"))
    check_interval_minutes: int = int(os.getenv("CHECK_INTERVAL_MINUTES", "60"))
    
    # Web
    web_host: str = os.getenv("WEB_HOST", "0.0.0.0")
    web_port: int = int(os.getenv("WEB_PORT", "8000"))
    
    locations: List[MonitoredLocation] = field(default_factory=list)

    def load_locations(self) -> List[MonitoredLocation]:
        if not os.path.exists(self.locations_file):
            return []
        try:
            with open(self.locations_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.locations = [
                    MonitoredLocation(
                        id=item.get("id", f"loc_{idx}"),
                        name=item.get("name", f"Lokasi #{idx+1}"),
                        latitude=float(item["latitude"]),
                        longitude=float(item["longitude"]),
                        radius_km=float(item.get("radius_km", 20.0)),
                        min_confidence=item.get("min_confidence", "nominal"),
                        alert_telegram=item.get("alert_telegram", True),
                        alert_whatsapp=item.get("alert_whatsapp", True),
                    )
                    for idx, item in enumerate(data)
                ]
                for location in self.locations:
                    if not -90 <= location.latitude <= 90:
                        raise ValueError(f"Latitude {location.name} harus antara -90 dan 90")
                    if not -180 <= location.longitude <= 180:
                        raise ValueError(f"Longitude {location.name} harus antara -180 dan 180")
                    if location.radius_km <= 0:
                        raise ValueError(f"Radius {location.name} harus lebih besar dari 0")
        except Exception as e:
            print(f"[WARN] Gagal membaca {self.locations_file}: {e}")
            self.locations = []
        return self.locations

def get_config() -> AppConfig:
    cfg = AppConfig()
    cfg.load_locations()
    return cfg
