import os
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'''
        <w:tcMar {nsdecls("w")}>
            <w:top w:w="{top}" w:type="dxa"/>
            <w:bottom w:w="{bottom}" w:type="dxa"/>
            <w:left w:w="{left}" w:type="dxa"/>
            <w:right w:w="{right}" w:type="dxa"/>
        </w:tcMar>
    ''')
    tcPr.append(tcMar)

def create_report():
    doc = Document()
    
    # Page setup - 1 inch margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # Base styles
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Calibri'
    normal_style.font.size = Pt(11)
    normal_style.font.color.rgb = RGBColor(0x2D, 0x37, 0x48)
    normal_style.paragraph_format.line_spacing = 1.15
    normal_style.paragraph_format.space_after = Pt(6)

    # Helper functions for formatted text
    def add_title(text, level=1):
        p = doc.add_paragraph()
        run = p.add_run(text)
        run.bold = True
        p.paragraph_format.keep_with_next = True
        if level == 1:
            run.font.size = Pt(18)
            run.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D) # Deep Navy
            p.paragraph_format.space_before = Pt(16)
            p.paragraph_format.space_after = Pt(8)
        elif level == 2:
            run.font.size = Pt(14)
            run.font.color.rgb = RGBColor(0x2B, 0x6C, 0xB0) # Blue
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(6)
        elif level == 3:
            run.font.size = Pt(12)
            run.font.color.rgb = RGBColor(0x2D, 0x37, 0x48)
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(4)
        return p

    def add_p(text):
        return doc.add_paragraph(text)

    def add_callout(text, title="NOTE"):
        tbl = doc.add_table(rows=1, cols=1)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        cell = tbl.cell(0, 0)
        cell.width = Inches(6.5)
        set_cell_background(cell, "F0F4F8")
        set_cell_margins(cell, top=120, bottom=120, left=180, right=180)
        p = cell.paragraphs[0]
        r_title = p.add_run(f"📌 {title}: ")
        r_title.bold = True
        r_title.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)
        r_text = p.add_run(text)
        r_text.font.size = Pt(10)
        p.paragraph_format.space_after = Pt(0)
        doc.add_paragraph()

    # ==================== COVER / TITLE PAGE ====================
    p_inst = doc.add_paragraph()
    p_inst.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_inst = p_inst.add_run("DEPARTMENT OF COMPUTER SCIENCE\nCHRIST (DEEMED TO BE UNIVERSITY), DELHI NCR")
    r_inst.font.size = Pt(12)
    r_inst.bold = True
    r_inst.font.color.rgb = RGBColor(0x4A, 0x55, 0x68)

    p_sp = doc.add_paragraph()
    p_sp.paragraph_format.space_before = Pt(36)
    p_sp.paragraph_format.space_after = Pt(12)
    p_sp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_sp = p_sp.add_run("SPECIALIZATION PROJECT FINAL REPORT")
    r_sp.font.size = Pt(22)
    r_sp.bold = True
    r_sp.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)

    p_proj = doc.add_paragraph()
    p_proj.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_proj = p_proj.add_run("S.E.H.A.T: Smart Emergency Healthcare Assistance & Triage Platform")
    r_proj.font.size = Pt(16)
    r_proj.bold = True
    r_proj.font.color.rgb = RGBColor(0x2B, 0x6C, 0xB0)

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_sub = p_sub.add_run("A Low-Literacy WhatsApp Healthcare Interface with AI Prescription OCR, Localized Pharmacy Matching, and Proximity Clinic Triage")
    r_sub.font.size = Pt(12)
    r_sub.italic = True
    r_sub.font.color.rgb = RGBColor(0x71, 0x80, 0x96)

    p_det = doc.add_paragraph()
    p_det.paragraph_format.space_before = Pt(80)
    p_det.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_det = p_det.add_run("Submitted in partial fulfillment of the requirements for the degree of\nMaster of Science in Computer Science / Artificial Intelligence\n\nAcademic Session: 2025 – 2026")
    r_det.font.size = Pt(11)
    r_det.font.color.rgb = RGBColor(0x4A, 0x55, 0x68)

    doc.add_page_break()

    # ==================== TABLE OF CONTENTS (IMAGE TEMPLATE FORMAT) ====================
    add_title("Specialization Project Final Report", level=1)
    add_p("Below is the structured content matrix and chapter division conforming strictly to the prescribed institutional project report format:")

    toc_table = doc.add_table(rows=1, cols=3)
    toc_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr_cells = toc_table.rows[0].cells
    hdr_cells[0].text = "Sr. No."
    hdr_cells[1].text = "Sub No."
    hdr_cells[2].text = "Content"
    
    col_widths = [Inches(1.0), Inches(1.0), Inches(4.5)]
    for row in toc_table.rows:
        for i, w in enumerate(col_widths):
            row.cells[i].width = w

    for cell in hdr_cells:
        set_cell_background(cell, "1B365D")
        for p in cell.paragraphs:
            for r in p.runs:
                r.bold = True
                r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    toc_data = [
        ("1.", "", "Introduction"),
        ("", "1.1", "Introduction and Final Title"),
        ("", "1.2", "Problem Statement"),
        ("2.", "", "Feasibility study"),
        ("", "2.1", "Purpose"),
        ("", "2.2", "Current Scope"),
        ("3.", "", "Software Specific Requirements"),
        ("", "3.1", "Specific Requirements"),
        ("", "3.1.1", "Frontend"),
        ("", "3.1.2", "Backend"),
        ("", "3.1.3", "Database"),
        ("4.", "", "Design"),
        ("", "4.1", "ER-Diagram"),
        ("", "4.2", "Data flow diagram (DFD 0 Level, 1- Level and 2 Level)"),
        ("5.", "", "Number of Modules, Detail of Modules"),
        ("6.", "", "Tables"),
        ("7.", "", "Coding"),
        ("", "7.1", "GUI"),
        ("", "7.2", "Backend"),
        ("8.", "", "Result Interpretations and Output Screenshots"),
        ("9.", "", "Future Scope"),
        ("10.", "", "References"),
    ]

    for sr, sub, content in toc_data:
        row = toc_table.add_row()
        for i, w in enumerate(col_widths):
            row.cells[i].width = w
        row.cells[0].text = sr
        row.cells[1].text = sub
        row.cells[2].text = content
        
        # Style row
        if sr != "" and sub == "":
            set_cell_background(row.cells[0], "EDF2F7")
            set_cell_background(row.cells[1], "EDF2F7")
            set_cell_background(row.cells[2], "EDF2F7")
            for cell in row.cells:
                for p in cell.paragraphs:
                    for r in p.runs:
                        r.bold = True
                        r.font.color.rgb = RGBColor(0x1A, 0x36, 0x5D)

    doc.add_page_break()

    # ==================== CHAPTER 1: INTRODUCTION ====================
    add_title("1. Introduction", level=1)
    
    add_title("1.1 Introduction and Final Title", level=2)
    add_p(
        "The project title is: S.E.H.A.T — Smart Emergency Healthcare Assistance & Triage Platform (Low-Literacy WhatsApp Healthcare Interface with AI Prescription OCR & Geolocation Coordination). "
        "Healthcare accessibility across tier-2, tier-3, and rural sectors in developing nations like India remains deeply fragmented. While sophisticated telemedicine applications exist, they mandate high digital literacy, continuous smartphone storage, English proficiency, and high-speed broadband connectivity. "
        "As a result, marginalized demographics experience critical healthcare friction—ranging from crowded outpatient department (OPD) queues and rampant medication non-adherence to critical delays in locating emergency blood reserves."
    )
    add_p(
        "S.E.H.A.T addresses this systemic gap by transforming WhatsApp—a ubiquitous, zero-friction communication channel already familiar to over 500 million citizens—into an intelligent healthcare bridge. "
        "Patients interact with the platform naturally by sending messages, voice notes, location pins, or photographs of doctor prescriptions. Behind this conversational layer sits a robust event-driven backend combining Google Gemini Vision OCR, geospatial proximity algorithms, dynamic queue state machines, and real-time chemist inventory synchronization."
    )

    add_title("1.2 Problem Statement", level=2)
    add_p(
        "Modern primary healthcare in developing economies faces four intertwined crises:\n"
        "1. Disorganized Clinic Queues & Overcrowding: Patients travel tens of kilometers only to wait 3 to 5 hours in physical waiting halls without knowing doctor availability, resulting in lost daily wages and infection cross-contamination.\n"
        "2. Prescription Illiteracy & Medication Non-Adherence: Over 65% of handwritten medical prescriptions in rural and suburban clinics are illegible to patients. Patients cannot understand dosages, frequencies, and special warnings, resulting in medication errors or complete default.\n"
        "3. Fragmented Pharmacy Inventories: Patients waste precious recovery time hopping from chemist to chemist in search of prescribed medications. No unified mechanism exists to match a multi-drug prescription against local pharmacies with verified stock levels.\n"
        "4. Critical Delays in Emergency Blood Availability: In obstetric emergencies and trauma cases, families must physically contact disparate blood banks to discover stock for specific blood groups, incurring fatal logistical delays.\n"
        "5. The 'App Fatigue' and Digital Literacy Barrier: Standalone mobile health apps suffer from abandonment rates exceeding 80% due to complex sign-ups, device memory constraints, and unfamiliar interfaces."
    )
    add_callout(
        "S.E.H.A.T establishes a 100% app-less healthcare paradigm: patients interact solely through their native WhatsApp account in English or Hindi, backed by web portals for healthcare professionals.",
        title="Core Engineering Objective"
    )

    # ==================== CHAPTER 2: FEASIBILITY STUDY ====================
    add_title("2. Feasibility study", level=1)
    
    add_title("2.1 Purpose", level=2)
    add_p(
        "The purpose of this feasibility investigation is to evaluate the technical, operational, and economic viability of deploying an intelligent conversational triage layer over existing telecommunication and healthcare infrastructures."
    )
    add_p(
        "• Technical Feasibility: The system leverages established, production-grade open standards: FastAPI (asynchronous Python 3.11+ web framework) delivering high concurrent throughput, Google Gemini Vision 3.6 Flash providing multimodal OCR with sub-second inference, SQLite/PostgreSQL for persistent data integrity, and the UltraMsg REST gateway for WhatsApp webhook routing without proprietary vendor lock-in.\n"
        "• Operational Feasibility: End-users require zero new software installations or onboarding tutorials. A user who can send a photo or location pin on WhatsApp can operate the platform immediately. Healthcare workers (doctors, chemists, blood bank operators) are provided with lightweight, responsive React web portals requiring minimal training.\n"
        "• Economic Feasibility: Operating on top of WhatsApp eliminates expensive mobile application distribution, Play Store fees, and multi-platform native UI maintenance. Server compute footprint is minimized via asynchronous non-blocking event loops, making local or low-tier cloud deployment affordable for civic hospitals and district authorities."
    )

    add_title("2.2 Current Scope", level=2)
    add_p(
        "The current production scope of S.E.H.A.T incorporates three end-to-end interactive workflows and four professional management dashboards:\n"
        "1. FLOW 1 (Clinic Discovery & Live Queue Triage): Geolocation-driven doctor listing via Haversine distance calculations, daily token sequence allocation, live queue status polling, automated position progression notifications (#2 and #1 in line alerts), and doctor emergency offline broadcasts.\n"
        "2. FLOW 2 (AI Prescription Parsing & Pharmacy Matching): Direct photo parsing via Gemini Vision OCR, CDSCO catalog bidirectional fuzzy token matching, single-chemist match vs. optimal 2-chemist combination fallback, stock staleness auditing (>24 hours), and plain Hindi conversational dosage instructions.\n"
        "3. FLOW 3 (Emergency Blood Bank Proximity Engine): Real-time blood group search supporting English and Hindi variants (e.g., 'KHOON O+'), proximity matching (2km to 5km radius), emergency closest-fallback override regardless of distance, zero-stock filtering, and 12-hour inventory freshness checks.\n"
        "4. Management Portals: Dedicated responsive web interfaces for Doctors (queue controller), Chemists (inventory catalog editor), Blood Banks (blood units grid), and Administrators (system analytics and audit logs)."
    )

    # ==================== CHAPTER 3: SOFTWARE SPECIFIC REQUIREMENTS ====================
    add_title("3. Software Specific Requirements", level=1)
    
    add_title("3.1 Specific Requirements", level=2)
    add_p(
        "The system architecture is bifurcated into a decoupled client-server model: the patient conversational client (WhatsApp), the administrative web clients (React SPA), and the core orchestration backend (FastAPI)."
    )

    add_title("3.1.1 Frontend", level=3)
    add_p(
        "• Framework & Core: React 18+ with Vite tooling for rapid Hot Module Replacement (HMR) and optimized ES bundle distribution.\n"
        "• Styling & Design System: Vanilla CSS3 design system with custom CSS custom properties (tokens) ensuring high performance, zero runtime overhead, responsive flexbox/grid layouts, and sleek healthcare color palettes.\n"
        "• State Management & Network: Modular React custom hooks (`useQueue`, `useAuth`, `useChemist`) with Axios interceptors managing JWT bearer tokens and automatic authorization redirects.\n"
        "• Component Structure: Role-gated single-page application rendering distinct views based on authenticated credentials (`DoctorDashboard`, `ChemistDashboard`, `BloodBankDashboard`, `AdminDashboard`, `LoginPage`).\n"
        "• Audio & Real-time Cues: Audio chime synthesis for clinical queue alerts upon token status shifts."
    )

    add_title("3.1.2 Backend", level=3)
    add_p(
        "• Language & Framework: Python 3.11 / 3.12+ running FastAPI and Uvicorn ASGI server with full asynchronous concurrency (`asyncio`).\n"
        "• WhatsApp Messaging Gateway: UltraMsg REST API integration utilizing asynchronous HTTP postbacks for conversational message handling, media downloads, and outbound notifications.\n"
        "• Artificial Intelligence & Vision Engine: Google Generative AI Python SDK (`google-generativeai`) accessing `gemini-3.6-flash` with optimized medical extraction prompts and JSON schema constraints.\n"
        "• Geospatial Computation: Pure mathematical Haversine spherical distance computation algorithms eliminating heavy GIS engine dependencies.\n"
        "• Security & Cryptography: Native `bcrypt` password hashing with salted cost factors, JWT token issuance with expiration controls, and telephone number SHA-256 pseudonymization for patient privacy."
    )

    add_title("3.1.3 Database", level=3)
    add_p(
        "• ORM Layer: SQLAlchemy 2.0 AsyncIO with `Mapped` and `mapped_column` type annotations providing asynchronous transaction safety.\n"
        "• Database Management Systems: Local SQLite with WAL (Write-Ahead Logging) mode for local development and rapid testing; PostgreSQL 15+ for high-concurrency production deployments.\n"
        "• Migration & Seed Integrity: Declarative schema definitions with complete seed datasets (`schema_and_seed.sql` and `backend/seed_dev.py`) covering CDSCO standard medicines, doctors, chemists, and blood reserves."
    )

    # ==================== CHAPTER 4: DESIGN ====================
    add_title("4. Design", level=1)
    
    add_title("4.1 ER-Diagram", level=2)
    add_p(
        "The Entity-Relationship (ER) model organizes S.E.H.A.T into 10 structured relational tables enforcing foreign key constraints, cascading deletions, and uniqueness rules. "
        "Figure 4.1 depicts the database entities, key attributes, and cardinality relationships connecting Doctors, Patients, Queue Tokens, Chemists, Medicines, Chemist Stocks, Blood Banks, and Prescription Logs."
    )
    
    er_img_path = os.path.abspath("report_assets/er_diagram.png")
    if os.path.exists(er_img_path):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.add_picture(er_img_path, width=Inches(6.2))
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r_cap = p_cap.add_run("Figure 4.1: S.E.H.A.T Relational Database Entity-Relationship Diagram")
        r_cap.font.size = Pt(9.5)
        r_cap.italic = True
    else:
        add_p("[ER Diagram Image: report_assets/er_diagram.png]")

    add_p(
        "Key Relational Highlights:\n"
        "• DOCTORS to QUEUE_TOKENS (1 : N): A doctor manages an ordered sequence of queue tokens for each clinical working day.\n"
        "• PATIENTS to QUEUE_TOKENS (1 : N): A patient can book appointments, but active queue constraints enforce a maximum of 1 active token per patient per doctor.\n"
        "• CHEMISTS to CHEMIST_STOCK (1 : N) & MEDICINES to CHEMIST_STOCK (1 : N): Associative entity capturing inventory availability and freshness timestamps for every pharmacy-medicine pair.\n"
        "• BLOOD_BANKS to BLOOD_STOCKS (1 : N): Tracks live unit inventories across 8 standard blood groups with a unique constraint on (blood_bank_id, blood_group)."
    )

    add_title("4.2 Data flow diagram (DFD 0 Level, 1- Level and 2 Level)", level=2)
    add_p(
        "Data Flow Diagrams (DFDs) illustrate the path, transformation, and storage of data as it travels between external entities (Patients, Doctors, Chemists, Blood Banks) and the S.E.H.A.T processing units."
    )

    # DFD Level 0
    add_title("4.2.1 DFD Level 0 (Context Level Diagram)", level=3)
    add_p(
        "The Level 0 Context Diagram represents the entire S.E.H.A.T platform as a single centralized process interacting with four primary external entities. "
        "Figure 4.2 illustrates how user inputs (GPS coordinates, prescription photographs, appointment requests) enter the platform and how formatted healthcare outputs return."
    )
    dfd0_path = os.path.abspath("report_assets/dfd_level_0.png")
    if os.path.exists(dfd0_path):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.add_picture(dfd0_path, width=Inches(5.8))
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r_cap = p_cap.add_run("Figure 4.2: Data Flow Diagram — Level 0 (Context Level)")
        r_cap.font.size = Pt(9.5)
        r_cap.italic = True

    # DFD Level 1
    add_title("4.2.2 DFD Level 1 (Process Decomposition Diagram)", level=3)
    add_p(
        "The Level 1 DFD decomposes the system into its five core operational sub-processes: (1.0) WhatsApp Dialogue & Ingestion Engine, (2.0) Doctor Queue Management Service, (3.0) Gemini AI Vision OCR & Translation Pipeline, (4.0) Pharmacy Stock & Combination Matcher, and (5.0) Emergency Blood Bank Locator. "
        "Figure 4.3 outlines how data transitions between processes and persistent data stores."
    )
    dfd1_path = os.path.abspath("report_assets/dfd_level_1.png")
    if os.path.exists(dfd1_path):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.add_picture(dfd1_path, width=Inches(6.0))
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r_cap = p_cap.add_run("Figure 4.3: Data Flow Diagram — Level 1 (Decomposition)")
        r_cap.font.size = Pt(9.5)
        r_cap.italic = True

    # DFD Level 2
    add_title("4.2.3 DFD Level 2 (Sub-Process Deep Dive)", level=3)
    add_p(
        "The Level 2 DFD details the algorithmic execution inside the two most complex subsystems: the AI Prescription OCR Pipeline (Processes 3.1 to 3.4) and the Dynamic Queue Progression Engine (Processes 2.1 to 2.3). "
        "Figure 4.4 illustrates format verification, confidence threshold enforcement (>=60%), token normalization, and sequential #2/#1 queue shift notifications."
    )
    dfd2_path = os.path.abspath("report_assets/dfd_level_2.png")
    if os.path.exists(dfd2_path):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.add_picture(dfd2_path, width=Inches(6.0))
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r_cap = p_cap.add_run("Figure 4.4: Data Flow Diagram — Level 2 (Prescription & Queue Sub-Processes)")
        r_cap.font.size = Pt(9.5)
        r_cap.italic = True

    # ==================== CHAPTER 5: MODULES ====================
    add_title("5. Number of Modules, Detail of Modules", level=1)
    add_p(
        "S.E.H.A.T is structured into six modular subsystems ensuring strict separation of concerns, high maintainability, and horizontal scalability:"
    )

    modules_info = [
        ("Module 1: Conversational Dialogue & Ingestion Gateway",
         "File: backend/routers/whatsapp.py\n"
         "Responsibilities: Handles incoming UltraMsg webhooks, deduplicates requests, parses multi-lingual messages (English & Devanagari Hindi), caches user GPS locations, enforces hourly rate limits (Rule 13), and formats outbound WhatsApp messages with clickable Google Maps direction links."),
        
        ("Module 2: Dynamic Doctor Queue Controller",
         "File: backend/services/queue_service.py & backend/routers/tokens.py\n"
         "Responsibilities: Manages token generation, daily sequence resets, real-time wait estimation ((position - 1) * avg_time), automated position progression (#2 and #1 in line alerts), alert deduplication tracking, auto-calling next patients upon consultation completion, and bulk cancellation broadcasts upon doctor emergency offline events."),
        
        ("Module 3: AI Prescription OCR Engine",
         "File: backend/services/ocr_service.py\n"
         "Responsibilities: Streams uploaded prescription image bytes to Google Gemini 3.6 Flash, applies strict medical extraction prompts, parses structured JSON outputs (drug name, strength, frequency, duration), and enforces confidence guards (Rule 10) rejecting unreadable images below 60% confidence."),
        
        ("Module 4: Bilingual Plain-Language Translation Explainer",
         "File: backend/services/translation_service.py\n"
         "Responsibilities: Transforms clinical Latin/English dosage jargon (e.g., '1-0-1 p.c.', 'OD', 'TDS') into conversational, low-literacy Hindi instructions organized into clear bullet points: purpose (यह दवाई किसलिए है), timing (कब लेनी है), frequency (दिन में कितनी बार), and key warnings."),
        
        ("Module 5: Pharmacy Proximity & Split-Stock Matcher",
         "File: backend/services/medicine_service.py\n"
         "Responsibilities: Resolves extracted medicine strings against the CDSCO drug catalog using fuzzy bidirectional token matching with length guards, searches pharmacies within an auto-expanding radius (5km to 25km), performs optimal 2-chemist split combination matching when single shops lack full inventory, and flags unverified stocks older than 24 hours."),
        
        ("Module 6: Emergency Blood Bank Discovery Engine",
         "File: backend/services/blood_service.py & backend/routers/blood_banks.py\n"
         "Responsibilities: Normalizes varied blood group queries, calculates proximity using Haversine distance, enforces an emergency nearest-neighbor fallback override when local radius stocks are depleted, filters out zero-inventory listings, and flags stocks unupdated for over 12 hours.")
    ]

    for m_title, m_desc in modules_info:
        add_title(m_title, level=2)
        add_p(m_desc)

    # ==================== CHAPTER 6: TABLES ====================
    add_title("6. Tables", level=1)
    add_p(
        "This section documents the database dictionary, listing all primary tables, attributes, data types, constraints, and operational descriptions:"
    )

    def add_schema_table(table_name, columns):
        add_title(f"Table 6: {table_name}", level=3)
        tbl = doc.add_table(rows=1, cols=4)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        hdr = tbl.rows[0].cells
        hdr[0].text = "Column Name"
        hdr[1].text = "Data Type"
        hdr[2].text = "Constraints"
        hdr[3].text = "Description"
        
        widths = [Inches(1.5), Inches(1.2), Inches(1.5), Inches(2.3)]
        for i, w in enumerate(widths):
            hdr[i].width = w
            set_cell_background(hdr[i], "2B6CB0")
            for p in hdr[i].paragraphs:
                for r in p.runs:
                    r.bold = True
                    r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                    r.font.size = Pt(9.5)

        for col, dtype, constr, desc in columns:
            row = tbl.add_row()
            for i, w in enumerate(widths):
                row.cells[i].width = w
            row.cells[0].text = col
            row.cells[1].text = dtype
            row.cells[2].text = constr
            row.cells[3].text = desc
            for cell in row.cells:
                for p in cell.paragraphs:
                    p.paragraph_format.space_after = Pt(2)
                    for r in p.runs:
                        r.font.size = Pt(8.5)
        doc.add_paragraph()

    add_schema_table("doctors", [
        ("id", "INTEGER", "PK, Auto-inc", "Unique identifier for doctor"),
        ("name", "VARCHAR(100)", "NOT NULL", "Doctor's full name"),
        ("phone", "VARCHAR(20)", "NOT NULL, Unique", "Contact phone number"),
        ("clinic_name", "VARCHAR(150)", "NOT NULL", "Registered clinic/hospital name"),
        ("address", "VARCHAR(255)", "NOT NULL", "Physical street address"),
        ("latitude", "DOUBLE PRECISION", "NOT NULL", "Geographical latitude coordinate"),
        ("longitude", "DOUBLE PRECISION", "NOT NULL", "Geographical longitude coordinate"),
        ("specialization", "VARCHAR(100)", "NOT NULL", "Medical discipline (e.g. General Physician)"),
        ("is_available", "BOOLEAN", "DEFAULT TRUE", "Live operational status (online/offline)"),
        ("avg_consultation_minutes", "INTEGER", "DEFAULT 15", "Average session duration per patient")
    ])

    add_schema_table("queue_tokens", [
        ("id", "INTEGER", "PK, Auto-inc", "Unique queue token record ID"),
        ("doctor_id", "INTEGER", "FK -> doctors.id", "Doctor with whom appointment is booked"),
        ("patient_phone", "VARCHAR(64)", "NOT NULL, Indexed", "SHA-256 hashed/masked patient phone"),
        ("patient_name", "VARCHAR(100)", "NOT NULL", "Patient full name"),
        ("token_number", "INTEGER", "NOT NULL", "Sequential daily token number (e.g. #1, #2)"),
        ("position", "INTEGER", "NOT NULL", "Current live position in queue"),
        ("status", "VARCHAR(20)", "DEFAULT 'waiting'", "Status: waiting, called, seen, cancelled"),
        ("estimated_wait_minutes", "INTEGER", "DEFAULT 0", "Dynamic estimated wait in minutes"),
        ("booked_at", "TIMESTAMP", "DEFAULT NOW()", "Timestamp of booking creation"),
        ("called_at", "TIMESTAMP", "Nullable", "Timestamp when doctor clicked 'Call Patient'"),
        ("seen_at", "TIMESTAMP", "Nullable", "Timestamp when consultation completed")
    ])

    add_schema_table("medicines", [
        ("id", "INTEGER", "PK, Auto-inc", "Unique catalog drug ID"),
        ("generic_name", "VARCHAR(150)", "NOT NULL, Unique", "Standardized generic chemical name"),
        ("brand_names", "JSON / JSONB", "NOT NULL", "List of known commercial brand names"),
        ("category", "VARCHAR(100)", "NOT NULL", "Therapeutic class (e.g., Analgesic, NSAID)"),
        ("schedule", "VARCHAR(20)", "DEFAULT 'H'", "Drug regulatory schedule (OTC, H, H1, X)"),
        ("standard_dosages", "JSON / JSONB", "NOT NULL", "List of standard strengths (e.g. 500mg, 650mg)")
    ])

    add_schema_table("chemists & chemist_stock", [
        ("id", "INTEGER", "PK, Auto-inc", "Chemist ID / Stock ID"),
        ("chemist_id", "INTEGER", "FK -> chemists.id", "Pharmacy shop identifier"),
        ("medicine_id", "INTEGER", "FK -> medicines.id", "Medicine reference"),
        ("is_available", "BOOLEAN", "DEFAULT TRUE", "Stock presence indicator"),
        ("last_updated", "TIMESTAMP", "DEFAULT NOW()", "Timestamp of last stock level verification")
    ])

    add_schema_table("blood_banks & blood_stocks", [
        ("id", "INTEGER", "PK, Auto-inc", "Blood Bank / Blood Stock record ID"),
        ("blood_bank_id", "INTEGER", "FK -> blood_banks.id", "Blood bank facility reference"),
        ("blood_group", "VARCHAR(5)", "NOT NULL", "Standard ABO/Rh group (A+, B+, O-, etc.)"),
        ("units_available", "INTEGER", "DEFAULT 0", "Current live inventory units count"),
        ("last_updated", "TIMESTAMP", "DEFAULT NOW()", "Stock verification timestamp (12h staleness)")
    ])

    # ==================== CHAPTER 7: CODING ====================
    add_title("7. Coding", level=1)
    
    add_title("7.1 GUI (Frontend Implementation)", level=2)
    add_p(
        "The React frontend operates as an event-driven dashboard connecting healthcare providers with their live queue and inventory state machines. "
        "Below are key code implementations from the Doctor Queue Hook (`useQueue.js`) demonstrating live status patches, optimistic UI updates, and chime alerts:"
    )

    code_gui = (
'''// frontend/src/hooks/useQueue.js
// Asynchronous hook managing live doctor queue state machine and audio cues
export const useQueue = (doctorId) => {
  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(true);

  // Play auditory cue on patient call or queue advance
  const playChime = () => {
    try {
      const audio = new Audio('/sounds/chime.mp3');
      audio.play().catch(e => console.log('Audio autoplay prevented'));
    } catch (err) {}
  };

  // Action: Call Next Patient into consultation room
  const callPatient = async (tokenId) => {
    try {
      const res = await api.patch(`/api/tokens/${tokenId}/status`, { status: 'called' });
      if (res.success) {
        playChime();
        setQueue(prev => prev.map(t => (t.id === tokenId ? res.data : t)));
        fetchData(); // Sync live estimations
      }
    } catch (err) {
      console.error('Failed calling patient:', err);
    }
  };

  // Action: Mark consultation as completed (SEEN)
  const seenPatient = async (tokenId) => {
    try {
      const res = await api.patch(`/api/tokens/${tokenId}/status`, { status: 'seen' });
      if (res.success) {
        playChime();
        fetchData(); // Auto-calls next patient & reorders queue
      }
    } catch (err) {
      console.error('Failed marking seen:', err);
    }
  };

  return { queue, loading, callPatient, seenPatient };
};'''
    )
    p_cg = doc.add_paragraph()
    r_cg = p_cg.add_run(code_gui)
    r_cg.font.name = 'Consolas'
    r_cg.font.size = Pt(8.5)
    r_cg.font.color.rgb = RGBColor(0x2D, 0x37, 0x48)
    p_cg.paragraph_format.space_before = Pt(4)
    p_cg.paragraph_format.space_after = Pt(8)

    add_title("7.2 Backend (Core Services Implementation)", level=2)
    add_p(
        "The backend implements rigorous asynchronous pipeline services. Below is the dynamic queue reordering and position progression notification logic from `queue_service.py`, featuring position deduplication tracking:"
    )

    code_backend = (
'''# backend/services/queue_service.py
# In-memory deduplication tracker: token_id -> set of delivered position alerts
TOKEN_NOTIFIED_POSITIONS: Dict[int, Set[int]] = {}

async def reorder_queue_and_notify(db: AsyncSession, doctor_id: int) -> None:
    """
    Recalculates positions and wait times for all active tokens.
    Notifies waiting patients at position 1 (next) and position 2.
    Deduplicates notifications to prevent redundant spam.
    """
    doctor = (await db.execute(select(Doctor).where(Doctor.id == doctor_id))).scalar_one_or_none()
    if not doctor:
        return

    # Fetch active tokens sorted by called status and booked order
    result = await db.execute(
        select(QueueToken)
        .where(and_(QueueToken.doctor_id == doctor_id, QueueToken.status.in_(["waiting", "called"])))
        .order_by(QueueToken.position, QueueToken.booked_at)
    )
    active_tokens = list(result.scalars().all())
    active_tokens.sort(key=lambda t: (0 if t.status == "called" else 1, t.position, t.booked_at))

    for idx, token in enumerate(active_tokens):
        new_position = idx + 1
        token.position = new_position
        token.estimated_wait_minutes = idx * doctor.avg_consultation_minutes
        db.add(token)

        notified_set = TOKEN_NOTIFIED_POSITIONS.setdefault(token.id, set())

        # Notify waiting patients reaching position 1 or 2
        if new_position in (1, 2) and token.status == "waiting":
            if new_position not in notified_set:
                notified_set.add(new_position)
                instruction = (
                    "Please be ready outside the consultation room."
                    if new_position == 1
                    else "Please head to the clinic waiting area now."
                )
                maps_link = f"https://www.google.com/maps/dir/?api=1&destination={doctor.latitude},{doctor.longitude}"
                msg = (
                    f"⏳ *Almost Your Turn!*\\n\\n"
                    f"Dear {token.patient_name}, you are now *#{new_position} in line* for Dr. {doctor.name}.\\n"
                    f"📍 *Clinic:* {doctor.clinic_name}\\n"
                    f"🕒 *Est. Wait:* ~{token.estimated_wait_minutes} mins\\n"
                    f"🗺️ *Directions:* {maps_link}\\n\\n"
                    f"{instruction}"
                )
                await send_whatsapp_notification(token.patient_phone, msg)

    await db.commit()'''
    )
    p_cb = doc.add_paragraph()
    r_cb = p_cb.add_run(code_backend)
    r_cb.font.name = 'Consolas'
    r_cb.font.size = Pt(8.5)
    r_cb.font.color.rgb = RGBColor(0x2D, 0x37, 0x48)
    p_cb.paragraph_format.space_before = Pt(4)
    p_cb.paragraph_format.space_after = Pt(8)

    # ==================== CHAPTER 8: RESULTS ====================
    add_title("8. Result Interpretations and Output Screenshots", level=1)
    add_p(
        "Extensive end-to-end operational testing was conducted using live UltraMsg WhatsApp webhooks and browser dashboard interactions. "
        "The results demonstrate flawless execution across clinic queue booking, multi-item prescription parsing, inventory split matching, and emergency blood bank searches."
    )

    add_title("8.1 WhatsApp Conversational Outputs & Test Runs", level=2)
    add_p(
        "Below are authentic output transcript matrices captured directly from the live WhatsApp conversational interface:"
    )

    def add_transcript_box(title, text):
        tbl = doc.add_table(rows=1, cols=1)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        cell = tbl.cell(0, 0)
        cell.width = Inches(6.5)
        set_cell_background(cell, "F7FAFC")
        set_cell_margins(cell, top=100, bottom=100, left=150, right=150)
        p = cell.paragraphs[0]
        r_t = p.add_run(f"📱 {title}\n")
        r_t.bold = True
        r_t.font.color.rgb = RGBColor(0x2B, 0x6C, 0xB0)
        r_b = p.add_run(text)
        r_b.font.name = 'Consolas'
        r_b.font.size = Pt(8.5)
        doc.add_paragraph()

    add_transcript_box("Test Case 1: Prescription Scan & Proximity Pharmacy Match",
'''*Prescription Scan Complete!* 🔬

📋 *Medicines on Prescription:*
• *FeSO4 tab* (A.D., 30 days (#30))
• *Ascorbic Acid 100mg tab* (Once a day, 30 days (#30))

📍 *Available Nearby:* Mohan Chemists (0.5 km away)
📞 Phone: +918888888888
🗺️ Directions: https://www.google.com/maps/dir/?api=1&destination=28.6625,77.3595

Reply with *EXPLAIN* to receive explanations for these medicines in simple Hindi.''')

    add_transcript_box("Test Case 2: Bilingual Plain Hindi Medical Instructions (EXPLAIN)",
'''पहली दवाई (खून की गोली - FeSO4):
→ यह दवाई किसलिए है: शरीर में खून की कमी पूरी करने और हीमोग्लोबिन बढ़ाने के लिए।
→ कब लेनी है: खाना खाने के बाद लें।
→ दिन में कितनी बार: दिन में एक बार।
→ कितने दिन तक: पूरे 30 दिन तक लेनी है।
→ जरूरी बात: इसे खाने के बाद लैट्रिन का रंग काला हो सकता है, इससे डरें नहीं।

दूसरी दवाई (विटामिन सी की गोली - Ascorbic Acid):
→ यह दवाई किसलिए है: शरीर की रोग प्रतिरोधक क्षमता बढ़ाने और खून सोखने में मदद के लिए।
→ कब लेनी है: खाना खाने के बाद लें।
→ दिन में कितनी बार: दिन में सिर्फ 1 बार।
→ कितने दिन तक: पूरे 30 दिन तक लेनी है।
→ जरूरी बात: इस गोली को आप आराम से चबाकर या चूसकर खा सकते हैं।

⚠️ Disclaimer: This Hindi translation is AI-generated for informational support.''')

    add_transcript_box("Test Case 3: Live Doctor Queue Sequential Progression",
'''[Booking Confirmed - 11:12]
Hello Yashasvi, your booking is confirmed with Dr. Sharma (General Physician).
📍 Clinic: Sharma Health Clinic | 🎫 Token Number: #4
👥 Queue Position: #3 | 🕒 Estimated Wait: ~30 mins

[Queue Shift Alert - 11:15]
⏳ *Almost Your Turn!*
Dear Yashasvi, you are now *#2 in line* for Dr. Sharma.
📍 Clinic: Sharma Health Clinic | 🕒 Est. Wait: ~15 mins
Please head to the clinic waiting area now.

[Queue Shift Alert - 11:28]
⏳ *Almost Your Turn!*
Dear Yashasvi, you are now *#1 in line* for Dr. Sharma.
📍 Clinic: Sharma Health Clinic | 🕒 Est. Wait: ~0 mins
Please be ready outside the consultation room.

[Doctor Calling Alert - 11:30]
🔔 *It's Your Turn!*
Hello Yashasvi, Token #4 is now being called!
Please enter Dr. Sharma's consultation room at Sharma Health Clinic now.''')

    # ==================== CHAPTER 9: FUTURE SCOPE ====================
    add_title("9. Future Scope", level=1)
    add_p(
        "S.E.H.A.T establishes a scalable foundation for expanding digital public health infrastructure. Future development trajectories include:\n"
        "1. Integration with Ayushman Bharat Digital Mission (ABDM): Connecting patient interactions with official Ayushman Bharat Health Account (ABHA) IDs to link WhatsApp consultation receipts and scanned prescriptions directly into national Electronic Health Records (EHR).\n"
        "2. AWS Cloud S3 Prescription Archival: Upgrading temporary local file handling to high-durability AWS S3 buckets with pre-signed ephemeral URLs and server-side AES-256 encryption for regulatory medical compliance.\n"
        "3. Multilingual Voice Audiobot: Integrating open-source speech models (e.g. Bhashini / Whisper) to enable completely illiterate patients to speak and listen via WhatsApp voice notes in Bhojpuri, Maithili, Tamil, and Bengali.\n"
        "4. Chronic Disease Refill Automation: Automated WhatsApp alerts calculating medication depletion dates for hypertension and diabetes patients, suggesting 1-click pharmacy reserve orders before dosages run out.\n"
        "5. Automated Teleconsultation Webrtc Links: Generating secure, zero-download video consultation links inside WhatsApp when doctor clinics are over capacity or patient mobility is restricted."
    )

    # ==================== CHAPTER 10: REFERENCES ====================
    add_title("10. References", level=1)
    references = [
        "1. World Health Organization (WHO), 'Global Strategy on Digital Health 2020–2025', Geneva, Switzerland, 2021.",
        "2. Ministry of Health and Family Welfare (MoHFW), Government of India, 'National Digital Health Blueprint (NDHB)', New Delhi, 2019.",
        "3. Google DeepMind & Google Cloud, 'Gemini Flash: Multimodal Capabilities, Architecture, and Low-Latency Serving', Technical Whitepaper, 2024.",
        "4. Central Drugs Standard Control Organization (CDSCO), 'National List of Essential Medicines (NLEM)', Directorate General of Health Services, New Delhi, India, 2022.",
        "5. Tiangolo, S., 'FastAPI: Modern, Fast (High-Performance), Web Framework for Building APIs with Python 3.8+', https://fastapi.tiangolo.com, 2023.",
        "6. Meta Platforms & UltraMsg, 'WhatsApp Business Platform Messaging Protocols and Webhook Architectural Guidelines', 2024.",
        "7. Sinnott, R. W., 'Virtues of the Haversine', Sky and Telescope, vol. 68, no. 2, p. 159, 1984.",
        "8. National Health Authority (NHA), 'Ayushman Bharat Digital Mission (ABDM) Sandbox & API Specifications', Government of India, 2023."
    ]
    for ref in references:
        p_ref = doc.add_paragraph(ref)
        p_ref.paragraph_format.left_indent = Inches(0.4)
        p_ref.paragraph_format.first_line_indent = Inches(-0.4)
        p_ref.paragraph_format.space_after = Pt(4)

    output_filename = "Specialization_Project_Final_Report_SEHAT.docx"
    doc.save(output_filename)
    print(f"Report saved successfully to {output_filename}")

if __name__ == "__main__":
    create_report()
