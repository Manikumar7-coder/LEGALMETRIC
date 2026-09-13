# SafeMetric – AI Powered Legal Metrology Compliance System

> **Team Name:** SAFE METRIC  
> **Tagline:** Scan. Validate. Trust.  
> **Statutory Basis:** Legal Metrology Act, 2009 & Legal Metrology (Packaged Commodities) Rules, 2011 (G.S.R. 202(E))  
> **Architecture Reference:** See [ARCHITECTURE.md](ARCHITECTURE.md) for full technical design, pipeline diagrams, and statutory matrices.

---

## 1. System Overview

**SafeMetric** is an enterprise-grade AI-powered regulatory compliance system built for enforcement officers, inspectors, and supervisors under the Department of Consumer Affairs. It automates the optical inspection of packaged commodities by capturing or uploading product labels, extracting declarations using OpenCV computer vision and RapidOCR/PaddleOCR, validating declarations against 21 statutory Legal Metrology rules, detecting infractions, generating multi-format export certificates (PDF, DOCX, CSV), and maintaining an auditable inspection history with Role-Based Access Control (RBAC).

### Key Statutory Capabilities (SIH26034 Compliance)
1. **Rule 7 Font Size & Readability Analysis**: Calculates physical character height in millimeters from OCR bounding polygons using either user-calibrated dimensions (confidence: 0.95) or statistical packaging tier heuristics (confidence: 0.60). Audits compliance against Rule 7(1)-(3) Tables I & II (area-dependent minimum character heights).
2. **Rule 8 Declaration Placement & Clear Space**: Evaluates Principal Display Panel (PDP) spatial clustering for core declarations (net quantity, MRP, manufacturer, consumer care, date) and verifies statutory clear space surrounding the net quantity numeral (1x character height vertically, 2x character height horizontally) under Rule 8(1) Proviso.
3. **Multi-Format Statutory Report Exporter**: Produces immutable publication-grade PDF certificates via ReportLab, editable Microsoft Word (`.docx`) statutory inspection notices with officer sign-off blocks via `python-docx`, and flat tabular CSV audit records.
4. **Hierarchical Role-Based Access Control (RBAC)**: Secure access tiering (`Admin` > `Supervisor` > `Inspector`). Enforces department-wide analytics visibility for supervisors/admins, restricts record deletion and user role management to administrators, and scopes field inspectors to their own inspections.

### Core Product Principle & Terminology Mandate
> [!IMPORTANT]
> SafeMetric evaluates **PACKAGED PRODUCT LABEL DECLARATION COMPLIANCE**. It does **NOT** evaluate consumable, physical, or medical safety.
>
> **Standard Statutory Terminology:**
> - `COMPLIANT`
> - `NON-COMPLIANT`
> - `PARTIALLY COMPLIANT`
> - `REVIEW REQUIRED`
> - `MISSING DECLARATION`
> - `INVALID DECLARATION`
> - `LOW OCR CONFIDENCE`
>
> *Prohibited Phrasing:* "Product is safe", "Guaranteed safe". The system provides automated compliance assistance; final regulatory determination remains subject to physical inspection by an authorized officer.

---

## 2. Architecture & Tech Stack

SafeMetric consists of **two unified client applications** powered by a single shared FastAPI backend. Detailed subsystem architecture and data flow diagrams are available in [ARCHITECTURE.md](ARCHITECTURE.md).

```
                  ┌────────────────────────────────────────┐
                  │          WEB APPLICATION               │
                  │   React 18 + Vite + Lucide Icons       │
                  └───────────────────┬────────────────────┘
                                      │
                                      ▼  REST API (JSON)
┌─────────────────────────────────────┴─────────────────────────────────────┐
│                       FASTAPI SHARED BACKEND                              │
│  • Pydantic Schemas  • SQLAlchemy ORM  • SQLite (PostgreSQL Ready)        │
│  • OpenCV Vision Preprocessing (CLAHE, Bilateral Denoising, Otsu)         │
│  • RapidOCR / PaddleOCR Text Engine & Polygon Bounding Box Extractor      │
│  • FontAnalysisEngine (Rule 7 Character Height in mm & Tables I/II)       │
│  • PlacementChecker (Rule 8 PDP Grouping & Net Qty Clear Space Zone)      │
│  • Legal Metrology Compliance Engine (21 Statutory Rules Evaluator)       │
│  • ReportLab PDF + python-docx DOCX + Tabular CSV Exporters               │
│  • Hierarchical RBAC (Admin, Supervisor, Inspector)                       │
└─────────────────────────────────────┬─────────────────────────────────────┘
                                      ▲  REST API (JSON)
                                      │
                  ┌───────────────────┴────────────────────┐
                  │          MOBILE APPLICATION            │
                  │ React Native + Expo (Camera First)     │
                  └────────────────────────────────────────┘
```

