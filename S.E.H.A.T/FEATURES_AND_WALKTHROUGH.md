# SEHAT Platform — Master Features & Integration Walkthrough

This document consolidates every feature, business rule, database structure, and automated verification result across all development phases of the SEHAT healthcare coordination platform.

---

## 🌟 Core System Features

### 1. Doctor Clinic Queues (FLOW 1)
- **Clinic Registry**: Tracks doctor coordinates, clinical address, specialization, operational status, average session duration, and real-time wait estimation.
- **Geolocated Search**: Calculates nearby clinics using the Haversine formula (2km default radius, auto-expanding to 5km if no available doctor is found).
- **Interactive Booking**: Patients booking queues receive an active token number and real-time ETA via SMS/WhatsApp message alerts.
- **Token Auto-Cancellation (Rule 1)**: Cron-based background schedulers scan active bookings and automatically cancel tokens if a patient has been called but fails to check in within 30 minutes.
- **Doctor Offline Notification (Rule 2)**: Toggling a doctor's status to "offline" triggers bulk UltraMsg WhatsApp notifications to all waiting token holders.
- **Doctor Dashboard UI**: Real-time patient queues controller with "Call Patient", "Mark Seen", and "Cancel Token" functions.

### 2. Pharmacy Stock Management (FLOW 2 - Part A)
- **Inventory Registry**: Chemists register shop locations and manage medicine stock counts.
- **Autocomplete Drug Catalog**: Real-time drug matching database compiling generic names, strengths (e.g. 500mg), dosage forms (e.g. Tablet), and brand names equivalents (e.g. Paracetamol matching Calpol, Crocin, Dolo).
- **Staleness Tracking (Rule 3)**: Chemist stocks unupdated for over 24 hours display a distinct "Inventory Unverified" indicator on both WhatsApp text listings and the chemist dashboard.
- **Chemist Dashboard UI**: High-fidelity stock catalog editor with autocomplete addition inputs and warning logs.

### 3. AI Prescription OCR & Hindi Explanations (FLOW 2 - Part B)
- **Gemini Vision OCR**: Employs Gemini Flash to parse uploaded photos of hand-written/printed prescriptions, returning structured JSON lists of drug names, strengths, and dosages.
- **Confidence Guard (Rule 10)**: Reject scans returning below a 60% confidence threshold, replying with: *"Unable to parse clearly. Please upload a clearer image of your prescription."*
- **Split-Chemist Matching (Rule 7)**: If a single nearby pharmacy does not carry all prescribed items, the engine automatically calculates a two-chemist split combination covering all drugs at minimal combined distance.
- **Hindi Explanation Generator (Rule 11)**: Uses LLM translations to create low-literacy, friendly Hindi conversational descriptions explaining dosage frequencies and instructions (e.g. *"दिन में दो बार भोजन के बाद लें"*).
- **Image Privacy Enforcement (Rule 12)**: Automatically deletes uploaded raw prescription images from local disk space immediately after parsing, storing only structured metadata and patient text logs.

### 4. Blood Bank Proximity Engine (FLOW 3)
- **Emergency Matching (Rule 5)**: Searches blood banks within 2km, expanding to 5km. If no matching group units exist, the system triggers an emergency override to return the closest available blood bank carrying that group *regardless of distance*.
- **Group Normalizer (Rule 8)**: Parses varied expressions (e.g. `"BLOOD B+"`, `"KHOON B+"`, `"b positive"`, `"b+"`, `"B positive blood"`) to standardized code strings (e.g. `B+`).
- **Blood Stock Staleness (Rule 4)**: Flags blood units unupdated for over 12 hours as unverified.
- **Zero Units Filter (Rule 9)**: Never lists blood banks with `units_available <= 0`.
- **Blood Bank Dashboard UI**: Displays units available per group and precise manual update adjustments.

