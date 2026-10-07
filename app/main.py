import os

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app import models
from app.database import Base, engine, get_db
from app.schemas import CertificateOut, JobCreate, JobCreated, JobStatus
from app.services import process_job, validate_recipient

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Bulk Certificate Generator")


def get_job_or_404(db: Session, job_id: int) -> models.Job:
    job = db.get(models.Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/")
def health_check():
    return {"message": "Certificate generator is running"}


@app.post("/jobs", response_model=JobCreated, status_code=202)
def create_job(
    payload: JobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    job = models.Job(
        course_name=payload.course_name,
        issued_on=payload.issued_on,
        status="pending",
    )
    db.add(job)

    valid = 0
    invalid = 0
    for r in payload.recipients:
        error = validate_recipient(r.name, r.email)
        cert = models.Certificate(
            job=job,
            recipient_name=(r.name or "").strip(),
            recipient_email=(r.email or "").strip(),
            status="failed" if error else "pending",
            error_message=error,
        )
        db.add(cert)
        if error:
            invalid += 1
        else:
            valid += 1

    if valid == 0:
        job.status = "failed"

    db.commit()
    db.refresh(job)

    if valid > 0:
        background_tasks.add_task(process_job, job.id)

    return JobCreated(
        job_id=job.id,
        status=job.status,
        total=len(payload.recipients),
        valid=valid,
        invalid=invalid,
    )


@app.get("/jobs/{job_id}", response_model=JobStatus)
def get_job_status(job_id: int, db: Session = Depends(get_db)):
    job = get_job_or_404(db, job_id)
    certs = job.certificates

    total = len(certs)
    successful = sum(1 for c in certs if c.status == "success")
    failed = sum(1 for c in certs if c.status == "failed")
    pending = total - successful - failed
    progress = round((successful + failed) / total * 100, 1) if total else 0.0

    return JobStatus(
        job_id=job.id,
        status=job.status,
        course_name=job.course_name,
        issued_on=job.issued_on,
        total=total,
        successful=successful,
        failed=failed,
        pending=pending,
        progress_percent=progress,
        failures=[CertificateOut.model_validate(c) for c in certs if c.status == "failed"],
    )


@app.get("/jobs/{job_id}/certificates", response_model=list[CertificateOut])
def list_certificates(job_id: int, db: Session = Depends(get_db)):
    job = get_job_or_404(db, job_id)
    return job.certificates


@app.get("/jobs/{job_id}/certificates/{cert_id}/download")
def download_certificate(job_id: int, cert_id: int, db: Session = Depends(get_db)):
    get_job_or_404(db, job_id)
    cert = db.get(models.Certificate, cert_id)

    if cert is None or cert.job_id != job_id:
        raise HTTPException(status_code=404, detail="Certificate not found in this job")
    if cert.status != "success":
        raise HTTPException(
            status_code=409,
            detail=f"Certificate is not available (status: {cert.status})",
        )
    if not cert.file_path or not os.path.exists(cert.file_path):
        raise HTTPException(status_code=404, detail="Certificate file is missing")

    return FileResponse(
        cert.file_path,
        media_type="application/pdf",
        filename=f"certificate_{cert.id}.pdf",
    )