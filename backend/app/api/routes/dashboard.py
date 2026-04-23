from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies.db import get_db
from app.dependencies.auth import get_current_admin
from app.db.models.user import User
from app.db.schemas.dashboard_schemas import DashboardResponse
from app.services.dashboard_service import get_dashboard

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/", response_model=DashboardResponse)
def dashboard(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    return get_dashboard(db)
