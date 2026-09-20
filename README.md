# NGO Impact Data Commons

A full-stack web platform designed to improve NGO transparency, accountability, donation tracking, project monitoring, evidence verification, and impact reporting.

The platform allows NGOs to manage their profiles and projects, upload project evidence, track expenses, maintain a tamper-evident ledger, and undergo automated project integrity and fraud-risk analysis. Administrators can review projects and investigate evidence-based risk findings.

---

# Features

- NGO registration and authentication
- Role-based access control
- Donor, NGO, and Admin dashboards
- Two-factor authentication / OTP verification
- NGO profile management
- Government verification
- NGO document management
- Project creation and management
- Project budget and expense tracking
- Beneficiary management
- Project evidence/photo/document uploads
- Photo integrity and duplicate-evidence detection
- SHA-256 file hashing
- Perceptual image hashing
- EXIF metadata inspection
- OCR-based document/invoice analysis
- Invoice amount and expense comparison
- Duplicate invoice detection
- Project financial-risk analysis
- Project evidence consistency analysis
- NGO/project identity cross-validation
- AI-assisted fraud-risk analysis
- Project integrity risk scoring
- Admin project review workflow
- Admin notifications
- Audit logging
- Tamper-evident SHA-256 hash-linked ledger
- Public transparency information
- AI Transparency Assistant
- REST API using FastAPI
- Next.js frontend
- SQLite database for development/demo

---

# Technology Stack

## Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS

## Backend

- Python
- FastAPI
- Uvicorn
- SQLAlchemy
- Pydantic
- JWT Authentication

## Database

- SQLite for development/demo
- PostgreSQL can be used for production

## Security and Verification

- JWT authentication
- Role-based authorization
- OTP / two-factor authentication
- SHA-256 hashing
- Perceptual image hashing
- Evidence integrity analysis
- Audit logging

---

# Project Structure

```text
NGO/
│
├── backend/
│   ├── app/
│   │   ├── models/
│   │   ├── routers/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── database.py
│   │   ├── dependencies.py
│   │   └── main.py
│   │
│   ├── uploads/
│   ├── .env
│   ├── db_init.py
│   ├── requirements.txt
│   └── ngo_commons.db
│
├── frontend/
│   ├── src/
│   │   └── app/
│   ├── public/
│   ├── package.json
│   └── .env.local
│
└── README.md


**Prerequisites**


python --version                       //Python 3.11.x
node --version             //Install Node.js.  , Check the installed versions:
npm --version
git clone <YOUR_GITHUB_REPOSITORY_URL>                       //Clone the Repository

Complete First-Time Execution

Terminal 1 — Backend
cd E:\NGO\backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python db_init.py
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

//Keep Terminal 1 running.

Terminal 2 — Frontend
cd E:\NGO\frontend
npm install
npm run dev

//Keep Terminal 2 running.


Browser
Open:http://localhost:3000


Normal Execution After Initial Setup

After the project has already been installed, you normally only need two terminals.

Terminal 1
cd E:\NGO\backend
.venv\Scripts\activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
Terminal 2
cd E:\NGO\frontend
npm run dev

Then open:

http://localhost:3000

