from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Annotated
from ..database import SessionLocal
from ..repositories.jobs import JobRepository
from ..schemas import JobCreate, JobOut, JobsPage
from ..services.scheduler import scheduler_service

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

router = APIRouter()

@router.get("/jobs", response_model=JobsPage, tags=["Jobs"])
def list_jobs(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    repo = JobRepository(db)
    items, count = repo.list(limit=limit, offset=offset)
    return {"items": items, "count": count, "limit": limit, "offset": offset}

@router.get("/jobs/{job_id}", response_model=JobOut, tags=["Jobs"])
def get_job(job_id: int, db: Session = Depends(get_db)):
    repo = JobRepository(db)
    job = repo.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.post("/jobs", response_model=JobOut, status_code=201, tags=["Jobs"])
def create_job(payload: JobCreate, db: Session = Depends(get_db)):
    # Basic validation: trigger specific fields
    if payload.trigger == "cron" and not payload.cron:
        raise HTTPException(status_code=422, detail="cron spec required for trigger=cron")
    if payload.trigger == "interval" and not payload.interval:
        raise HTTPException(status_code=422, detail="interval spec required for trigger=interval")

    repo = JobRepository(db)
    existing = repo.get_by_name(payload.name)
    if existing:
        raise HTTPException(status_code=409, detail="Job with this name already exists")

    # Choose executor from params; default to 'email' or 'compute'
    executor = payload.params.get("executor", "email" if "to" in payload.params else "compute")

    job = repo.create(name=payload.name, trigger=payload.trigger, params=payload.params)
    db.commit()  # to get job.id

    trig_args = (payload.cron.model_dump(by_alias=True, exclude_none=True) if payload.trigger == "cron"
                 else payload.interval.model_dump(exclude_none=True))
    # Include params to pass to executor
    trig_args = {**trig_args, "params": payload.params}

    # register with APScheduler
    scheduler_service.add_job(job.id, executor, payload.trigger, trig_args)

    db.refresh(job)
    return job
