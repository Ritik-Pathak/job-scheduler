from typing import Any, Dict
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_SUBMITTED
from datetime import datetime, timezone
import logging

from ..config import settings
from ..database import engine, SessionLocal
from ..repositories.jobs import JobRepository
from ..models import JobStatus
from .executors import EXECUTOR_REGISTRY

logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self):
        jobstores = {"default": SQLAlchemyJobStore(engine=engine)}
        self.scheduler = BackgroundScheduler(jobstores=jobstores, timezone=settings.tz)

        # wire listeners
        self.scheduler.add_listener(self._on_job_executed, EVENT_JOB_EXECUTED)
        self.scheduler.add_listener(self._on_job_error, EVENT_JOB_ERROR)
        self.scheduler.add_listener(self._on_job_submitted, EVENT_JOB_SUBMITTED)

    def start(self):
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("APScheduler started")

    def shutdown(self):
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

    def _on_job_submitted(self, event):
        # update status to running just before execution (best-effort)
        job_id = int(event.job_id.split(":")[0])
        with SessionLocal() as db:
            repo = JobRepository(db)
            repo.update_run_times(job_id, status=JobStatus.running)
            db.commit()

    def _on_job_executed(self, event):
        job_id = int(event.job_id.split(":")[0])
        with SessionLocal() as db:
            repo = JobRepository(db)
            next_run = self.scheduler.get_job(event.job_id).next_run_time if self.scheduler.get_job(event.job_id) else None
            repo.update_run_times(job_id, last_run_at=datetime.now(timezone.utc), next_run_at=next_run, status=JobStatus.scheduled)
            db.commit()
        logger.info("Job %s executed successfully", job_id)

    def _on_job_error(self, event):
        job_id = int(event.job_id.split(":")[0])
        with SessionLocal() as db:
            repo = JobRepository(db)
            repo.update_run_times(job_id, last_run_at=datetime.now(timezone.utc), status=JobStatus.failed)
            db.commit()
        logger.exception("Job %s failed", job_id)

    def add_job(self, job_id: int, executor_key: str, trigger: str, trigger_args: Dict[str, Any]) -> str:
        func = EXECUTOR_REGISTRY.get(executor_key)
        if not func:
            raise ValueError(f"Unknown executor '{executor_key}'. Available: {list(EXECUTOR_REGISTRY)}")

        if trigger == "cron":
            trig = CronTrigger(**trigger_args)
        elif trigger == "interval":
            trig = IntervalTrigger(**trigger_args)
        else:
            raise ValueError("Unsupported trigger. Use 'cron' or 'interval'.")

        aps_id = f"{job_id}:{executor_key}"
        self.scheduler.add_job(func=func, trigger=trig, id=aps_id, kwargs={"job_id": job_id, **trigger_args.get("params", {})})
        next_run = self.scheduler.get_job(aps_id).next_run_time
        # Persist next_run_at on our side
        with SessionLocal() as db:
            repo = JobRepository(db)
            repo.update_run_times(job_id, next_run_at=next_run, status=JobStatus.scheduled)
            db.commit()
        return aps_id

scheduler_service = SchedulerService()