### 5. Access Control, Rate Limiting & Platform Security
- **Dashboards Login Gate**: Login tab switcher verifying JWT credentials for role `doctor`, `chemist`, `blood_bank`, or `admin`.
- **Bcrypt Native Hashing**: Implements native Python bcrypt hashing, avoiding historical 72-byte string truncation bugs on Python 3.12+.
- **Supabase Authentication Dependency**: Automatically decodes and validates incoming Bearer JWT tokens against live Supabase Auth profiles (`/auth/v1/user`) if a `SUPABASE_URL` is set, falling back to local JWT signatures offline.
- **Axios HTTP Client Interceptors**: Client-side axios interceptors inject auth tokens on outgoing headers and trigger login page redirects on `401 Unauthorized` responses.
- **WhatsApp Message Rate Limiter (Rule 13)**: Restricts patient phone numbers to a maximum of 10 incoming messages per hour, responding with localized rate limit warnings if exceeded.

---

## 📁 File Structure Map

| Module | File Path | Description |
|---|---|---|
| **Database schemas** | [doctor.py](file:///c:/Users/YASHASVI%20PANDEY/Desktop/S.E.H.A.T/backend/models/doctor.py) | Doctors ORM mapping |
| | [chemist.py](file:///c:/Users/YASHASVI%20PANDEY/Desktop/S.E.H.A.T/backend/models/chemist.py) | Chemists and Medicines catalog |
| | [patient.py](file:///c:/Users/YASHASVI%20PANDEY/Desktop/S.E.H.A.T/backend/models/patient.py) | Patients profiles and rate limiting logs |
| | [blood_bank.py](file:///c:/Users/YASHASVI%20PANDEY/Desktop/S.E.H.A.T/backend/models/blood_bank.py) | Blood banks and group stocks |
| **Business Services**| [auth_service.py](file:///c:/Users/YASHASVI%20PANDEY/Desktop/S.E.H.A.T/backend/services/auth_service.py) | JWT authentication controls & Supabase hook |
| | [medicine_service.py](file:///c:/Users/YASHASVI%20PANDEY/Desktop/S.E.H.A.T/backend/services/medicine_service.py) | 2-chemist combination matcher |
| | [blood_service.py](file:///c:/Users/YASHASVI%20PANDEY/Desktop/S.E.H.A.T/backend/services/blood_service.py) | Emergency distance matching calculations |
| | [ocr_service.py](file:///c:/Users/YASHASVI%20PANDEY/Desktop/S.E.H.A.T/backend/services/ocr_service.py) | Gemini vision prescription scanner |
| | [translation_service.py](file:///c:/Users/YASHASVI%20PANDEY/Desktop/S.E.H.A.T/backend/services/translation_service.py) | Hindi translation explainer |
| **API Endpoints** | [auth.py](file:///c:/Users/YASHASVI%20PANDEY/Desktop/S.E.H.A.T/backend/routers/auth.py) | Handles session logins |
| | [whatsapp.py](file:///c:/Users/YASHASVI%20PANDEY/Desktop/S.E.H.A.T/backend/routers/whatsapp.py) | UltraMsg message webhook processor |
| **Frontend UI** | [App.jsx](file:///c:/Users/YASHASVI%20PANDEY/Desktop/S.E.H.A.T/frontend/src/App.jsx) | Tab-routers and auth session switch |
| | [LoginPage.jsx](file:///c:/Users/YASHASVI%20PANDEY/Desktop/S.E.H.A.T/frontend/src/pages/LoginPage.jsx) | 4-tab role selector interface |
| | [BloodBankDashboard.jsx](file:///c:/Users/YASHASVI%20PANDEY/Desktop/S.E.H.A.T/frontend/src/pages/BloodBankDashboard.jsx) | Blood bank inventory card grid |
| **Deployment** | [Dockerfile](file:///c:/Users/YASHASVI%20PANDEY/Desktop/S.E.H.A.T/backend/Dockerfile) | Backend server container |
| | [Dockerfile](file:///c:/Users/YASHASVI%20PANDEY/Desktop/S.E.H.A.T/frontend/Dockerfile) | Web build served via Nginx |
| | [docker-compose.yml](file:///c:/Users/YASHASVI%20PANDEY/Desktop/S.E.H.A.T/docker-compose.yml) | DB, API, and frontend compose file |
| | [DEPLOYMENT.md](file:///c:/Users/YASHASVI%20PANDEY/Desktop/S.E.H.A.T/DEPLOYMENT.md) | Operations and hosting manual |
| | [schema_and_seed.sql](file:///c:/Users/YASHASVI%20PANDEY/Desktop/S.E.H.A.T/schema_and_seed.sql) | Production PostgreSQL seed dump |
