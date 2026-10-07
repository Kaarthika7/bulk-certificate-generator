import re

from app import models
from app.database import SessionLocal
from app.generator import generate_certificate

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
OUTPUT_DIR = "certificates"


def validate_recipient(name: str | None, email: str | None) -> str | None:
    """Return an error message if the recipient is invalid, else None."""
    if not name or not name.strip():
        return "Name is required"
    if not email or not EMAIL_RE.match(email.strip()):
        return "A valid email is required"
    return None


def process_job(job_id: int) -> None:
    """Generate a PDF for every pending certificate in the job."""
    db = SessionLocal()  # background task needs its OWN session
    try:
        job = db.get(models.Job, job_id)
        job.status = "processing"
        db.commit()

        pending = [c for c in job.certificates if c.status == "pending"]

        for cert in pending:
            try:
                path = f"{OUTPUT_DIR}/job_{job.id}/cert_{cert.id}.pdf"
                generate_certificate(
                    name=cert.recipient_name,
                    course_name=job.course_name,
                    issued_on=job.issued_on,
                    output_path=path,
                )
                cert.status = "success"
                cert.file_path = path
            except Exception as e:
                cert.status = "failed"
                cert.error_message = f"Generation failed: {e}"
            db.commit()  # save after each one, so progress is visible

        any_failed = any(c.status == "failed" for c in job.certificates)
        job.status = "completed_with_errors" if any_failed else "completed"
        db.commit()
    finally:
        db.close()