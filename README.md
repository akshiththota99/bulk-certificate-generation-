# Bulk Certificate Generator

A FastAPI-based backend for generating bulk certificates from a single predefined template.

## Features

- Accepts a certificate generation request with many recipients in one API call
- Validates recipient data using Pydantic
- Generates a PDF certificate for each valid recipient
- Tracks job progress and per-recipient success/failure status
- Provides endpoints to check job status and retrieve certificates

## Project Structure

- `app/` - application source code
- `app/routes/` - API endpoints
- `app/services/` - certificate generation logic
- `app/generated/` - generated PDFs
- `tests/` - automated tests
- `requirements.txt` - Python dependencies

## Setup

1. Create and activate a virtual environment
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Run the Application

```bash
uvicorn app.main:app --reload
```

The API will be available at:

- http://127.0.0.1:8000

## Run Tests

```bash
pytest
```

## Submit a Certificate Generation Request

Send a POST request to:

```http
POST /jobs
Content-Type: application/json
```

Example payload:

```json
{
  "course_name": "Python Fundamentals",
  "recipients": [
    {
      "name": "Alice Johnson",
      "email": "alice@example.com"
    },
    {
      "name": "Bob Smith",
      "email": "bob@example.com"
    }
  ]
}
```

## Check Job Status

```http
GET /jobs/{job_id}
```

Response includes:

- `job_id`
- `status`
- `total`
- `success`
- `failed`

## Retrieve Generated Certificates

```http
GET /jobs/{job_id}/certificates
```

Or download a single certificate:

```http
GET /certificates/{certificate_id}
```

## Design Decisions

- Chose FastAPI because it is lightweight, fast, and well-suited to JSON APIs.
- Used SQLite as the relational database for simplicity and local development.
- Used a single predefined certificate template to satisfy the requirement for fixed-format certificate generation.
- Processed the bulk request synchronously for simplicity. This is a good fit for moderate certificate volumes and keeps the implementation easy to understand and debug.
- Individual recipient failures are isolated so one bad record does not stop the rest of the job from being processed.
