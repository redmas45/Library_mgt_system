"""
Script utilities — shared helpers for scripts.
"""

import os
import sys

# Ensure backend modules are importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))


def get_db_session():
    """Get a database session for scripts."""
    from app.db.database import SessionLocal
    return SessionLocal()


def seed_admin_user(email: str = "admin@library.ai", password: str = "admin123"):
    """Create a default admin user for development."""
    from app.db.crud.user_crud import get_user_by_email, create_user
    from app.db.models.user import UserRole
    from app.services.auth_service import hash_password

    db = get_db_session()
    try:
        existing = get_user_by_email(db, email)
        if existing:
            print(f"Admin user already exists: {email}")
            return

        hashed = hash_password(password)
        user = create_user(
            db=db,
            email=email,
            username="admin",
            hashed_password=hashed,
            full_name="System Administrator",
            role=UserRole.ADMIN,
        )
        print(f"✅ Admin user created: {user.email} (password: {password})")
    finally:
        db.close()


if __name__ == "__main__":
    print("Seeding admin user...")
    seed_admin_user()
    print("Done!")
