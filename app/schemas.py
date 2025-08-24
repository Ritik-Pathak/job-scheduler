from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

class CronSpec(BaseModel):
    year: Optional[str | int] = None
    month: Optional[str | int] = None
    day: Optional[str | int] = Field(None, alias="day_of_month")
    week: Optional[str | int] = None
    day_of_week: Optional[str | int] = None
    hour: Optional[str | int] = None
    minute: Optional[str | int] = None
    second: Optional[str | int] = None

class IntervalSpec(BaseModel):
    weeks: Optional[int] = None
    days: Optional[int] = None
    hours: Optional[int] = None
    minutes: Optional[int] = None
    seconds: Optional[int] = None

class JobCreate(BaseModel):
    name: str = Field(..., examples=["monday_email_blast"])
    trigger: str = Field(..., description="'cron' or 'interval'", pattern="^(cron|interval)$")
    cron: Optional[CronSpec] = None
    interval: Optional[IntervalSpec] = None
    params: Dict[str, Any] = Field(default_factory=dict)

class JobOut(BaseModel):
    id: int
    name: str
    trigger: str
    params: Dict[str, Any]
    status: str
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class JobsPage(BaseModel):
    items: list[JobOut]
    count: int
    limit: int
    offset: int
