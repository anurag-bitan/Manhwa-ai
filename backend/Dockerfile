# ============================
# 1. Base Image
# ============================
FROM python:3.11-slim

# ============================
# 2. Install system dependencies
# ============================
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    tesseract-ocr \
    poppler-utils \
    libsm6 \
    libxext6 \
    libgl1 \
    build-essential \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# ============================
# 3. Set work directory
# ============================
WORKDIR /app

# ============================
# 4. Copy requirements first (better caching)
# ============================
COPY requirements.txt .

# ============================
# 5. Install Python dependencies
# ============================
RUN pip install --no-cache-dir -r requirements.txt

# ============================
# 6. Copy application code
# ============================
COPY app ./app
# COPY service_account.json .
# COPY job_status ./job_status
# ============================
# 7. Expose default port (Cloud Run uses $PORT)
# ============================
ENV PORT=8080
EXPOSE 8080

# ============================
# 8. Start FastAPI with Uvicorn
# Cloud Run will inject PORT (usually 8080)
# ============================
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port $PORT"]