---

## 3. Directory Layout

```
safemetric/
├── ARCHITECTURE.md                  # Comprehensive technical & statutory architecture
├── README.md                        # Project overview, quickstart & run guide
│
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app entrypoint, lifespan & static mounts
│   │   ├── database.py              # SQLite / SQLAlchemy connection
│   │   ├── demo_seeder.py           # Pre-seeds rules, demo officers (Admin/Supervisor/Inspector)
│   │   ├── models/                  # User, Inspection, InspectionField, Rule, Report
│   │   ├── schemas/                 # Pydantic validation schemas
│   │   ├── routers/
│   │   │   ├── auth.py              # Authentication (login, register)
│   │   │   ├── users.py             # Admin-only user management & role assignment
│   │   │   ├── inspections.py       # Inspection upload, analyze, list, delete
│   │   │   ├── dashboard.py         # Department & personal analytics KPIs
│   │   │   ├── reports.py           # Multi-format report download (PDF, DOCX, CSV)
│   │   │   ├── profile.py           # User profile management
│   │   │   └── rules.py             # Knowledge base & statutory rules catalog
│   │   ├── services/
│   │   │   ├── quality_service.py   # Blur, glare, and resolution assessment
│   │   │   └── inspection_service.py# Inspection pipeline orchestrator
│   │   ├── auth/                    # bcrypt security, JWT handlers & RBAC dependencies
│   │   ├── ocr/                     # OpenCV preprocessing & OCR text extractor
│   │   ├── extraction/
│   │   │   ├── field_extractor.py   # Statutory declaration parser (12 fields)
│   │   │   ├── normalizer.py        # Unit and value normalization
│   │   │   ├── font_analysis.py     # Rule 7 character height & Table I/II analysis
│   │   │   └── placement_checker.py # Rule 8 PDP clustering & clear space analysis
│   │   ├── rules/
│   │   │   ├── knowledge_base.py    # 21 statutory rules catalog with legal citations
│   │   │   └── compliance_engine.py # Rule evaluator (PASS, FAIL, NEEDS_REVIEW, NOT_APPLICABLE)
│   │   └── reports/
│   │       ├── pdf_generator.py     # ReportLab publication-grade PDF generator
│   │       └── report_exporter.py   # DOCX and CSV report exporters
│   ├── uploads/                     # Uploaded label images
│   ├── reports/                     # Generated PDF/DOCX/CSV reports
│   ├── demo_samples/                # Pre-rendered benchmark label images
│   ├── requirements.txt             # Python dependencies
│   ├── test_rules_knowledge_base.py # Statutory rules catalog test
│   ├── test_compliance_engine.py    # Compliance evaluation engine test
│   ├── test_font_analysis.py        # Rule 7 character height & font analysis test
│   ├── test_placement_checker.py    # Rule 8 PDP & clear space test
│   ├── test_report_exporter.py      # DOCX & CSV report export test
│   └── test_rbac.py                 # Role-based access control test
│
├── web/
│   ├── src/
│   │   ├── components/              # Sidebar, Header, EvidenceViewer, ProtectedRoute
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx        # KPI metrics, category chart, recent audit logs
│   │   │   ├── Scan.jsx             # Camera/file intake with dimension calibration
│   │   │   ├── Result.jsx           # Audit breakdown, font analysis, placement check, export
│   │   │   ├── History.jsx          # Auditable history with search and RBAC actions
│   │   │   ├── Reports.jsx          # Multi-format report download center
│   │   │   ├── Users.jsx            # Admin-only user management & role control
│   │   │   ├── Profile.jsx          # Officer profile settings
│   │   │   └── Login.jsx            # Authentication with 1-click demo accounts
│   │   ├── context/                 # AuthContext with role helpers (isAdmin, isSupervisor)
│   │   ├── services/api.js          # Axios client with multi-format download & user API
│   │   └── App.jsx                  # Route definitions
│   ├── package.json
│   └── vite.config.js
│
└── mobile/
    ├── src/
    │   ├── screens/                 # Dashboard, Scan, Result, History, Reports, Profile
    │   ├── navigation/              # AppNavigator & TabNavigator
    │   ├── services/api.js          # Native API client with format selector
    │   └── context/AuthContext.js   # Mobile AuthContext
    ├── App.js                       # Mobile root
    ├── app.json                     # Expo configuration
    └── package.json
```

