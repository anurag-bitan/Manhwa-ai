# backend/app/routers/status.py

import os
import time
import json
from fastapi import APIRouter, HTTPException

router = APIRouter()

# ----------------------------------------------------------
# HEALTH & BASIC ENDPOINTS
# ----------------------------------------------------------

@router.get("/status/ping")
def ping():
    return {"ping": "pong", "time": time.time()}

@router.get("/status/health")
def health():
    return {
        "status": "healthy",
        "service": "manhwa-ai-backend",
        "timestamp": time.time()
    }

# ----------------------------------------------------------
# JOB STATUS SYSTEM
# ----------------------------------------------------------

# Correct base directory for backend/job_status
BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../")
)

STATUS_DIR = os.path.join(BASE_DIR, "job_status")
os.makedirs(STATUS_DIR, exist_ok=True)


def status_path(job_id: str):
    """Full path to job status JSON file."""
    return os.path.join(STATUS_DIR, f"{job_id}.json")


def read_status(job_id: str):
    """Read status JSON safely."""
    path = status_path(job_id)

    if not os.path.exists(path):
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def list_all_jobs():
    jobs = []
    for filename in os.listdir(STATUS_DIR):
        if filename.endswith(".json"):
            try:
                with open(os.path.join(STATUS_DIR, filename), "r", encoding="utf-8") as f:
                    jobs.append(json.load(f))
            except:
                continue

    # Sort newest first
    jobs = sorted(jobs, key=lambda x: x.get("_updated_at", 0), reverse=True)
    return jobs


# ----------------------------------------------------------
# API ROUTES
# ----------------------------------------------------------

@router.get("/status/job/{job_id}")
def get_job_status(job_id: str):
    """
    Retrieve job info for a given job_id.
    Used by frontend polling for /generate_video.
    """
    data = read_status(job_id)

    if data is None:
        raise HTTPException(
            status_code=404,
            detail=f"No job found with id {job_id}"
        )

    return {
        "job_id": job_id,
        "status": data.get("status", "unknown"),
        "message": data.get("message", ""),
        "preview_url": data.get("preview_url"),
        "video_url": data.get("video_url")
    }


@router.get("/status/jobs")
def get_all_jobs():
    """
    List all jobs (for debugging and admin UI).
    """
    jobs = list_all_jobs()
    return {
        "count": len(jobs),
        "jobs": jobs
    }
