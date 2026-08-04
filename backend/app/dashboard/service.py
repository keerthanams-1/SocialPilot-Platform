from sqlalchemy.orm import Session
from app.database.models import DashboardLayout
from app.dashboard.admin_dashboard import AdminDashboardService
from app.dashboard.business_dashboard import BusinessDashboardService
from app.dashboard.creator_dashboard import CreatorDashboardService
from app.dashboard.marketing_dashboard import MarketingDashboardService
from app.dashboard.schemas import AdminDashboardOut, BusinessDashboardOut, CreatorDashboardOut, MarketingDashboardOut, DashboardLayoutOut, DashboardLayoutUpdate

class DashboardOrchestratorService:
    """Service orchestrator for role-based multi-dashboard views and layout customization."""

    @staticmethod
    def get_admin_dashboard(db: Session) -> AdminDashboardOut:
        return AdminDashboardService.get_dashboard(db)

    @staticmethod
    def get_business_dashboard(db: Session, team_id: str) -> BusinessDashboardOut:
        return BusinessDashboardService.get_dashboard(db, team_id)

    @staticmethod
    def get_creator_dashboard(db: Session, user_id: str) -> CreatorDashboardOut:
        return CreatorDashboardService.get_dashboard(db, user_id)

    @staticmethod
    def get_marketing_dashboard(db: Session, team_id: str) -> MarketingDashboardOut:
        return MarketingDashboardService.get_dashboard(db, team_id)

    @staticmethod
    def get_user_layout(db: Session, user_id: str, role_name: str) -> DashboardLayout:
        layout = db.query(DashboardLayout).filter(DashboardLayout.user_id == user_id).first()
        if not layout:
            layout = DashboardLayout(
                user_id=user_id,
                role_name=role_name,
                layout_json='["followers_widget", "engagement_widget", "reach_widget"]',
                theme="light",
                default_date_range="30d"
            )
            db.add(layout)
            db.commit()
            db.refresh(layout)
        return layout

    @staticmethod
    def update_user_layout(db: Session, user_id: str, role_name: str, payload: DashboardLayoutUpdate) -> DashboardLayout:
        layout = DashboardOrchestratorService.get_user_layout(db, user_id, role_name)
        layout.layout_json = payload.layout_json
        if payload.theme:
            layout.theme = payload.theme
        if payload.default_date_range:
            layout.default_date_range = payload.default_date_range
        db.commit()
        db.refresh(layout)
        return layout