---

## 4. Run Commands

### 1. Shared Backend (FastAPI)

```bash
# Navigate to backend folder
cd backend

# (Optional) Create and activate virtual environment
python -m venv venv

# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
# (Optional) Install testing & dev dependencies
pip install -r requirements-dev.txt

# Run backend development server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
*Backend API Docs (Swagger):* `http://127.0.0.1:8000/docs`

---

### 2. Web Application (React + Vite)

```bash
# Navigate to web folder
cd web

# Install dependencies
npm install

# Start Vite development server
npm run dev
```
*Web App URL:* `http://localhost:5173`

---

### 3. Mobile Application (React Native / Expo)

```bash
# Navigate to mobile folder
cd mobile

# Install dependencies
npm install

# Start Expo development server
npx expo start
```

**Testing on Different Targets:**
- **Android Emulator:** Press `a` in the Expo terminal (connects to `10.0.2.2:8000`).
- **Physical Device:** Install the **Expo Go** app on your phone, ensure your phone and PC are on the same Wi-Fi, and scan the QR code.
- **Web Browser:** Press `w` to test the mobile UI directly in your web browser.

---

## 5. Demo Accounts & RBAC Roles

SafeMetric pre-seeds three demo accounts across the role hierarchy for testing and jury demonstrations:

| Role | Email | Password | Scope & Permissions |
|:---|:---|:---|:---|
| **Admin** | `officer@safemetric.gov.in` | `password123` | Full system access: delete inspections, manage user accounts & assign roles (`GET/PUT /api/users`), view all records & analytics. |
| **Supervisor** | `supervisor@safemetric.gov.in` | `password123` | Department-wide analytics (`GET /api/dashboard/stats`), view all officers' inspections, cannot delete records or manage users. |
| **Inspector** | `inspector@safemetric.gov.in` | `password123` | Field officer: upload/scan commodities, view personal inspections & stats, download reports (PDF/DOCX/CSV). |

*The Web login screen features a 1-click **"Fill Demo Officer Credentials"** button.*

---

## 6. SIH Judge Demonstration Flow (Under 3 Minutes)

1. **Open SafeMetric Web** (`http://localhost:5173`).
2. **Login as Administrator:** Click *"Fill Demo Officer Credentials"* (`officer@safemetric.gov.in`) → Click *"Login to SafeMetric"*.
3. **Dashboard:** Review department-wide KPI metrics, compliance rate, violations breakdown, and audit activity.
4. **Initiate Scan:** Click **`+ SCAN PRODUCT`**.
   - Optional: Enter package dimensions (e.g., Length: `150` mm, Width: `200` mm) to enable high-confidence Rule 7 physical scale calibration.
5. **Demonstrate Compliant Commodity:**
   - Click **`✓ SafeRice (Compliant)`** button (or upload `sample_saferice.png`).
   - Click **`ANALYZE PRODUCT COMPLIANCE`**.
   - Observe the animated processing pipeline (Quality check → OpenCV preprocessing → OCR extraction → Font Analysis → Placement Check → Statutory Rules).
   - **Result Screen:**
     - Status: `COMPLIANT` green banner, 100% score, 0 violations.
     - **Font Size & Label Readability (Rule 7)** card: Character height measurements in mm, Table I/II thresholds, scale method indicator.
     - **Declaration Placement & Grouping (Rule 8)** card: Core declarations PDP cluster box, net quantity clear space verification.
     - Interactive OCR bounding box evidence viewer.
