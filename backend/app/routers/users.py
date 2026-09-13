"""
users.py
========
User Management Router (Admin Only).
Provides endpoints for listing users, updating user roles, and account management.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserRole
from app.auth.jwt_handler import require_admin, normalize_role


router = APIRouter(prefix="/api/users", tags=["User Management"])


class UpdateRoleRequest(BaseModel):
    role: str


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str
    organization: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


@router.get("", response_model=List[UserOut])
def list_users(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Lists all user accounts in the department. Admin only."""
    users = db.query(User).order_by(User.id.asc()).all()
    result = []
    for u in users:
        result.append(UserOut(
            id=u.id,
            name=u.name,
            email=u.email,
            role=normalize_role(u.role),
            organization=u.organization,
            created_at=u.created_at.isoformat() if u.created_at else None
        ))
    return result


@router.put("/{user_id}/role", response_model=UserOut)
def update_user_role(
    user_id: int,
    req: UpdateRoleRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Updates a user's role (Inspector, Supervisor, Admin). Admin only."""
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found.")

    new_role = normalize_role(req.role)
    target_user.role = new_role
    db.commit()
    db.refresh(target_user)

    return UserOut(
        id=target_user.id,
        name=target_user.name,
        email=target_user.email,
        role=target_user.role,
        organization=target_user.organization,
        created_at=target_user.created_at.isoformat() if target_user.created_at else None
    )


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Deletes a user account. Admin only. Cannot delete own account."""
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own administrative account."
        )

    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found.")

    db.delete(target_user)
    db.commit()
    return {"message": f"User account #{user_id} ({target_user.email}) successfully deleted."}
