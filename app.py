import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from fastapi import FastAPI, Request, Query, Header, HTTPException, Response
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional, List
import asyncio
import threading
import logging
import time

from config import get_config
from database import Database
from firms_service import FirmsService
from notifier import Notifier
from main import run_monitoring_cycle

app = FastAPI(title="Jaga Hutan API", version="1.0.0")

if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    if os.path.exists("static/favicon.svg"):
        return FileResponse("static/favicon.svg", media_type="image/svg+xml")
    return Response(status_code=204)

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
monitoring_lock = threading.Lock()
logger = logging.getLogger("jaga_hutan.api")

class SimpleTTLCache:
    """Cache in-memory sederhana dengan Time-To-Live untuk mencegah query database berulang."""
    def __init__(self, ttl_seconds: int = 30):
        self.ttl = ttl_seconds
        self._cache = {}
        self._lock = threading.Lock()

    def get(self, key: str):
        with self._lock:
            if key in self._cache:
                val, expiry = self._cache[key]
                if time.time() < expiry:
                    return val
                del self._cache[key]
            return None

    def set(self, key: str, value):
        with self._lock:
            self._cache[key] = (value, time.time() + self.ttl)

    def clear(self):
        with self._lock:
            self._cache.clear()

api_cache = SimpleTTLCache(ttl_seconds=30)

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={},
    )

@app.get("/api/locations")
async def get_locations():
    await asyncio.to_thread(cfg.load_locations)
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
async def get_hotspots(
    days: int = Query(7, ge=1, le=30),
    location_id: Optional[str] = None,
    min_frp: Optional[float] = Query(None, ge=0.0)
):
    cache_key = f"hotspots_{days}_{location_id}_{min_frp}"
    cached = api_cache.get(cache_key)
    if cached is not None:
        return cached

    results = await asyncio.to_thread(db.get_recent_hotspots, days, location_id, min_frp)
    api_cache.set(cache_key, results)
    return results

from air_quality import fetch_indonesia_air_quality

@app.get("/api/air-quality")
async def get_air_quality():
    cache_key = "air_quality_indonesia"
    cached = api_cache.get(cache_key)
    if cached is not None:
        return cached

    data = await asyncio.to_thread(fetch_indonesia_air_quality)
    api_cache.set(cache_key, data)
    return data

@app.get("/api/stats")
async def get_stats():
    cache_key = "stats_summary"
    cached = api_cache.get(cache_key)
    if cached is not None:
        return cached

    stats = await asyncio.to_thread(db.get_stats)
    api_cache.set(cache_key, stats)
    return stats

@app.get("/health/live")
async def health_live():
    return {"status": "ok"}

@app.get("/health/ready")
async def health_ready():
    try:
        await asyncio.to_thread(db.get_stats)
    except Exception:
        raise HTTPException(status_code=503, detail="Database tidak siap")
    return {
        "status": "ready",
        "firms_configured": firms.is_configured(),
        "simulation_mode": cfg.simulation_enabled,
    }

@app.get("/api/export/geojson")
async def export_geojson(
    days: int = Query(7, ge=1, le=30),
    location_id: Optional[str] = None,
    min_frp: Optional[float] = Query(None, ge=0.0)
):
    """
    Ekspor data hotspot ke format standar GeoJSON (FeatureCollection) untuk QGIS / ArcGIS / Leaflet.
    """
    hotspots = await asyncio.to_thread(db.get_recent_hotspots, days, location_id, min_frp)
    features = []
    for spot in hotspots:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [spot["longitude"], spot["latitude"]]
            },
            "properties": {
                "hotspot_uid": spot["hotspot_uid"],
                "brightness": spot["brightness"],
                "scan_date": spot["scan_date"],
                "scan_time": spot["scan_time"],
                "satellite": spot["satellite"],
                "instrument": spot["instrument"],
                "confidence": spot["confidence_label"],
                "frp_mw": spot["frp"],
                "location_name": spot["location_name"],
                "distance_km": spot["distance_km"]
            }
        })
    return {
        "type": "FeatureCollection",
        "features": features
    }

@app.get("/api/export/csv")
async def export_csv(
    days: int = Query(7, ge=1, le=30),
    location_id: Optional[str] = None,
    min_frp: Optional[float] = Query(None, ge=0.0)
):
    """
    Ekspor data hotspot ke format CSV.
    """
    import io
    import csv
    from fastapi.responses import Response

    hotspots = await asyncio.to_thread(db.get_recent_hotspots, days, location_id, min_frp)
    output = io.StringIO()
    if hotspots:
        writer = csv.DictWriter(output, fieldnames=list(hotspots[0].keys()))
        writer.writeheader()
        writer.writerows(hotspots)
    
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=jaga_hutan_hotspots_{days}d.csv"}
    )

@app.post("/api/trigger-check")
async def trigger_check(
    simulate: bool = False,
    x_admin_token: Optional[str] = Header(default=None),
):
    if not cfg.manual_trigger_token:
        raise HTTPException(status_code=503, detail="Pemicu manual dinonaktifkan")
    if x_admin_token != cfg.manual_trigger_token:
        raise HTTPException(status_code=401, detail="Token admin tidak valid")
    if simulate and not cfg.simulation_enabled:
        raise HTTPException(status_code=403, detail="Mode simulasi tidak diizinkan")
    if not monitoring_lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="Siklus monitoring sedang berjalan")
    try:
        await asyncio.to_thread(run_monitoring_cycle, cfg, db, firms, notifier, simulate)
        api_cache.clear()
        return {"status": "success", "message": "Pengecekan hotspot berhasil dijalankan."}
    except Exception:
        logger.exception("Pengecekan hotspot manual gagal")
        return JSONResponse(status_code=500, content={"status": "error", "message": "Pengecekan gagal. Periksa log server."})
    finally:
        monitoring_lock.release()

if __name__ == "__main__":
    import uvicorn
    print(f"🌲 Menjalankan Web Dashboard Jaga Hutan di http://localhost:{cfg.web_port}")
    uvicorn.run(app, host=cfg.web_host, port=cfg.web_port)
