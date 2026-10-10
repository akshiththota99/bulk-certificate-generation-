# Certificate routes
import os
from pathlib import Path

from fastapi.responses import FileResponse
from fastapi import APIRouter
from fastapi import HTTPException

from app.database import SessionLocal
from app.models import Job, Certificate
from app.schemas import CertificateRequest
from app.services.generator import generate_certificate

router = APIRouter()
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _resolve_certificate_path(file_path: str | None) -> str:
    if not file_path:
        raise HTTPException(status_code=404, detail="Certificate file not found")

    candidate = Path(file_path)
    if not candidate.is_absolute():
        candidate = (PROJECT_ROOT / candidate).resolve()

    return str(candidate)


def _serialize_certificate(certificate):
    return {
        "id": certificate.id,
        "job_id": certificate.job_id,
        "recipient_name": certificate.recipient_name,
        "email": certificate.email,
        "course_name": certificate.course_name,
        "status": certificate.status,
        "certificate_path": certificate.certificate_path,
        "error_message": certificate.error_message,
    }


@router.get("/")
def root():
    return {
        "message": "Bulk Certificate Generator API is running",
        "endpoints": [
            "/jobs",
            "/jobs/{job_id}",
            "/jobs/{job_id}/certificates"
        ]
    }


@router.post("/jobs")
def create_job(request: CertificateRequest):

    db = SessionLocal()

    try:
        job = Job(
            total_recipients=len(
                request.recipients
            )
        )

        db.add(job)
        db.commit()
        db.refresh(job)

        for recipient in request.recipients:
            try:
                output_dir = PROJECT_ROOT / "app" / "generated"
                output_dir.mkdir(parents=True, exist_ok=True)

                file_path = str((output_dir / f"{recipient.name}_{job.id}.pdf").resolve())

                generate_certificate(
                    recipient.name,
                    request.course_name,
                    file_path
                )

                cert = Certificate(
                    job_id=job.id,
                    recipient_name=recipient.name,
                    email=recipient.email,
                    course_name=request.course_name,
                    status="SUCCESS",
                    certificate_path=file_path
                )

                db.add(cert)
                job.success_count += 1

            except Exception as e:
                cert = Certificate(
                    job_id=job.id,
                    recipient_name=recipient.name,
                    email=recipient.email,
                    course_name=request.course_name,
                    status="FAILED",
                    error_message=str(e)
                )

                db.add(cert)
                job.failure_count += 1

        job.status = "COMPLETED"
        db.commit()

        return {
            "job_id": job.id,
            "status": job.status
        }
    finally:
        db.close()


@router.get("/jobs/{job_id}")
def get_job(job_id: int):

    db = SessionLocal()

    try:
        job = db.query(Job).filter(
            Job.id == job_id
        ).first()

        if not job:
            raise HTTPException(
                status_code=404,
                detail={
                    "message": "Job not found",
                    "job_id": job_id,
                    "suggestion": "Create a new job before requesting job details."
                }
            )

        return {
            "job_id": job.id,
            "status": job.status,
            "total": job.total_recipients,
            "success": job.success_count,
            "failed": job.failure_count
        }
    finally:
        db.close()


@router.get("/jobs/{job_id}/certificates")
def get_certificates(job_id: int):

    db = SessionLocal()

    try:
        certificates = db.query(
            Certificate
        ).filter(
            Certificate.job_id == job_id
        ).all()

        serialized = [_serialize_certificate(item) for item in certificates]

        if not certificates:
            return {
                "job_id": job_id,
                "message": "No certificates were found for this job yet.",
                "certificates": []
            }

        return {
            "job_id": job_id,
            "message": "Certificates retrieved successfully.",
            "certificates": serialized
        }
    finally:
        db.close()

@router.get("/certificates/{certificate_id}")
def download_certificate(certificate_id: int):

    db = SessionLocal()

    try:
        certificate = db.query(
            Certificate
        ).filter(
            Certificate.id == certificate_id
        ).first()

        if not certificate:
            raise HTTPException(
                status_code=404,
                detail="Certificate not found"
            )

        file_path = _resolve_certificate_path(certificate.certificate_path)
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=404,
                detail="Certificate file not found"
            )

        return FileResponse(
            file_path,
            media_type="application/pdf",
            filename=f"{certificate.recipient_name.replace(' ', '_')}.pdf"
        )
    finally:
        db.close()