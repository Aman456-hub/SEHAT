import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

os.makedirs("report_assets", exist_ok=True)

def create_er_diagram():
    fig, ax = plt.subplots(figsize=(14, 10), dpi=300)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Title
    ax.text(7, 9.6, "Entity-Relationship (ER) Diagram — S.E.H.A.T Platform", 
            ha='center', va='center', fontsize=16, fontweight='bold', color='#1B365D')

    entities = [
        {"name": "DOCTORS", "x": 0.8, "y": 6.8, "w": 2.8, "h": 2.2, 
         "attrs": ["id (PK)", "name", "phone", "clinic_name", "specialization", "latitude, longitude", "is_available", "avg_consultation_minutes"]},
        {"name": "QUEUE_TOKENS", "x": 4.8, "y": 6.8, "w": 3.0, "h": 2.2, 
         "attrs": ["id (PK)", "doctor_id (FK)", "patient_phone", "patient_name", "token_number", "position", "status", "estimated_wait_minutes", "booked_at, called_at, seen_at"]},
        {"name": "PATIENTS", "x": 9.2, "y": 6.8, "w": 2.8, "h": 2.2, 
         "attrs": ["id (PK)", "phone (Unique)", "name", "language", "latitude, longitude", "created_at"]},
        
        {"name": "CHEMISTS", "x": 0.8, "y": 2.2, "w": 2.8, "h": 2.0, 
         "attrs": ["id (PK)", "name, phone", "shop_name", "address", "latitude, longitude", "is_open"]},
        {"name": "CHEMIST_STOCK", "x": 4.8, "y": 2.2, "w": 2.8, "h": 2.0, 
         "attrs": ["id (PK)", "chemist_id (FK)", "medicine_id (FK)", "is_available", "last_updated"]},
        {"name": "MEDICINES", "x": 8.8, "y": 2.2, "w": 2.8, "h": 2.0, 
         "attrs": ["id (PK)", "generic_name", "brand_names (JSON)", "category", "schedule", "standard_dosages (JSON)"]},
        
        {"name": "PRESCRIPTION_LOGS", "x": 0.8, "y": 0.2, "w": 3.4, "h": 1.5, 
         "attrs": ["id (PK)", "patient_phone", "image_url", "extracted_medicines (JSON)", "matched_chemist_id (FK)", "hindi_explanation", "ocr_confidence"]},
        {"name": "BLOOD_BANKS", "x": 5.2, "y": 0.2, "w": 2.8, "h": 1.5, 
         "attrs": ["id (PK)", "name, phone, address", "latitude, longitude", "is_open_24hrs"]},
        {"name": "BLOOD_STOCKS", "x": 9.2, "y": 0.2, "w": 2.8, "h": 1.5, 
         "attrs": ["id (PK)", "blood_bank_id (FK)", "blood_group", "units_available", "last_updated"]}
    ]

    for ent in entities:
        # Box
        rect = patches.FancyBboxPatch((ent["x"], ent["y"]), ent["w"], ent["h"],
                                      boxstyle="round,pad=0.08", ec="#2B6CB0", fc="#EBF8FF", lw=1.5)
        ax.add_patch(rect)
        # Header Box
        hdr = patches.FancyBboxPatch((ent["x"], ent["y"] + ent["h"] - 0.4), ent["w"], 0.4,
                                     boxstyle="round,pad=0.04", ec="#2B6CB0", fc="#2B6CB0", lw=1.5)
        ax.add_patch(hdr)
        ax.text(ent["x"] + ent["w"]/2, ent["y"] + ent["h"] - 0.2, ent["name"],
                ha='center', va='center', fontsize=9.5, fontweight='bold', color='white')
        
        # Attributes
        txt = "\n".join(["• " + a for a in ent["attrs"]])
        ax.text(ent["x"] + 0.12, ent["y"] + ent["h"] - 0.5, txt,
                ha='left', va='top', fontsize=7.2, color='#2D3748', linespacing=1.2)

    # Relationship connectors
    def draw_arrow(x1, y1, x2, y2, label=""):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", color="#3182CE", lw=1.5))
        if label:
            mx, my = (x1 + x2)/2, (y1 + y2)/2
            ax.text(mx, my + 0.12, label, fontsize=7.5, ha='center', va='center', 
                    bbox=dict(boxstyle="square,pad=0.1", fc="white", ec="none", alpha=0.8), color="#2C5282", fontweight='bold')

    draw_arrow(3.6, 7.9, 4.8, 7.9, "1 : N (Generates)")
    draw_arrow(9.2, 7.9, 7.8, 7.9, "1 : N (Books)")
    draw_arrow(3.6, 3.2, 4.8, 3.2, "1 : N (Holds)")
    draw_arrow(8.8, 3.2, 7.6, 3.2, "1 : N (Cataloged)")
    draw_arrow(8.0, 0.95, 9.2, 0.95, "1 : N (Inventories)")
    draw_arrow(2.2, 2.2, 2.2, 1.7, "1 : N (Dispenses)")

    plt.tight_layout()
    plt.savefig("report_assets/er_diagram.png", bbox_inches='tight')
    plt.close()
    print("ER Diagram generated successfully.")

