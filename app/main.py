import logging
from fastapi import FastAPI
from .config import settings
from .database import init_db
from .api.routes import router as api_router
from .services.scheduler import scheduler_service

logging.basicConfig(level=logging.INFO)

tags_metadata = [
    {
        "name": "Jobs",
        "description": "Create and manage scheduled jobs. Supports cron and interval triggers.",
    }
]

app = FastAPI(
    title="Scheduler Service",
    version="0.1.0",
    description="A microservice for scheduling and managing jobs.",
    openapi_tags=tags_metadata
)

@app.on_event("startup")
def on_startup():
    init_db()
    scheduler_service.start()

@app.on_event("shutdown")
def on_shutdown():
    scheduler_service.shutdown()

app.include_router(api_router)
