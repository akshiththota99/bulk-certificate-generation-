import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.main import app
import app.routes.certificates as cert_routes
from app.models import Certificate, Job


@pytest.fixture
def client(monkeypatch, tmp_path):
    db_path = tmp_path / "test_certificates.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
    Base.metadata.create_all(bind=engine)
    monkeypatch.setattr(cert_routes, "SessionLocal", TestingSessionLocal)

    with TestClient(app) as test_client:
        yield test_client


def test_create_generation_job(client):
    payload = {
        "course_name": "Python Fundamentals",
        "recipients": [
            {"name": "Alice Johnson", "email": "alice@example.com"},
            {"name": "Bob Smith", "email": "bob@example.com"},
        ],
    }

    response = client.post("/jobs", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert "job_id" in body
    assert body["status"] == "COMPLETED"

    job_id = body["job_id"]
    session = cert_routes.SessionLocal()
    try:
        job = session.query(Job).filter(Job.id == job_id).first()
        assert job is not None
        assert job.total_recipients == 2
        assert job.success_count == 2
        assert job.failure_count == 0

        certificates = session.query(Certificate).filter(Certificate.job_id == job_id).all()
        assert len(certificates) == 2
        for cert in certificates:
            assert cert.status == "SUCCESS"
            assert os.path.exists(cert.certificate_path)
    finally:
        session.close()


def test_input_validation_rejects_bad_email(client):
    payload = {
        "course_name": "Python Fundamentals",
        "recipients": [
            {"name": "Alice Johnson", "email": "not-an-email"},
        ],
    }

    response = client.post("/jobs", json=payload)

    assert response.status_code == 422


def test_generate_certificate_creates_pdf_file(tmp_path):
    output_path = tmp_path / "sample_certificate.pdf"
    cert_routes.generate_certificate("Jane Doe", "Python Essentials", str(output_path))

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_job_status_and_progress(client):
    payload = {
        "course_name": "Data Science Basics",
        "recipients": [
            {"name": "Charlie", "email": "charlie@example.com"},
            {"name": "Dana", "email": "dana@example.com"},
        ],
    }

    create_response = client.post("/jobs", json=payload)
    job_id = create_response.json()["job_id"]

    status_response = client.get(f"/jobs/{job_id}")

    assert status_response.status_code == 200
    body = status_response.json()
    assert body["total"] == 2
    assert body["success"] == 2
    assert body["failed"] == 0
    assert body["status"] == "COMPLETED"


def test_individual_certificate_failure_does_not_stop_others(client, monkeypatch):
    original = cert_routes.generate_certificate

    def fake_generate(recipient_name, course_name, output_path):
        if recipient_name == "Alice Johnson":
            raise ValueError("Simulated PDF generation failure")
        return original(recipient_name, course_name, output_path)

    monkeypatch.setattr(cert_routes, "generate_certificate", fake_generate)

    payload = {
        "course_name": "Workshop Completion",
        "recipients": [
            {"name": "Alice Johnson", "email": "alice@example.com"},
            {"name": "Bob Smith", "email": "bob@example.com"},
        ],
    }

    response = client.post("/jobs", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "COMPLETED"

    job_id = body["job_id"]
    status_response = client.get(f"/jobs/{job_id}")
    progress = status_response.json()
    assert progress["success"] == 1
    assert progress["failed"] == 1

    certs_response = client.get(f"/jobs/{job_id}/certificates")
    certs = certs_response.json()["certificates"]
    assert len(certs) == 2
    assert any(item["status"] == "SUCCESS" for item in certs)
    assert any(item["status"] == "FAILED" for item in certs)


def test_retrieve_generated_certificates(client):
    payload = {
        "course_name": "Certificate Course",
        "recipients": [
            {"name": "Eve", "email": "eve@example.com"},
        ],
    }

    create_response = client.post("/jobs", json=payload)
    job_id = create_response.json()["job_id"]

    response = client.get(f"/jobs/{job_id}/certificates")
    body = response.json()

    assert response.status_code == 200
    assert body["job_id"] == job_id
    assert len(body["certificates"]) == 1
    assert body["certificates"][0]["recipient_name"] == "Eve"

    cert_id = body["certificates"][0]["id"]
    download_response = client.get(f"/certificates/{cert_id}")
    assert download_response.status_code == 200
    assert download_response.headers["content-type"].startswith("application/pdf")


def test_download_missing_certificate_returns_404(client):
    db = cert_routes.SessionLocal()
    try:
        job = Job(status="COMPLETED", total_recipients=1, success_count=0, failure_count=0)
        db.add(job)
        db.commit()
        db.refresh(job)

        cert = Certificate(
            job_id=job.id,
            recipient_name="Ghost User",
            email="ghost@example.com",
            course_name="Missing Course",
            status="SUCCESS",
            certificate_path="app/generated/missing_certificate.pdf",
        )
        db.add(cert)
        db.commit()
        db.refresh(cert)

        response = client.get(f"/certificates/{cert.id}")
        assert response.status_code == 404
        assert response.json()["detail"] == "Certificate file not found"
    finally:
        db.close()
