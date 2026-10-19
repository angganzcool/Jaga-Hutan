#!/usr/bin/env bash
set -euo pipefail

echo "=============================================="
echo "🌲 JAGA HUTAN - VPS DEPLOYMENT SCRIPT"
echo "=============================================="

APP_DIR="${APP_DIR:-/opt/jaga-hutan}"

if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    echo "📦 Menjalankan deployment via Docker Compose..."
    if [ ! -f .env ]; then
        echo "⚠️ .env tidak ditemukan, membuat dari .env.example..."
        cp .env.example .env
    fi
    docker compose up -d --build
    echo "✅ Jaga Hutan berhasil dideploy via Docker Compose!"
    docker compose ps
else
    echo "🐍 Docker tidak ditemukan, menjalankan via Python venv systemd..."
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    ./venv/bin/pip install --upgrade pip
    ./venv/bin/pip install -r requirements.txt

    if [ ! -f .env ]; then
        cp .env.example .env
    fi

    echo "✅ Dependensi siap. Untuk menjalankan di background VPS gunakan:"
    echo "   nohup ./venv/bin/python app.py > web.log 2>&1 &"
    echo "   nohup ./venv/bin/python main.py --daemon > worker.log 2>&1 &"
fi

echo "=============================================="
