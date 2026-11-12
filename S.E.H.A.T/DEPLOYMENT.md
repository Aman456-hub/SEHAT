# SEHAT Platform — Production Deployment Guide

This guide details the steps required to deploy the complete SEHAT healthcare platform (FastAPI backend + React frontend + PostgreSQL database + Supabase authentication + Twilio WhatsApp webhook) into production.

---

## 1. Database (PostgreSQL)

The database schema utilizes standard async PostgreSQL database pools via SQLAlchemy.

1. **Option A: Managed Database (Recommended)**
   - Provision a PostgreSQL database on a managed service provider (e.g. Supabase, Render PostgreSQL, AWS RDS, Neon).
   - Retrieve the connection string. Translate it from `postgres://` to `postgresql://` so that the backend correctly rewrites it to `postgresql+asyncpg://` on startup.

2. **Option B: Docker Compose Run**
   - Run the unified database, backend, and frontend containers locally or on a virtual private server (VPS) using:
     ```bash
     docker-compose up -d --build
     ```

---

## 2. Authentication (Supabase Setup)

The API is fully integrated with Supabase JWT authentication. Follow these steps to configure access:

1. **Create Supabase Project**
   - Go to [Supabase Console](https://supabase.com) and create a new project.
2. **Retrieve API Credentials**
   - Navigate to **Project Settings -> API**.
   - Copy the **Project URL** (`SUPABASE_URL`) and the **Anon Public Key** (`SUPABASE_ANON_KEY`).
3. **Configure User Metadata / Roles**
   - When a coordinator (doctor, chemist, or blood bank manager) registers or signs up in Supabase, make sure they have a `role` metadata property set (e.g. `role: "doctor"`, `role: "chemist"`, `role: "blood_bank"`, or `role: "admin"`).
   - This metadata payload determines dashboard authorization inside the FastAPI middleware guards.

---

## 3. Backend Deployment (Render / VPS)

The FastAPI server is containerized and ready to deploy.

1. **Deploy to Render (Web Service)**
   - Connect your GitHub repository to Render.
   - Select **Web Service** and choose **Docker** as the runtime environment.
   - Render will automatically locate `backend/Dockerfile` if you configure the **Docker Path** to `./backend/Dockerfile` and set the **Build Context** to `./backend`.
   - Add the following **Environment Variables** in the Render settings:
     ```env
     ENVIRONMENT=production
     DATABASE_URL=postgresql://<user>:<password>@<host>:<port>/<dbname>
     SUPABASE_URL=https://<your-project-id>.supabase.co
     SUPABASE_ANON_KEY=<your-anon-key>
     GEMINI_API_KEY=<your-gemini-vision-key>
     ULTRAMSG_INSTANCE_ID=<your-instance-id>
     ULTRAMSG_TOKEN=<your-ultramsg-token>
     DEFAULT_SEARCH_RADIUS_KM=5
     MAX_SEARCH_RADIUS_KM=25
     ```

2. **Database Schema Creation on Startup**
   - The FastAPI startup context loop `backend/main.py:lifespan` automatically triggers:
     ```python
     async with engine.begin() as conn:
         await conn.run_sync(Base.metadata.create_all)
     ```
   - This ensures all tables (including `blood_banks`, `blood_stock`, `patients`, and `whatsapp_message_logs`) are automatically created on first deployment.

---

## 4. UltraMsg WhatsApp Webhook Configuration

1. **Expose Server URL**
   - Retrieve the public URL of your deployed backend service (e.g., `https://sehat-backend.onrender.com`).
2. **Bind Webhook in UltraMsg Console**
   - Go to your **UltraMsg Dashboard** -> **Instance Settings**.
   - Enable **Webhook on Received Message** (`ON`).
   - Set the webhook URL to:
     ```
     https://sehat-backend.onrender.com/ultramsg
     ```
   - Set HTTP Method to **POST**.
   - Ensure **Webhook Download Media** is enabled (`ON`) so prescription photos are retrieved seamlessly.

---

## 5. Frontend Deployment (Vercel / Netlify)

1. **Deploy to Vercel**
   - Import the `frontend/` directory of your repository.
   - Choose **Vite** as the framework preset.
   - Set the **Root Directory** configuration to `frontend`.
   - Add the following **Environment Variable**:
     ```env
     VITE_API_URL=https://sehat-backend.onrender.com
     ```
   - Deploy. Nginx is not required on Vercel as it serves static builds natively. If hosting on a custom Linux server inside a Docker container, the provided `frontend/Dockerfile` uses Nginx to serve assets and fallbacks correctly.

---

## 6. Administrative Seed Commands

To load baseline medicines and initial clinic/pharmacy profiles:

1. Access the running backend shell.
2. Run:
   ```bash
   python -m backend.seed_dev
   ```
   *(This creates the default Admin: `admin@sehat.in` / `sehat2026`, and seeds Ghaziabad testing clinics).*
