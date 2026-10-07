# Bulk Certificate Generator API

A backend API that accepts a list of recipients, generates a PDF certificate for each valid recipient, tracks the results, and lets clients check job progress and download certificates.

## Features

- Accept many recipients in one request
- Validate recipient names and email addresses
- Generate PDF certificates from one predefined template
- Continue processing if an individual certificate fails
- Track job status and progress
- List certificates and download successfully generated PDFs

## Technology

- Python
- FastAPI
- SQLAlchemy
- SQLite
- ReportLab
- Pytest

## Setup

Create and activate a virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Install the dependencies:

```powershell
python -m pip install fastapi "uvicorn[standard]" sqlalchemy reportlab pytest httpx
```

## Run the application

From the project root, run:

```powershell
python -m uvicorn app.main:app --reload
```

Open the API documentation at:

```text
http://127.0.0.1:8000/docs
```

The app creates a local SQLite database named `certificates.db`. Generated PDFs are saved in the `certificates/` folder.

## Run the tests

From the project root, run:

```powershell
python -m pytest -q
```

## API endpoints

### Health check

```http
GET /
```

### Create a generation job

```http
POST /jobs
```

Example request:

```json
{
  "course_name": "Python Workshop",
  "issued_on": "2026-10-07",
  "recipients": [
    {
      "name": "Asha Rao",
      "email": "asha@example.com"
    },
    {
      "name": "Ravi Kumar",
      "email": "ravi@example.com"
    }
  ]
}
```

The API returns HTTP `202 Accepted`, a job ID, and recipient counts. Invalid recipients are recorded as failures while valid recipients continue processing.

### Check job status and progress

```http
GET /jobs/{job_id}
```

Returns the job status, recipient counts, progress percentage, and details about failed certificates.

### List certificates for a job

```http
GET /jobs/{job_id}/certificates
```

Returns each certificate's ID, recipient information, status, and any error message.

### Download a certificate

```http
GET /jobs/{job_id}/certificates/{cert_id}/download
```

Downloads the PDF for a successfully generated certificate.

## Design decisions

- A single bulk request creates one job containing all recipients.
- Each recipient is validated separately. An invalid recipient is marked failed without blocking valid recipients.
- FastAPI `BackgroundTasks` handles generation after the job response is returned. This keeps the project simple and avoids requiring a separate queue service.
- Each certificate result is saved as it is processed, so completed work is recorded even if a later certificate fails.
- PDF filenames use certificate IDs rather than recipient names to avoid duplicate names and unsafe filename characters.
- The project uses one predefined certificate template, as required by the assignment.

## What I learned

This project helped me practice building REST APIs with FastAPI, working with a relational database through SQLAlchemy, generating PDFs, handling failures in bulk processing, and testing API behavior with pytest.

## Future scope

- Use a durable background job queue such as Celery with Redis.
- Add authentication and authorization.
- Support multiple certificate templates.
- Add pagination for large certificate lists.
- Store generated PDFs in cloud object storage.