from __future__ import annotations

import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel

from etl.pipeline import ETLPipeline, PipelineConfig
from jobs.scheduler import JobScheduler
from jobs.store import JobRecord, JobStatus, JobStore
from storage.files import FileStorage, StorageConfig


API_TOKEN = os.getenv("API_TOKEN", "secret-token")
FILE_SIZE_LIMIT_MB = float(os.getenv("FILE_SIZE_LIMIT_MB", 5))
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
REPORT_DIR = DATA_DIR / "reports"


class JobRequest(BaseModel):
    input_path: str
    description: Optional[str] = None


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    created_at: str
    updated_at: str
    metrics: Optional[dict] = None
    output_pdf: Optional[str] = None
    preview_html: Optional[str] = None
    error: Optional[str] = None


app = FastAPI(title="ETL Portfolio API", version="0.1.0")


storage = FileStorage(StorageConfig(base_path=DATA_DIR, uploads_path=UPLOAD_DIR, reports_path=REPORT_DIR))
store = JobStore(DATA_DIR / "jobs.db")
pipeline = ETLPipeline(PipelineConfig(template_dir=BASE_DIR / "templates"))
scheduler = JobScheduler(store=store, pipeline=pipeline, storage=storage)


@app.on_event("startup")
def startup():
    storage.ensure_folders()
    store.initialize()
    scheduler.start()


@app.on_event("shutdown")
def shutdown():
    scheduler.stop()


def authenticate(token: str = None):
    if token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid API token")


@app.post("/upload")
async def upload_file(file: UploadFile = File(...), token: str = Depends(authenticate)):
    contents = await file.read()
    limit_bytes = FILE_SIZE_LIMIT_MB * 1024 * 1024
    if len(contents) > limit_bytes:
        raise HTTPException(status_code=413, detail=f"File exceeds {FILE_SIZE_LIMIT_MB} MB limit")

    filename = f"{uuid.uuid4()}_{file.filename}"
    path = storage.save_upload(filename, contents)
    return {"path": str(path)}


@app.post("/jobs/start")
def start_job(request: JobRequest, token: str = Depends(authenticate)):
    if not storage.exists(request.input_path):
        raise HTTPException(status_code=404, detail="File not found")
    job_id = scheduler.enqueue(request.input_path, description=request.description)
    return {"job_id": job_id}


@app.get("/jobs/{job_id}", response_model=JobStatusResponse)
def get_job(job_id: str, token: str = Depends(authenticate)):
    record = store.get(job_id)
    if not record:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(
        job_id=record.id,
        status=record.status.value,
        created_at=record.created_at.isoformat(),
        updated_at=record.updated_at.isoformat(),
        metrics=record.metrics,
        output_pdf=str(record.output_pdf) if record.output_pdf else None,
        preview_html=str(record.preview_html) if record.preview_html else None,
        error=record.error,
    )


@app.get("/jobs")
def list_jobs(token: str = Depends(authenticate)):
    rows: List[JobRecord] = store.list_recent(limit=50)
    return [
        {
            "job_id": row.id,
            "status": row.status.value,
            "created_at": row.created_at.isoformat(),
            "updated_at": row.updated_at.isoformat(),
            "description": row.description,
            "output_pdf": str(row.output_pdf) if row.output_pdf else None,
        }
        for row in rows
    ]


@app.get("/jobs/{job_id}/download")
def download_report(job_id: str, token: str = Depends(authenticate)):
    record = store.get(job_id)
    if not record or not record.output_pdf:
        raise HTTPException(status_code=404, detail="Report not ready")
    return FileResponse(path=record.output_pdf, media_type="application/pdf", filename=os.path.basename(record.output_pdf))


@app.get("/jobs/{job_id}/preview")
def preview_report(job_id: str, token: str = Depends(authenticate)):
    record = store.get(job_id)
    if not record or not record.preview_html:
        raise HTTPException(status_code=404, detail="Preview not ready")
    html_content = Path(record.preview_html).read_text()
    return HTMLResponse(content=html_content)


@app.get("/health")
def health():
    return JSONResponse({"status": "ok", "time": datetime.utcnow().isoformat()})

