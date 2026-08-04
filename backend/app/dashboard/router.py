import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.dependencies import get_current_user, require_role
from app.core.responses import standard_response
from app.users.models import User
from app.dashboard.service import DashboardOrchestratorService
from app.dashboard.schemas import DashboardLayoutUpdate

logger = logging.getLogger("socialpilot.dashboard.router")
router = APIRouter(prefix="/api/v1/dashboard", tags=["Role-Based Dashboards & Customization"])

@router.get("/admin")
def get_admin_dashboard(
    db: Session = Depends(get_db),
    current_user: User = require_role(["Administrator"])
):
    """Retrieve System Administrator Health & Operational Dashboard."""
    dashboard_data = DashboardOrchestratorService.get_admin_dashboard(db)
    return standard_response(
        success=True,
        message="Administrator dashboard data retrieved",
        data=dashboard_data.model_dump()
    )

@router.get("/business")
def get_business_dashboard(
    db: Session = Depends(get_db),
    current_user: User = require_role(["Administrator", "Business User"])
):
    """Retrieve Business Manager Dashboard (Campaigns, ROI, Budgets, Approvals)."""
    team_id = current_user.team_memberships[0].team_id if current_user.team_memberships else "demo_team"
    dashboard_data = DashboardOrchestratorService.get_business_dashboard(db, team_id)
    return standard_response(
        success=True,
        message="Business manager dashboard data retrieved",
        data=dashboard_data.model_dump()
    )

@router.get("/creator")
def get_creator_dashboard(
    db: Session = Depends(get_db),
    current_user: User = require_role(["Administrator", "Business User", "Content Creator"])
):
    """Retrieve Content Creator Workspace Dashboard (Drafts, Schedules, Media, Personal Stats)."""
    dashboard_data = DashboardOrchestratorService.get_creator_dashboard(db, current_user.id)
    return standard_response(
        success=True,
        message="Content creator dashboard data retrieved",
        data=dashboard_data.model_dump()
    )

@router.get("/marketing")
def get_marketing_dashboard(
    db: Session = Depends(get_db),
    current_user: User = require_role(["Administrator", "Business User", "Marketing Specialist"])
):
    """Retrieve Marketing Team Analytics Dashboard (CTR, Reach, Impressions, Best Time)."""
    team_id = current_user.team_memberships[0].team_id if current_user.team_memberships else "demo_team"
    dashboard_data = DashboardOrchestratorService.get_marketing_dashboard(db, team_id)
    return standard_response(
        success=True,
        message="Marketing team dashboard data retrieved",
        data=dashboard_data.model_dump()
    )

@router.get("/layout")
def get_user_dashboard_layout(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve user's custom widget layout and theme preferences."""
    role_name = current_user.role.name if current_user.role else "Business User"
    layout = DashboardOrchestratorService.get_user_layout(db, current_user.id, role_name)
    return standard_response(
        success=True,
        message="User dashboard layout retrieved",
        data={
            "user_id": layout.user_id,
            "role_name": layout.role_name,
            "layout_json": layout.layout_json,
            "theme": layout.theme,
            "default_date_range": layout.default_date_range,
            "updated_at": layout.updated_at.isoformat()
        }
    )

@router.put("/layout")
def update_user_dashboard_layout(
    payload: DashboardLayoutUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Save updated widget arrangement, default date range, and theme settings."""
    role_name = current_user.role.name if current_user.role else "Business User"
    layout = DashboardOrchestratorService.update_user_layout(db, current_user.id, role_name, payload)
    return standard_response(
        success=True,
        message="User dashboard layout updated",
        data={
            "user_id": layout.user_id,
            "theme": layout.theme,
            "default_date_range": layout.default_date_range
        }
    )