def create_dfd_level_0():
    fig, ax = plt.subplots(figsize=(12, 6), dpi=300)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6)
    ax.axis('off')
    
    ax.text(6, 5.6, "Data Flow Diagram (DFD) — Level 0 (Context Level Diagram)", 
            ha='center', va='center', fontsize=14, fontweight='bold', color='#1B365D')

    # Central Process
    circ = patches.Circle((6, 2.8), 1.25, ec="#2B6CB0", fc="#BEE3F8", lw=2)
    ax.add_patch(circ)
    ax.text(6, 3.0, "0.0\nS.E.H.A.T\nHEALTHCARE\nPLATFORM", ha='center', va='center', 
            fontsize=10.5, fontweight='bold', color='#1A365D')

    # Entities
    entities = [
        {"name": "PATIENT\n(WhatsApp User)", "x": 0.6, "y": 2.2, "w": 2.0, "h": 1.2},
        {"name": "DOCTOR\n(Web Portal)", "x": 4.8, "y": 4.5, "w": 2.4, "h": 0.9},
        {"name": "CHEMIST\n(Web Portal)", "x": 9.4, "y": 2.2, "w": 2.0, "h": 1.2},
        {"name": "BLOOD BANK\n(Web Portal)", "x": 4.8, "y": 0.3, "w": 2.4, "h": 0.9}
    ]

    for e in entities:
        rect = patches.FancyBboxPatch((e["x"], e["y"]), e["w"], e["h"],
                                      boxstyle="round,pad=0.08", ec="#2D3748", fc="#EDF2F7", lw=1.5)
        ax.add_patch(rect)
        ax.text(e["x"] + e["w"]/2, e["y"] + e["h"]/2, e["name"],
                ha='center', va='center', fontsize=8.5, fontweight='bold', color='#2D3748')

    # Flows
    ax.annotate('GPS Pin / Rx Photo / Token Request', xy=(4.75, 3.2), xytext=(2.6, 3.2),
                arrowprops=dict(arrowstyle="->", color="#3182CE", lw=1.3), fontsize=7)
    ax.annotate('Queue Token / Stock Alert / Hindi Rx', xy=(2.6, 2.5), xytext=(4.75, 2.5),
                arrowprops=dict(arrowstyle="->", color="#38A169", lw=1.3), fontsize=7)

    ax.annotate('Consultation / Call Next / Seen', xy=(6.0, 4.05), xytext=(6.0, 4.5),
                arrowprops=dict(arrowstyle="->", color="#3182CE", lw=1.3), fontsize=7, ha='center')
    ax.annotate('Live Queue Tokens & Status', xy=(6.0, 4.5), xytext=(6.0, 4.05),
                arrowprops=dict(arrowstyle="->", color="#38A169", lw=1.3), fontsize=7, ha='center')

    ax.annotate('Stock Updates & Availability', xy=(7.25, 3.1), xytext=(9.4, 3.1),
                arrowprops=dict(arrowstyle="->", color="#3182CE", lw=1.3), fontsize=7)
    ax.annotate('Prescription Match Inquiries', xy=(9.4, 2.5), xytext=(7.25, 2.5),
                arrowprops=dict(arrowstyle="->", color="#38A169", lw=1.3), fontsize=7)

    ax.annotate('Blood Units Available', xy=(6.0, 1.55), xytext=(6.0, 1.2),
                arrowprops=dict(arrowstyle="->", color="#3182CE", lw=1.3), fontsize=7, ha='center')

    plt.tight_layout()
    plt.savefig("report_assets/dfd_level_0.png", bbox_inches='tight')
    plt.close()
    print("DFD Level 0 generated.")

