# S.E.H.A.T: Scalable and Efficient Healthcare Access Tool

A WhatsApp-first healthcare access platform for semi-urban and rural India, deployed on AWS. Patients use only WhatsApp (text, location pin or photo). Doctors, chemists, blood banks and admins use a role-based React web portal.

Built by **Aman Chhimwal** and **Yashasvi Pandey** at CHRIST (Deemed to be University), Delhi NCR Campus. Cloud version submitted for *Applied Cloud Computing and Architecture (BCA302-5)*.

## Features

- **Live doctor queue**: nearby doctors from a location pin, numbered token, queue position, estimated wait, and alerts at #2, #1 and when called.
- **Prescription reader**: Gemini Vision extracts medicines, dosage and duration from a photo, with a confidence score.
- **Hindi explanation**: reply `EXPLAIN` for a simple Hindi explanation of each medicine, with an AI disclaimer.
- **Pharmacy matcher**: nearest chemist with the medicines in stock, with a split-order suggestion if no single shop has everything.
- **Blood-bank locator**: `BLOOD B+` or `KHOON B+` returns the nearest banks holding the group.
- **Role-based portals**: doctor, chemist, blood bank and admin dashboards with JWT login.

## Cloud architecture (AWS)

```
Patient (WhatsApp) -> UltraMsg -> Cloudflare Tunnel (HTTPS) -> FastAPI on Amazon EC2 :8000
                                                                  |-> Google Gemini (OCR + Hindi)
                                                                  |-> Amazon S3 via IAM instance profile
```

- **EC2**: Ubuntu 24.04 LTS, native Python 3.12 virtual environment, no Docker.
- **S3**: private bucket (Block All Public Access) storing `prescriptions/<hash>/` images and `ocr_audit/<hash>/` JSON audit logs.
- **IAM**: boto3 uses the EC2 instance profile (LabRole), so no AWS keys are stored.
- **Pre-signed URLs**: time-limited links for viewing stored images.
- **Fallback**: if S3 is disabled or unreachable, files are saved to local `uploads/`.
- **Security group**: inbound 22, 80, 443 and 8000 only.

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite 5, Tailwind CSS 3.4, Axios |
| Backend | FastAPI, Uvicorn, SQLAlchemy 2.0 (async), Pydantic |
| AI | Google Gemini (Vision OCR and Hindi translation) |
| Messaging | UltraMsg WhatsApp gateway |
| Database | SQLite (demo), PostgreSQL via `DATABASE_URL` |
| Cloud | Amazon EC2, S3, IAM, boto3, Cloudflare Tunnel |
| Security | bcrypt, JWT (python-jose), salted SHA-256 phone hashing |

## Project structure

```
backend/     FastAPI app: routers, services, models, seed_dev.py
frontend/    React portal (Vite)
```

## Getting started

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python seed_dev.py               # load the Ghaziabad demo data
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Set `VITE_API_URL` to your backend URL (defaults to `http://localhost:8000`).

### Environment variables

Create a `.env` file in `backend/`. Never commit it.

```
GEMINI_API_KEY=<your key>
ULTRAMSG_INSTANCE_ID=<your instance>
ULTRAMSG_TOKEN=<your token>
S3_BUCKET_NAME=<your bucket>
AWS_REGION=us-east-1
DATABASE_URL=<optional, defaults to SQLite>
```

No AWS access keys are needed on EC2: boto3 reads credentials from the instance profile.

### Connecting WhatsApp

Run `cloudflared tunnel --url http://localhost:8000` on the server, then paste the HTTPS address into the **Webhook URL on Received** setting in the UltraMsg dashboard. A quick tunnel gets a new address on every start, so update it after each restart.

## Privacy

- Patient phone numbers are stored only as salted SHA-256 hashes.
- S3 object keys contain only the hash, never a readable identifier.
- Production use would need a consent notice, a retention and deletion policy, and a review against the Digital Personal Data Protection Act, 2023.

## Known limitations

- If the Gemini call fails, OCR returns a built-in sample prescription (demo convenience).
- Alert history is held in memory, so a restart can repeat alerts.
- No automated test suite yet.
- Single EC2 instance with a local database: no load balancer, auto scaling or managed database.

## Future scope

Amazon RDS, load balancing and auto scaling, CloudWatch monitoring, Secrets Manager, S3 lifecycle rules, infrastructure as code, the official WhatsApp Business Cloud API, semantic medicine matching, and more languages with voice notes.

## Disclaimer

Hindi explanations and prescription readings are AI-generated for informational support only and are not medical advice.
