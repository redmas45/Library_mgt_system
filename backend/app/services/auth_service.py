from sqlalchemy.orm import Session
from passlib.context import CryptContext
from fastapi import HTTPException, status

from app.db.crud.user_crud import (
    get_user_by_email,
    get_user_by_username,
    create_user,
)
from app.db.models.user import User, UserRole
from app.db.schemas.user_schemas import UserCreate, Token
from app.dependencies.auth import create_access_token
from app.utils.logger import logger

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def register_user(db: Session, user_data: UserCreate) -> User:
    if get_user_by_email(db, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    if get_user_by_username(db, user_data.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken",
        )

    hashed_pw = hash_password(user_data.password)
    user = create_user(
        db=db,
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_pw,
        full_name=user_data.full_name,
    )
    logger.info(f"New user registered: {user.email}")
    return user


def register_admin(db: Session, user_data: UserCreate) -> User:
    if get_user_by_email(db, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    if get_user_by_username(db, user_data.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken",
        )

    hashed_pw = hash_password(user_data.password)
    user = create_user(
        db=db,
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_pw,
        full_name=user_data.full_name,
        role=UserRole.ADMIN,
    )
    logger.info(f"New admin registered: {user.email}")
    return user


def login_user(db: Session, email: str, password: str) -> Token:
    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value if isinstance(user.role, UserRole) else user.role,
        }
    )
    logger.info(f"User logged in: {user.email}")
    return Token(access_token=access_token)