def create_dfd_level_1():
    fig, ax = plt.subplots(figsize=(13, 8), dpi=300)
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 8)
    ax.axis('off')
    
    ax.text(6.5, 7.6, "Data Flow Diagram (DFD) — Level 1 (Process Decomposition)", 
            ha='center', va='center', fontsize=14, fontweight='bold', color='#1B365D')

    procs = [
        {"num": "1.0", "title": "WhatsApp Dialog\n& Ingestion Engine", "x": 1.0, "y": 4.5},
        {"num": "2.0", "title": "Doctor Queue\nManagement Service", "x": 5.0, "y": 5.2},
        {"num": "3.0", "title": "Gemini AI Vision\nOCR & Translation", "x": 5.0, "y": 3.2},
        {"num": "4.0", "title": "Pharmacy Stock &\nCombination Matcher", "x": 9.0, "y": 3.2},
        {"num": "5.0", "title": "Emergency Blood\nBank Locator", "x": 5.0, "y": 1.2}
    ]

    for p in procs:
        circ = patches.Circle((p["x"] + 1.1, p["y"] + 0.6), 0.9, ec="#2B6CB0", fc="#EBF8FF", lw=1.5)
        ax.add_patch(circ)
        ax.text(p["x"] + 1.1, p["y"] + 0.9, p["num"], ha='center', va='center', fontsize=8, fontweight='bold', color='#2B6CB0')
        ax.text(p["x"] + 1.1, p["y"] + 0.45, p["title"], ha='center', va='center', fontsize=7.5, fontweight='bold', color='#1A365D')

    # Data Stores
    stores = [
        {"name": "D1: Doctors & Queues", "x": 8.8, "y": 6.2, "w": 3.2, "h": 0.6},
        {"name": "D2: Prescription Logs", "x": 1.0, "y": 2.2, "w": 3.0, "h": 0.6},
        {"name": "D3: Medicine Inventory", "x": 8.8, "y": 1.8, "w": 3.2, "h": 0.6},
        {"name": "D4: Blood Stock Store", "x": 8.8, "y": 0.6, "w": 3.2, "h": 0.6}
    ]

    for s in stores:
        ax.plot([s["x"], s["x"] + s["w"]], [s["y"] + s["h"], s["y"] + s["h"]], color="#4A5568", lw=1.5)
        ax.plot([s["x"], s["x"] + s["w"]], [s["y"], s["y"]], color="#4A5568", lw=1.5)
        ax.text(s["x"] + s["w"]/2, s["y"] + s["h"]/2, s["name"], ha='center', va='center', fontsize=8, fontweight='bold', color="#2D3748")

    # Connectors
    ax.annotate('Doctor Search / Booking', xy=(5.0, 5.8), xytext=(2.9, 5.4),
                arrowprops=dict(arrowstyle="->", color="#3182CE", lw=1.2), fontsize=6.8)
    ax.annotate('Prescription Photo', xy=(5.0, 3.8), xytext=(2.8, 4.6),
                arrowprops=dict(arrowstyle="->", color="#3182CE", lw=1.2), fontsize=6.8)
    ax.annotate('Blood Search (e.g. O+)', xy=(5.0, 1.8), xytext=(2.6, 4.3),
                arrowprops=dict(arrowstyle="->", color="#3182CE", lw=1.2), fontsize=6.8)

    ax.annotate('Token Alloc / Reorder', xy=(8.8, 6.4), xytext=(6.9, 6.0),
                arrowprops=dict(arrowstyle="<->", color="#38A169", lw=1.2), fontsize=6.8)
    ax.annotate('Extracted Drug List', xy=(8.8, 3.8), xytext=(7.0, 3.8),
                arrowprops=dict(arrowstyle="->", color="#3182CE", lw=1.2), fontsize=6.8)
    ax.annotate('Match & Distance Query', xy=(10.0, 2.5), xytext=(10.0, 3.0),
                arrowprops=dict(arrowstyle="<->", color="#38A169", lw=1.2), fontsize=6.8)
    ax.annotate('Stock Query (Haversine)', xy=(8.8, 1.0), xytext=(7.0, 1.6),
                arrowprops=dict(arrowstyle="<->", color="#38A169", lw=1.2), fontsize=6.8)

    plt.tight_layout()
    plt.savefig("report_assets/dfd_level_1.png", bbox_inches='tight')
    plt.close()
    print("DFD Level 1 generated.")

