"""
CRUD operations for the User model.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List

from app.db.models.user import User, UserRole


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get a user by their ID."""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get a user by their email address."""
    return db.query(User).filter(User.email == email).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get a user by their username."""
    return db.query(User).filter(User.username == username).first()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """Get a paginated list of users."""
    return db.query(User).offset(skip).limit(limit).all()


def get_user_count(db: Session) -> int:
    """Get total number of users."""
    return db.query(func.count(User.id)).scalar()


def create_user(
    db: Session,
    email: str,
    username: str,
    hashed_password: str,
    full_name: Optional[str] = None,
    role: UserRole = UserRole.USER,
) -> User:
    """Create a new user."""
    user = User(
        email=email,
        username=username,
        hashed_password=hashed_password,
        full_name=full_name,
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user_id: int, **kwargs) -> Optional[User]:
    """Update user fields."""
    user = get_user_by_id(db, user_id)
    if not user:
        return None
    for key, value in kwargs.items():
        if hasattr(user, key) and value is not None:
            setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user


def deactivate_user(db: Session, user_id: int) -> Optional[User]:
    """Deactivate a user account."""
    return update_user(db, user_id, is_active=0)
