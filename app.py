import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional, List

from config import get_config
from database import Database
from firms_service import FirmsService
from notifier import Notifier
from main import run_monitoring_cycle

app = FastAPI(title="Jaga Hutan API", version="1.0.0")

templates = Jinja2Templates(directory="templates")

cfg = get_config()
db = Database(cfg.db_path)
firms = FirmsService(
    map_key=cfg.firms_map_key,
    source=cfg.firms_source,
    country=cfg.firms_country,
    day_range=cfg.firms_day_range
)
notifier = Notifier(cfg)

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/locations")
async def get_locations():
    cfg.load_locations()
    return [
        {
            "id": loc.id,
            "name": loc.name,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "radius_km": loc.radius_km,
            "min_confidence": loc.min_confidence,
            "alert_telegram": loc.alert_telegram,
            "alert_whatsapp": loc.alert_whatsapp,
        }
        for loc in cfg.locations
    ]

@app.get("/api/hotspots")
async def get_hotspots(days: int = Query(7, ge=1, le=30), location_id: Optional[str] = None):
    results = db.get_recent_hotspots(days=days, location_id=location_id)
    return results

@app.get("/api/stats")
async def get_stats():
    return db.get_stats()

@app.post("/api/trigger-check")
async def trigger_check(simulate: bool = False):
    try:
        run_monitoring_cycle(cfg, db, firms, notifier, force_simulation=simulate)
        return {"status": "success", "message": "Pengecekan hotspot berhasil dijalankan."}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

if __name__ == "__main__":
    import uvicorn
    print(f"🌲 Menjalankan Web Dashboard Jaga Hutan di http://localhost:{cfg.web_port}")
    uvicorn.run(app, host=cfg.web_host, port=cfg.web_port)