def create_dfd_level_2():
    fig, ax = plt.subplots(figsize=(13, 8), dpi=300)
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 8)
    ax.axis('off')
    
    ax.text(6.5, 7.6, "Data Flow Diagram (DFD) — Level 2 (Prescription & Queue Processing)", 
            ha='center', va='center', fontsize=14, fontweight='bold', color='#1B365D')

    procs = [
        {"num": "3.1", "title": "Image Receive &\nFormat Check", "x": 0.8, "y": 4.8},
        {"num": "3.2", "title": "Gemini Vision OCR\nJSON Extraction", "x": 3.8, "y": 4.8},
        {"num": "3.3", "title": "Confidence Check\n(Threshold >= 60%)", "x": 6.8, "y": 4.8},
        {"num": "3.4", "title": "Token Normalizer\n& DB Matcher", "x": 9.8, "y": 4.8},
        
        {"num": "2.1", "title": "Queue Pos Counter\n& ETA Estimator", "x": 2.0, "y": 1.6},
        {"num": "2.2", "title": "Token Creation &\nConfirm Dispatch", "x": 5.5, "y": 1.6},
        {"num": "2.3", "title": "Dynamic State Machine\n(#2 & #1 Shift Alerts)", "x": 9.0, "y": 1.6}
    ]

    for p in procs:
        rect = patches.FancyBboxPatch((p["x"], p["y"]), 2.4, 1.4,
                                      boxstyle="round,pad=0.08", ec="#2B6CB0", fc="#EBF8FF", lw=1.3)
        ax.add_patch(rect)
        ax.text(p["x"] + 1.2, p["y"] + 1.1, p["num"], ha='center', va='center', fontsize=8, fontweight='bold', color='#2B6CB0')
        ax.text(p["x"] + 1.2, p["y"] + 0.65, p["title"], ha='center', va='center', fontsize=7.2, fontweight='bold', color='#1A365D')

    # Connections in flow 3
    ax.annotate('', xy=(3.8, 5.5), xytext=(3.2, 5.5), arrowprops=dict(arrowstyle="->", color="#3182CE", lw=1.3))
    ax.annotate('', xy=(6.8, 5.5), xytext=(6.2, 5.5), arrowprops=dict(arrowstyle="->", color="#3182CE", lw=1.3))
    ax.annotate('', xy=(9.8, 5.5), xytext=(9.2, 5.5), arrowprops=dict(arrowstyle="->", color="#38A169", lw=1.3))
    ax.text(8.0, 5.7, "Valid (>=60%)", fontsize=6.8, color="#276749", ha='center', fontweight='bold')
    
    # Rejection flow
    ax.annotate('Reject & Reprompt', xy=(1.5, 4.8), xytext=(8.0, 4.4),
                arrowprops=dict(arrowstyle="->", color="#E53E3E", lw=1.2, connectionstyle="arc3,rad=-0.2"), fontsize=6.8, color="#C53030")

    # Connections in flow 2
    ax.annotate('', xy=(5.5, 2.3), xytext=(4.4, 2.3), arrowprops=dict(arrowstyle="->", color="#3182CE", lw=1.3))
    ax.annotate('', xy=(9.0, 2.3), xytext=(7.9, 2.3), arrowprops=dict(arrowstyle="->", color="#3182CE", lw=1.3))

    ax.text(6.5, 3.8, "FLOW A: AI Prescription OCR Pipeline (Top) | FLOW B: Dynamic Queue Engine (Bottom)",
            ha='center', va='center', fontsize=9, fontweight='bold', color='#4A5568',
            bbox=dict(boxstyle="round,pad=0.3", fc="#EDF2F7", ec="#CBD5E0"))

    plt.tight_layout()
    plt.savefig("report_assets/dfd_level_2.png", bbox_inches='tight')
    plt.close()
    print("DFD Level 2 generated.")

if __name__ == "__main__":
    create_er_diagram()
    create_dfd_level_0()
    create_dfd_level_1()
    create_dfd_level_2()
    print("All diagrams generated successfully!")
