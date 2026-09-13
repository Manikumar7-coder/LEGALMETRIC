import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.database import Base, engine, SessionLocal
from app.routers import (
    auth_router,
    profile_router,
    settings_router,
    inspections_router,
    dashboard_router,
    reports_router,
    rules_router,
    users_router
)


def _seed_infrastructure(db):
    """
    Seeds ONLY the legal rules and one default officer account on first run.
    Does NOT create any demo inspections, dummy products, or fake history records.
    The History page will be empty until the user actually uploads and processes a product image.
    """
    from app.models.user import User
    from app.models.rule import Rule
    from app.auth.security import hash_password
    from app.rules.rule_engine import rule_engine
    import datetime

    # 1. Seed Legal Metrology rules (idempotent — skips if already present)
    rules_metadata = rule_engine.get_all_rules_metadata()
    for rm in rules_metadata:
        existing = db.query(Rule).filter(Rule.rule_id == rm["rule_id"]).first()
        if not existing:
            r = Rule(
                rule_id=rm["rule_id"],
                field=rm["field"],
                description=rm["description"],
                required=rm["required"],
                severity=rm["severity"],
                active=True,
                reference=rm["reference"]
            )
            db.add(r)
    db.commit()

    # 2. Seed default inspector account (idempotent — skips if already present)
    default_email = "officer@safemetric.gov.in"
    officer = db.query(User).filter(User.email == default_email).first()
    if not officer:
        officer = User(
            name="Officer Rajesh Kumar",
            email=default_email,
            password_hash=hash_password("password123"),
            role="Admin",
            organization="Department of Consumer Affairs, Delhi Zone",
            created_at=datetime.datetime.utcnow()
        )
        db.add(officer)
        db.commit()
    elif officer.role != "Admin":
        officer.role = "Admin"
        db.commit()

    # Seed Supervisor account if not present
    sup_email = "supervisor@safemetric.gov.in"
    supervisor = db.query(User).filter(User.email == sup_email).first()
    if not supervisor:
        supervisor = User(
            name="Supervisor Sunita Patel",
            email=sup_email,
            password_hash=hash_password("password123"),
            role="Supervisor",
            organization="Legal Metrology Regional HQ",
            created_at=datetime.datetime.utcnow()
        )
        db.add(supervisor)
        db.commit()

    # Seed Field Inspector account if not present
    insp_email = "inspector@safemetric.gov.in"
    inspector = db.query(User).filter(User.email == insp_email).first()
    if not inspector:
        inspector = User(
            name="Field Inspector Amit Verma",
            email=insp_email,
            password_hash=hash_password("password123"),
            role="Inspector",
            organization="Legal Metrology Enforcement Squad",
            created_at=datetime.datetime.utcnow()
        )
        db.add(inspector)
        db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB schema (creates tables if they don't exist)
    Base.metadata.create_all(bind=engine)

    # Seed infrastructure only — legal rules and default officer, NO demo inspections
    db = SessionLocal()
    try:
        _seed_infrastructure(db)
    finally:
        db.close()

    yield


app = FastAPI(
    title="SafeMetric – Legal Metrology Compliance System",
    description=(
        "Automated optical label-compliance checking under the "
        "Legal Metrology (Packaged Commodities) Rules, 2011. "
        "Processes ANY uploaded packaged commodity image generically — "
        "no product database, no predefined products."
    ),
    version="2.0.0",
    lifespan=lifespan
)

# CORS configuration
# Explicit list of allowed origins. Wildcard "*" CANNOT be used when allow_credentials=True
# because browsers reject wildcard Access-Control-Allow-Origin with credentials/JWT headers.
ALLOWED_ORIGINS = [
    # Web Frontend - Vite Dev Server (localhost & 127.0.0.1)
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://localhost:5173",
    "https://127.0.0.1:5173",

    # Web Frontend - Standard React / Alternative Dev Ports
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://localhost:3000",
    "https://127.0.0.1:3000",

    # Web Frontend - Vite Preview Ports
    "http://localhost:4173",
    "http://127.0.0.1:4173",
    "https://localhost:4173",
    "https://127.0.0.1:4173",

    # Common Development & Preview Ports
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "https://localhost:8080",
    "https://127.0.0.1:8080",

    # Mobile Frontend - Expo Metro Bundler & Expo Web
    "http://localhost:8081",
    "http://127.0.0.1:8081",
    "https://localhost:8081",
    "https://127.0.0.1:8081",
    "http://localhost:19006",
    "http://127.0.0.1:19006",
    "https://localhost:19006",
    "https://127.0.0.1:19006",

    # Backend Host Origin (Direct API calls or Swagger UI)
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "https://localhost:8000",
    "https://127.0.0.1:8000",
]

# Append any production/staging origins provided via environment variables
_env_origins = os.getenv("ALLOWED_ORIGINS") or os.getenv("CORS_ORIGINS")
if _env_origins:
    for _o in _env_origins.split(","):
        _cleaned = _o.strip().rstrip("/")
        if _cleaned and _cleaned not in ALLOWED_ORIGINS:
            ALLOWED_ORIGINS.append(_cleaned)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "Content-Length", "Content-Type"],
)

# Static file directories
backend_root = os.path.dirname(os.path.dirname(__file__))
uploads_dir = os.path.join(backend_root, "uploads")
demo_dir = os.path.join(backend_root, "demo_samples")
reports_dir = os.path.join(backend_root, "reports")

os.makedirs(uploads_dir, exist_ok=True)
os.makedirs(demo_dir, exist_ok=True)
os.makedirs(reports_dir, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")
app.mount("/demo_samples", StaticFiles(directory=demo_dir), name="demo_samples")

# Include API Routers
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(settings_router)
app.include_router(inspections_router)
app.include_router(dashboard_router)
app.include_router(reports_router)
app.include_router(rules_router)
app.include_router(users_router)


@app.get("/")
def root():
    return {
        "system": "SafeMetric – Legal Metrology Compliance System",
        "status": "ONLINE",
        "rules_edition": "Legal Metrology (Packaged Commodities) Rules, 2011",
        "note": "No product database. Processes any uploaded packaged commodity image."
    }


@app.get("/api/health")
def health_check():
    return {"status": "healthy", "engine": "FastAPI", "db": "SQLite / SQLAlchemy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
