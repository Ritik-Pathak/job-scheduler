import time
import logging

logger = logging.getLogger(__name__)

def send_email_job(job_id: int, to: str, subject: str = "Hello", **kwargs):
    # Dummy email sending
    logger.info("Job %s: sending email to %s subject=%s kwargs=%s", job_id, to, subject, kwargs)
    # Simulate work
    time.sleep(1)
    logger.info("Job %s: email sent", job_id)

def number_crunch_job(job_id: int, dataset: str = "default", **kwargs):
    logger.info("Job %s: crunching numbers on dataset=%s ...", job_id, dataset)
    time.sleep(2)
    logger.info("Job %s: crunch done", job_id)

# Registry mapping for dynamic execution
EXECUTOR_REGISTRY = {
    "email": send_email_job,
    "compute": number_crunch_job,
}
