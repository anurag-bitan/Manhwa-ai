# backend/app/main.py
"""
AI Manhwa Backend - Clean Restart Version
Optimized · Stable · No Firebase · Supabase Ready
"""

import os
import time
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
# backend/app/main.py  (paste into top with other imports)

# Load .env
load_dotenv()


# -----------------------------------------------------
# FASTAPI APP INITIALIZATION
# -----------------------------------------------------
app = FastAPI(
    title="Manhwa AI Backend",
    description="Transform manga PDFs into narrated cinematic videos",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# -----------------------------------------------------
# CORS (Allow local frontend)
# -----------------------------------------------------
app.add_middleware(
    CORSMiddleware,
   allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",

        # Your real Vercel domains:
        "https://manhwa-a1wv8f96g-anurag-bitans-projects.vercel.app",
        "https://manhwa-ai-git-main-anurag-bitans-projects.vercel.app",
        "https://manhwa-ai-theta.vercel.app",
        "*.vercel.app",
        # Cloud Run domain
        "https://manhwa-backend-h7g66jyc2q-el.a.run.app",
        "https:/manhwa-backend-h7g66jyc2q-el.a.run.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------------------------------
# GLOBAL EXCEPTION HANDLER
# -----------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print("\n===== GLOBAL ERROR =====")
    print(f"Path: {request.url.path}")
    print(f"Error: {exc}")
    print("========================\n")

    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_error",
            "message": str(exc),
            "path": request.url.path,
        },
    )


# -----------------------------------------------------
# REQUEST TIME LOGGER
# -----------------------------------------------------
@app.middleware("http")
async def add_timing(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    response.headers["X-Process-Time"] = f"{time.time() - start:.3f}s"
    return response


# -----------------------------------------------------
# IMPORT ROUTERS
# (now that app is initialized)
# -----------------------------------------------------
from app.routers import status
from app.routers import generate_audio_story
from app.routers import generate_video

API_PREFIX = "/api/v1"

app.include_router(status.router, prefix=API_PREFIX, tags=["System Status"])
app.include_router(generate_audio_story.router, prefix=API_PREFIX, tags=["Audio & Script"])
app.include_router(generate_video.router, prefix=API_PREFIX, tags=["Video Generation"])


# -----------------------------------------------------
# ROOT ROUTES
# -----------------------------------------------------
@app.get("/")
async def root():
    return {
        "status": "running",
        "message": "Manhwa AI Backend is live!",
        "health": "/health",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "time": time.time(),
    }


# -----------------------------------------------------
# STARTUP & SHUTDOWN
# -----------------------------------------------------
@app.on_event("startup")
async def startup():
    print("\n==============================")
    print("  Manhwa AI Backend Started")
    print("==============================")
    print("Docs: http://localhost:8000/docs")

    # create safe dirs
    os.makedirs("temp", exist_ok=True)
    os.makedirs("job_status", exist_ok=True)


@app.on_event("shutdown")
async def shutdown():
    print("\n==============================")
    print("  Backend shutdown complete.")
    print("==============================\n")
