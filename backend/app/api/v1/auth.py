"""Authentication routes: registration and JWT login."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models import User
from app.db.session import get_db
from app.schemas.auth import TokenResponse, UserLogin, UserRegister
from app.schemas.user import UserRead

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserRegister, db: Session = Depends(get_db)) -> User:
    """Register a new user account; the first registered user becomes admin."""
    existing = db.scalar(
        select(User).where(
            or_(User.email == payload.email.lower(), User.username == payload.username)
        )
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with that email or username already exists",
        )

    is_first_user = db.scalar(select(User.id).limit(1)) is None
    settings = get_settings()
    user = User(
        email=payload.email.lower(),
        username=payload.username,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role="admin" if is_first_user else "user",
        preferred_model=settings.default_model,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login_user(payload: UserLogin, db: Session = Depends(get_db)) -> TokenResponse:
    """Authenticate credentials and issue a signed JWT access token."""
    identifier = payload.username_or_email.strip()
    user = db.scalar(
        select(User).where(
            or_(User.email == identifier.lower(), User.username == identifier)
        )
    )
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    settings = get_settings()
    token = create_access_token(
        subject=user.id,
        role=user.role,
        extra_claims={"username": user.username},
    )
    return TokenResponse(
        access_token=token,
        expires_in_minutes=settings.access_token_expire_minutes,
    )
