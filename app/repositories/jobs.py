from sqlalchemy.orm import Session
from sqlalchemy import select, func
from typing import Optional
from .. import models

class JobRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, name: str, trigger: str, params: dict) -> models.Job:
        job = models.Job(name=name, trigger=trigger, params=params)
        self.db.add(job)
        self.db.flush()
        return job

    def get(self, job_id: int) -> Optional[models.Job]:
        return self.db.get(models.Job, job_id)

    def get_by_name(self, name: str) -> Optional[models.Job]:
        return self.db.execute(select(models.Job).where(models.Job.name == name)).scalar_one_or_none()

    def list(self, limit: int = 50, offset: int = 0) -> tuple[list[models.Job], int]:
        items = self.db.execute(
            select(models.Job).order_by(models.Job.created_at.desc()).limit(limit).offset(offset)
        ).scalars().all()
        count = self.db.execute(select(func.count(models.Job.id))).scalar() or 0
        return items, count

    def update_run_times(self, job_id: int, last_run_at=None, next_run_at=None, status: Optional[models.JobStatus]=None):
        job = self.get(job_id)
        if not job:
            return None
        if last_run_at is not None:
            job.last_run_at = last_run_at
        if next_run_at is not None:
            job.next_run_at = next_run_at
        if status is not None:
            job.status = status
        self.db.add(job)
        return job
