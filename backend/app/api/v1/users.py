"""User profile and administrative user-management routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_current_user
from app.core.security import hash_password
from app.db.models import User
from app.db.session import get_db
from app.schemas.user import UserAdminUpdate, UserRead, UserUpdateMe

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserRead)
def read_me(current_user: User = Depends(get_current_user)) -> User:
    """Return the authenticated user's profile."""
    return current_user


@router.patch("/me", response_model=UserRead)
def update_me(
    payload: UserUpdateMe,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    """Update the authenticated user's full name, preferred model, or password."""
    if payload.full_name is not None:
        current_user.full_name = payload.full_name
    if payload.preferred_model is not None:
        current_user.preferred_model = payload.preferred_model
    if payload.password is not None:
        current_user.hashed_password = hash_password(payload.password)

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("", response_model=list[UserRead])
def list_users(
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> list[User]:
    """List all platform users (admin only)."""
    return list(db.scalars(select(User).order_by(User.created_at.desc())).all())


@router.patch("/{user_id}", response_model=UserRead)
def admin_update_user(
    user_id: str,
    payload: UserAdminUpdate,
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> User:
    """Update user role, active flag, or preferred model (admin only)."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if payload.role is not None:
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.preferred_model is not None:
        user.preferred_model = payload.preferred_model

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_user(
    user_id: str,
    admin_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> None:
    """Delete a user account (admin only, cannot self-delete)."""
    if user_id == admin_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrators cannot delete their own active account",
        )
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    db.delete(user)
    db.commit()
