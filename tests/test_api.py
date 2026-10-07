from app import services
from app.generator import generate_certificate


def sample_payload():
    return {
        "course_name": "Python Workshop",
        "issued_on": "2026-10-07",
        "recipients": [
            {"name": "Asha Rao", "email": "asha@example.com"},
            {"name": "Ravi Kumar", "email": "ravi@example.com"},
        ],
    }


def test_create_job(client):
    response = client.post("/jobs", json=sample_payload())

    assert response.status_code == 202
    body = response.json()
    assert body["total"] == 2
    assert body["valid"] == 2
    assert body["invalid"] == 0


def test_invalid_recipient_is_recorded(client):
    payload = sample_payload()
    payload["recipients"] = [{"name": "Meera", "email": "not-an-email"}]

    response = client.post("/jobs", json=payload)

    assert response.status_code == 202
    assert response.json()["invalid"] == 1

    job_id = response.json()["job_id"]
    certificates = client.get(f"/jobs/{job_id}/certificates").json()

    assert certificates[0]["status"] == "failed"
    assert certificates[0]["error_message"] == "A valid email is required"


def test_certificate_generation_creates_pdf(tmp_path):
    output_path = tmp_path / "certificate.pdf"

    generate_certificate(
        name="Asha Rao",
        course_name="Python Workshop",
        issued_on="2026-10-07",
        output_path=str(output_path),
    )

    assert output_path.exists()
    assert output_path.read_bytes().startswith(b"%PDF")


def test_job_status_reports_progress(client):
    payload = sample_payload()
    payload["recipients"].append({"name": "", "email": "nobody@example.com"})

    create_response = client.post("/jobs", json=payload)
    job_id = create_response.json()["job_id"]

    response = client.get(f"/jobs/{job_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert body["successful"] == 2
    assert body["failed"] == 1
    assert body["pending"] == 0
    assert body["progress_percent"] == 100.0


def test_one_generation_failure_does_not_stop_the_rest(client, monkeypatch):
    real_generator = services.generate_certificate

    def fail_for_ravi(name, course_name, issued_on, output_path):
        if name == "Ravi Kumar":
            raise RuntimeError("Simulated PDF error")
        real_generator(name, course_name, issued_on, output_path)

    monkeypatch.setattr(services, "generate_certificate", fail_for_ravi)

    create_response = client.post("/jobs", json=sample_payload())
    job_id = create_response.json()["job_id"]

    status = client.get(f"/jobs/{job_id}").json()

    assert status["status"] == "completed_with_errors"
    assert status["successful"] == 1
    assert status["failed"] == 1

    certificates = client.get(f"/jobs/{job_id}/certificates").json()
    results = {c["recipient_name"]: c["status"] for c in certificates}
    assert results == {"Asha Rao": "success", "Ravi Kumar": "failed"}


def test_generated_certificate_can_be_retrieved(client):
    create_response = client.post("/jobs", json=sample_payload())
    job_id = create_response.json()["job_id"]

    certificates = client.get(f"/jobs/{job_id}/certificates").json()
    successful_certificate = next(c for c in certificates if c["status"] == "success")

    response = client.get(
        f"/jobs/{job_id}/certificates/{successful_certificate['id']}/download"
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")