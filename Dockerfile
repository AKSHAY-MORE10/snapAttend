# ─────────────────────────────────────────────
# Dockerfile  —  SnapClass FastAPI backend
# ─────────────────────────────────────────────

FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    libsndfile1 \
    git \
    curl \
    gcc \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install CPU-only torch FIRST
RUN pip install --no-cache-dir \
    torch==2.1.0+cpu \
    torchaudio==2.1.0+cpu \
    --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN pip install --no-cache-dir fastapi==0.115.0 uvicorn[standard]==0.30.6 python-multipart==0.0.9

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]