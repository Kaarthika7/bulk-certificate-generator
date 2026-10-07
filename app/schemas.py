from pydantic import BaseModel, ConfigDict, Field


class RecipientIn(BaseModel):
    name: str | None = None
    email: str | None = None


class JobCreate(BaseModel):
    course_name: str = Field(min_length=1, max_length=200)
    issued_on: str = Field(min_length=1, max_length=50)
    recipients: list[RecipientIn] = Field(min_length=1, max_length=1000)


class JobCreated(BaseModel):
    job_id: int
    status: str
    total: int
    valid: int
    invalid: int


class CertificateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    recipient_name: str
    recipient_email: str
    status: str
    error_message: str | None = None


class JobStatus(BaseModel):
    job_id: int
    status: str
    course_name: str
    issued_on: str
    total: int
    successful: int
    failed: int
    pending: int
    progress_percent: float
    failures: list[CertificateOut]