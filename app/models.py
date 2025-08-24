from sqlalchemy import Column, Integer, String, DateTime, JSON, Enum, func
from sqlalchemy.orm import Mapped, mapped_column
import enum
from .database import Base

class JobStatus(str, enum.Enum):
    scheduled = "scheduled"
    running = "running"
    paused = "paused"
    completed = "completed"
    failed = "failed"

class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    trigger: Mapped[str] = mapped_column(String(20), nullable=False)  # "cron" | "interval" | "date"
    params: Mapped[dict] = mapped_column(JSON, default=dict)

    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), default=JobStatus.scheduled)

    last_run_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_run_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