6. **Multi-Format Report Export:**
   - On the Result screen, demonstrate multi-format exports:
     - Click **`PDF`**: Downloads publication-grade certificate with stamp and signature line.
     - Click **`Word (.docx)`**: Downloads editable statutory inspection notice with officer sign-off block.
     - Click **`CSV`**: Downloads flat tabular audit row for spreadsheet archiving.
7. **Demonstrate Non-Compliant Commodity:**
   - Click **`Scan Next Commodity`** → select **`✕ Crispy Wafers (Non-Compliant)`**.
   - Review itemized violations (Missing Consumer Care under Rule 6(1)(n), ambiguous Net Quantity "Approx 200g" under Rule 12(6), missing currency symbol under Rule 6(1)(e)).
8. **Role-Based Access Control (RBAC) & User Management:**
   - Navigate to **`User Management`** (`/users`) in the sidebar (visible only to Admin).
   - Show active registered officers, change user roles dynamically between Inspector, Supervisor, and Admin.
   - Navigate to **`History`**: Admin sees all inspections with Delete buttons. Log in as Inspector to observe scoped personal view with Delete buttons disabled.

---

## 7. Legal Metrology Rules Implemented (21 Statutory Rules)

All 21 rules are directly encoded from the Legal Metrology Act, 2009 and the Legal Metrology (Packaged Commodities) Rules, 2011 (G.S.R. 202(E)):

| # | Rule ID | Legal Reference | Statutory Requirement | Severity |
|:--:|:---|:---|:---|:---:|
| 1 | `LMA-2009-SEC-18-MANDATORY` | Section 18(1), LMA 2009 | Minimum mandatory declarations present on pre-packaged commodity | HIGH |
| 2 | `LMA-2009-SEC-36-DEEMED-MFG` | Section 36(1) & 49, LMA 2009 | Deemed manufacturer liability attribution | HIGH |
| 3 | `PCR-2011-R6-1-A-MFG-NAME` | Rule 6(1)(a) & Rule 10(1)-(2) | Complete name of manufacturer, packer, or importer | HIGH |
| 4 | `PCR-2011-R6-1-A-ADDR` | Rule 6(1)(a) & Rule 10(1) Exp | Complete factory or registered postal address | HIGH |
| 5 | `PCR-2011-R6-1-B-GENERIC-NAME` | Rule 6(1)(b), PCR 2011 | Generic or common name of the commodity | HIGH |
| 6 | `PCR-2011-R6-1-C-NET-QUANTITY` | Rule 6(1)(c), Rule 11 & 12 | Standard net quantity in SI metric units (g, kg, ml, l) | HIGH |
| 7 | `PCR-2011-R12-6-PROHIBITED-QUALIFIERS` | Rule 12(6), PCR 2011 | Prohibition of misleading qualifiers ("approx", "about", "minimum") | HIGH |
| 8 | `PCR-2011-R13-UNITS-SYMBOLS` | Rule 13(1)-(5), PCR 2011 | Prescribed SI unit symbols and capitalization | MEDIUM |
| 9 | `PCR-2011-R6-1-D-DATE` | Rule 6(1)(d) & Rule 6(1)(g) | Month and year of manufacture, packing, or import (MM/YYYY) | HIGH |
| 10 | `PCR-2011-R6-1-E-MRP` | Rule 6(1)(e) & Rule 2(m) | Maximum Retail Price with currency (₹ / Rs.) and "incl. of all taxes" | HIGH |
| 11 | `PCR-2011-R6-1-EA-USP` | Rule 6(1)(ea) & Rule 6(11) | Unit Sale Price per g/kg/ml/l when net quantity > 100g/ml | MEDIUM |
| 12 | `PCR-2011-R6-1-AB-COUNTRY-ORIGIN` | Rule 6(1)(ab) & Rule 10(1) | Country of Origin statement on all commodities | HIGH |
| 13 | `PCR-2011-R6-2-CONSUMER-CARE` | Rule 6(2), PCR 2011 | Consumer Care grievance phone, email, and postal contact | HIGH |
| 14 | `PCR-2011-R6-3-STICKER-RESTRICTION` | Rule 6(3) & Rule 6(4) | Prohibition of price alteration by sticker overlay | HIGH |
| 15 | `PCR-2011-R5-SECOND-SCHEDULE` | Rule 5 & Second Schedule | Standard packaging size compliance for scheduled commodities | MEDIUM |
| 16 | `PCR-2011-THIRD-SCHEDULE-WHEN-PACKED` | Rule 11(4) & Third Schedule | "When Packed" net quantity qualification restricted to specified goods | MEDIUM |
| 17 | `PCR-2011-R9-LEGIBILITY-CONTRAST-LANG` | Rule 9(1) & Rule 9(4) | Declarations prominent, legible, contrasting, in Hindi or English | MEDIUM |
| 18 | `PCR-2011-R26-STATUTORY-EXEMPTIONS` | Rule 26 & Rule 3 | Statutory exemptions for small (<= 10g/ml) or institutional packs | LOW |
| 19 | `PCR-2011-R7-PHYSICAL-MEASUREMENT` | Rule 7 & First Schedule | Maximum Permissible Error (MPE) physical weight advisory | LOW |
| 20 | `PCR-2011-R7-FONT-SIZE-COMPLIANCE` | Rule 7(1)-(3), Tables I & II | Character/numeral height in mm relative to package surface area | HIGH |
| 21 | `PCR-2011-R8-DECLARATION-PLACEMENT` | Rule 8(1)-(2), PCR 2011 | Grouping on Principal Display Panel; clear space around net quantity | HIGH |

