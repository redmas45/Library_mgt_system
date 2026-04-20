"""
Auth routes — registration, login, and profile endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies.db import get_db
from app.dependencies.auth import get_current_user, get_current_admin
from app.db.models.user import User
from app.db.schemas.user_schemas import UserCreate, UserLogin, UserResponse, Token
from app.services.auth_service import register_user, register_admin, login_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=201)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user account."""
    user = register_user(db, user_data)
    return UserResponse.model_validate(user)


@router.post("/register/admin", response_model=UserResponse, status_code=201)
def register_admin_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Register a new admin account. Requires existing admin auth."""
    user = register_admin(db, user_data)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """Login and receive a JWT token."""
    return login_user(db, user_data.email, user_data.password)


@router.get("/me", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    """Get the current user's profile."""
    return UserResponse.model_validate(current_user)
