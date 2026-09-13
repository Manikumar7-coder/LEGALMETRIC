from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.auth.security import decode_access_token

security = HTTPBearer(auto_error=False)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("user_id")
    email = payload.get("email")
    if not user_id and not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    
    user = None
    if user_id:
        user = db.query(User).filter(User.id == user_id).first()
    elif email:
        user = db.query(User).filter(User.email == email).first()
        
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account no longer exists",
        )
        
    return user

def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User | None:
    if not credentials:
        return None
    try:
        return get_current_user(credentials, db)
    except Exception:
        return None


def normalize_role(role_str: str | None) -> str:
    """
    Normalizes arbitrary or legacy role strings to one of three canonical roles:
    'Admin', 'Supervisor', 'Inspector'.
    Enforcement Officer (legacy default) explicitly normalizes to 'Inspector' (least privilege).
    """
    if not role_str:
        return "Inspector"
    r = str(role_str).strip().lower()
    if r in ("admin", "administrator", "system_admin", "administrative officer", "admin officer"):
        return "Admin"
    elif r in ("supervisor", "lead inspector", "chief inspector", "reviewer", "zonal supervisor"):
        return "Supervisor"
    elif r in ("inspector", "enforcement officer", "legal metrology inspector", "officer", "field officer", "field inspector", "user"):
        return "Inspector"
    return "Inspector"


def require_role(*allowed_roles: str):
    """
    FastAPI dependency factory enforcing Role-Based Access Control (RBAC).
    Admin inherently satisfies all role requirements.
    Supervisor satisfies Supervisor and Inspector requirements.
    """
    normalized_allowed = {normalize_role(r) for r in allowed_roles}

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_role = normalize_role(current_user.role)

        # Admin has root privileges across all endpoints
        if user_role == "Admin":
            return current_user

        # Supervisor can access Supervisor and Inspector endpoints
        if "Supervisor" in normalized_allowed and user_role == "Supervisor":
            return current_user

        if user_role in normalized_allowed:
            return current_user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Access denied: This action requires one of [{', '.join(allowed_roles)}] permissions. "
                f"Your account role is '{current_user.role}'."
            )
        )

    return role_checker


# Canonical convenience dependencies
require_admin = require_role("Admin")
require_supervisor = require_role("Admin", "Supervisor")
require_inspector = require_role("Admin", "Supervisor", "Inspector")