---

## 8. Verification & Test Suites

The backend includes six automated verification test suites covering statutory compliance, font geometry, spatial placement, multi-format report generation, and role security:

```bash
cd backend

# Install test runner & client dependencies (pytest, httpx)
pip install -r requirements-dev.txt

# 1. Verify 21 statutory rules in Knowledge Base
python test_rules_knowledge_base.py

# 2. Verify Compliance Engine evaluation logic
python test_compliance_engine.py

# 3. Verify Rule 7 character height & Table I/II font analysis
python test_font_analysis.py

# 4. Verify Rule 8 PDP grouping & net quantity clear space checks
python test_placement_checker.py

# 5. Verify multi-format report exporter (PDF, DOCX, CSV)
python test_report_exporter.py

# 6. Verify Role-Based Access Control (Admin / Supervisor / Inspector)
python test_rbac.py
```

---

## 9. API Reference Summary

| Method | Endpoint | Access | Description |
|:---|:---|:---|:---|
| `POST` | `/api/auth/login` | Public | Authenticates officer and returns JWT bearer token |
| `POST` | `/api/auth/register` | Public | Registers new field officer (default role: `Inspector`) |
| `GET` | `/api/users` | Admin | Lists all registered users and their assigned roles |
| `PUT` | `/api/users/{id}/role` | Admin | Updates role of a specific user (`Admin`, `Supervisor`, `Inspector`) |
| `DELETE` | `/api/users/{id}` | Admin | Deletes user account (prevents self-deletion) |
| `POST` | `/api/inspections/upload` | Any Officer | Uploads commodity image with optional package dimensions (`package_length_mm`, `package_width_mm`) |
| `POST` | `/api/inspections/analyze` | Any Officer | Executes optical extraction, font analysis, placement check, and rule validation |
| `GET` | `/api/inspections` | Any Officer | Lists inspections (Inspectors see own; Supervisors/Admins see all) |
| `GET` | `/api/inspections/{id}` | Any Officer | Retrieves full inspection details with font and placement audit |
| `DELETE` | `/api/inspections/{id}` | Admin | Permanently deletes an inspection record |
| `GET` | `/api/dashboard/stats` | Any Officer | Retrieves analytics KPIs (Supervisors/Admins see department-wide stats) |
| `GET` | `/api/reports/{id}/download` | Any Officer | Downloads report with format query parameter: `?format=pdf`, `?format=docx`, or `?format=csv` |
| `GET` | `/api/rules` | Any Officer | Catalogs all 21 statutory Legal Metrology rules with citations |

---

## 10. Known Limitations & Roadmap

- **Multi-Angle Stitching:** Cylindrical packaging (bottles, cans) currently requires flat-label presentation; future releases will support panorama cylindrical unrolling.
- **Multilingual Recognition:** Support for regional Indian official languages (Hindi, Tamil, Marathi, Bengali, Telugu) under the 8th Schedule.
- **Central Regulatory Registry:** Integration with the National Consumer Helpline (NCH) and e-Daakhil consumer grievance portals.
