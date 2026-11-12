# SEHAT — Project Status (Revised Scope)

Here is the current status of all features, business rules, and tech stack items following the integration of the **Blood Bank System (FLOW 3)** and **Secure Authentication Gate (Phase 4)**.

---

## ✅ What is Done

### 1. Database & Schema Models
- **ORM Schema Models** (`backend/models/`):
  - `Doctor` (clinic details, geolocation, availability status, average wait metrics)
  - `Chemist` (pharmacy profile, open status)
  - `Medicine` (generic name, brand names JSON array, standard dosages)
  - `ChemistStock` (inventory updates tracking last updated timestamp)
  - `QueueToken` (waiting, called, seen, cancelled status logs)
  - `PrescriptionLog` (Vision JSON results, cached translation explanation, OCR confidence score)
  - `BloodBank` (phone, location, is_open_24hrs, closing/opening times)
  - `BloodStock` (blood group units count, unique key constraint)
  - `Patient` (session state logs, language, coordinates history)
  - `Admin` (analytics dashboard profile credentials)

### 2. Services & Business Logics (`backend/services/`)
- **OCR Parser (`ocr_service.py`)**: Vision extraction prompt utilizing Gemini API.
- **Hindi Translator (`translation_service.py`)**: Plain-language low-literacy explanation formatter for patient prescriptions.
- **Medicine Stock Matcher (`medicine_service.py`)**: CDSCO catalog matching with token length guards (preventing substring false positives), Haversine distance, radius expansion (5km → 25km), and 2-chemist combination fallback split matching.
- **Queue Controller (`queue_service.py`)**: Token booking, sequential queue progression notifications (`#2 in line` and `#1 in line`), alert deduplication tracking, and auto-calling next patient on consultation completion.
- **Notification Client (`notification_service.py`)**: UltraMsg WhatsApp provider with logging and graceful fallback.
- **Location Helper (`location_service.py`)**: Haversine formula distance calculations.
- **Blood Stock Service (`blood_service.py`)**: Proximity matching with default radius (2km), expanded search (5km), emergency closest fallback (Rule 5), zero units filtering (Rule 9), and 12-hour staleness verification (Rule 4).

### 3. API Routers (`backend/routers/`)
- `/api/auth/login` & `/me`: Handle secure user session credentials validations and token creation.
- `/api/doctors/*`: Manage doctor clinics availability toggles and listings.
- `/api/chemists/*`: Autocomplete search of medicines, bulk stock inventory updates.
- `/api/tokens/*`: Handle clinic queue status updates.
- `/api/blood-banks/*`: Bulk update available units per group, read stock cards inventory.
- `/api/admin/analytics`: Central analytics metrics.
- `/ultramsg` & `/api/whatsapp/webhook`: UltraMsg webhook dispatcher routing FLOW 1 (doctor booking), FLOW 2 (prescription scans and Hindi explanations), and FLOW 3 (blood group search by coordinates).

### 4. React Frontend Dashboards (`frontend/src/`)
- **LoginPage**: Tab selectors matching role credentials.
- **DoctorDashboard**: Live queue updates, availability toggler.
- **ChemistDashboard**: Stock lists and autocomplete additions.
- **BloodBankDashboard**: Grid displaying group counts and incremental stock adjustment forms.
- **AdminDashboard**: Global analytics cards, scanned medicines ranks.
- **App.jsx**: Token checks, logout redirect, and dynamic tab rendering based on session roles.

---

- **WhatsApp Rate Limiter (Rule 13)**: Implemented query checks in `backend/routers/whatsapp.py` to count database logs against `whatsapp_message_logs` over the preceding hour. Blocks and issues warning alerts once count >= 10.
- **Supabase JWT Validator** (`backend/services/auth_service.py`): Created dual-mode authentication dependency. Calls `${SUPABASE_URL}/auth/v1/user` for session validation when live key parameters exist, falling back to local JWT validation for offline dev environments.
- **Dockerization Configs**: Created `backend/Dockerfile`, `frontend/Dockerfile`, `frontend/nginx.conf`, and `docker-compose.yml` defining unified multi-container setups.
- **Production Guide** (`DEPLOYMENT.md`): Step-by-step setup guides for PostgreSQL databases, Supabase keys, UltraMsg webhooks, and Vercel/Render hosting configurations.

---

## 🔶 What is Remaining (To Complete Production Polish)

### High Priority

| Feature | Requirement | Notes |
|---------|-------------|-------|
| 🗄️ **ChromaDB Integration** | Use ChromaDB vector embeddings for fuzzy medicine name matching. | Currently matches brands/generics exactly in SQL. ChromaDB will catch spelling errors (e.g. "paracetmol" → "Paracetamol"). |

### Medium Priority

| Feature | Requirement | Notes |
|---------|-------------|-------|
| 🧪 **Unit Tests** | Coverage for all service files and router logic. | Verification verified with scratch automated scripts. A standard `pytest` suite is recommended for CI/CD. |

