# Gunakan base image Python yang ringan
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install dependensi sistem yang dibutuhkan
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Salin requirements dan install paket Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Salin seluruh kode proyek
COPY . .

# Expose port web dashboard
EXPOSE 8000

# Default command: Jalankan web dashboard
CMD ["python", "app.py"]
