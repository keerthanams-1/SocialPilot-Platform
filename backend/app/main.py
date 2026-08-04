import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from app.core.config import settings
from app.database.session import engine, Base, SessionLocal
from app.database.models import Role, Permission, User, Team, TeamMember, SocialAccount, Post, Campaign, PublishingLog, PostMetric, Notification, AuditLog
from app.core.security import get_password_hash
from app.core.crypto import encrypt_token
from app.core.scheduler import scheduler_loop
from app.auth.routes import router as auth_router
from app.users.routes import router as user_router
from app.authentication.router import router as v2_auth_router
from app.users.router import router as v2_user_router
from app.teams.routes import router as team_router
from app.social.routes import router as social_router
from app.social.router import router as v3_social_router
from app.posts.routes import router as post_router
from app.campaigns.routes import router as campaign_router
from app.analytics.routes import router as analytics_router
from app.notifications.routes import router as notifications_router
from app.teams.workspace_router import router as workspace_router

# Seeding script to run on database creation
def seed_database():
    db = SessionLocal()
    try:
        # 1. Define standard permissions
        permissions_data = [
            "team:create", "team:invite", "team:remove",
            "post:create", "post:publish", "post:delete",
            "analytics:view", "settings:edit"
        ]
        
        db_permissions = {}
        for p_name in permissions_data:
            existing = db.query(Permission).filter(Permission.name == p_name).first()
            if not existing:
                new_perm = Permission(name=p_name)
                db.add(new_perm)
                db_permissions[p_name] = new_perm
            else:
                db_permissions[p_name] = existing
        db.commit()

        # 2. Define standard roles and their permission mapping
        roles_mapping = {
            "Administrator": permissions_data, # Admins override checking, but seed all just in case
            "Business User": [
                "team:create", "team:invite", "team:remove",
                "post:create", "post:publish", "post:delete",
                "analytics:view", "settings:edit"
            ],
            "Marketing Team": [
                "team:invite", "post:create", "post:publish", "post:delete", "analytics:view"
            ],
            "Content Creator": [
                "post:create", "analytics:view"
            ]
        }

        db_roles = {}
        for r_name, p_names in roles_mapping.items():
            role = db.query(Role).filter(Role.name == r_name).first()
            if not role:
                role = Role(name=r_name)
                db.add(role)
                db.commit()
                db.refresh(role)
            
            # Map permissions to role
            role.permissions = [db_permissions[pn] for pn in p_names]
            db.add(role)
            db_roles[r_name] = role
            
        db.commit()

        # 3. Create/Seed the four user accounts representing each role
        users_seeding = [
            {"name": "Admin Owner", "email": "admin@socialpilot.com", "username": "admin_owner", "role": "Administrator"},
            {"name": "Business Manager", "email": "business@socialpilot.com", "username": "business_mgr", "role": "Business User"},
            {"name": "Marketing Specialist", "email": "marketing@socialpilot.com", "username": "marketing_spec", "role": "Marketing Team"},
            {"name": "Content Producer", "email": "creator@socialpilot.com", "username": "creator_prod", "role": "Content Creator"}
        ]
        
        db_users = {}
        for u in users_seeding:
            user = db.query(User).filter(User.email == u["email"]).first()
            if not user:
                hashed = get_password_hash("SecurePassword123!")
                user = User(
                    name=u["name"],
                    email=u["email"],
                    username=u["username"],
                    password_hash=hashed,
                    role_id=db_roles[u["role"]].id,
                    status="active"
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            db_users[u["email"]] = user

        # 4. Create the shared Team Workspace "Global Marketing Workspace"
        team = db.query(Team).filter(Team.name == "Global Marketing Workspace").first()
        if not team:
            team = Team(name="Global Marketing Workspace", owner_id=db_users["admin@socialpilot.com"].id)
            db.add(team)
            db.commit()
            db.refresh(team)
            
            # Map all 4 users as members in this team workspace
            members_map = [
                ("admin@socialpilot.com", "owner"),
                ("business@socialpilot.com", "admin"),
                ("marketing@socialpilot.com", "member"),
                ("creator@socialpilot.com", "member")
            ]
            for email, role_in_team in members_map:
                tm = TeamMember(
                    team_id=team.id,
                    user_id=db_users[email].id,
                    role_in_team=role_in_team
                )
                db.add(tm)
            db.commit()

        # 5. Create Connected Channels (LinkedIn and Instagram)
        accounts_seeding = [
            {"platform": "linkedin", "name": "Corporate LinkedIn Page"},
            {"platform": "instagram", "name": "Company Instagram Feed"}
        ]
        db_accounts = {}
        for acc_spec in accounts_seeding:
            acc = db.query(SocialAccount).filter(
                SocialAccount.team_id == team.id,
                SocialAccount.platform == acc_spec["platform"]
            ).first()
            if not acc:
                acc = SocialAccount(
                    team_id=team.id,
                    user_id=db_users["admin@socialpilot.com"].id,
                    platform=acc_spec["platform"],
                    platform_account_id=f"simulated_{acc_spec['platform']}_id",
                    account_name=acc_spec["name"],
                    avatar_url=f"https://api.dicebear.com/7.x/identicon/svg?seed={acc_spec['platform']}",
                    access_token=encrypt_token("mock_token"),
                    refresh_token=encrypt_token("mock_refresh"),
                    expires_at=datetime.utcnow() + timedelta(days=90),
                    created_at=datetime.utcnow()
                )
                db.add(acc)
                db.commit()
                db.refresh(acc)
            db_accounts[acc_spec["platform"]] = acc

        # 6. Create Campaigns "Q3 Global Launch Campaign"
        campaign = db.query(Campaign).filter(Campaign.name == "Q3 Global Launch Campaign").first()
        if not campaign:
            campaign = Campaign(
                team_id=team.id,
                name="Q3 Global Launch Campaign",
                description="Promoting the brand launch globally across professional and consumer channels.",
                start_date=datetime.utcnow() - timedelta(days=5),
                end_date=datetime.utcnow() + timedelta(days=25),
                budget=5000.0,
                objectives="Increase corporate impressions by 30% and secure 500 landing page sign-ups.",
                created_at=datetime.utcnow()
            )
            db.add(campaign)
            db.commit()
            db.refresh(campaign)

        # 7. Create seeded posts representing each role's actions:
        # A. Published post (Marketing Team action) with impressions metrics
        pub_post = db.query(Post).filter(
            Post.team_id == team.id,
            Post.content_text == "Announcing the global launch of our brand new corporate website! Check it out."
        ).first()
        if not pub_post:
            import json
            pub_post = Post(
                team_id=team.id,
                user_id=db_users["marketing@socialpilot.com"].id,
                content_text="Announcing the global launch of our brand new corporate website! Check it out.",
                platform_targets=json.dumps([db_accounts["linkedin"].id]),
                schedule_type="scheduled",
                scheduled_at=datetime.utcnow() - timedelta(days=2),
                status="published",
                campaign_id=campaign.id,
                created_at=datetime.utcnow() - timedelta(days=3)
            )
            db.add(pub_post)
            db.commit()
            db.refresh(pub_post)
            
            # Seed performance metrics
            metrics = PostMetric(
                post_id=pub_post.id,
                platform="linkedin",
                impressions=1250,
                clicks=85,
                engagements=64,
                retrieved_at=datetime.utcnow()
            )
            db.add(metrics)
            db.commit()

        # B. Future scheduled post (Marketing Team action)
        sch_post = db.query(Post).filter(
            Post.team_id == team.id,
            Post.content_text == "Sharing three tips to scale business operations efficiently. Read more on our blog!"
        ).first()
        if not sch_post:
            import json
            sch_post = Post(
                team_id=team.id,
                user_id=db_users["marketing@socialpilot.com"].id,
                content_text="Sharing three tips to scale business operations efficiently. Read more on our blog!",
                platform_targets=json.dumps([db_accounts["linkedin"].id]),
                schedule_type="scheduled",
                scheduled_at=datetime.utcnow() + timedelta(days=1),
                status="scheduled",
                campaign_id=campaign.id,
                created_at=datetime.utcnow()
            )
            db.add(sch_post)
            db.commit()

        # C. Draft post created by Content Creator
        draft_post = db.query(Post).filter(
            Post.team_id == team.id,
            Post.content_text == "[Draft] Behind-the-scenes snapshot of our design workshop. Exciting designs coming soon!"
        ).first()
        if not draft_post:
            import json
            draft_post = Post(
                team_id=team.id,
                user_id=db_users["creator@socialpilot.com"].id,
                content_text="[Draft] Behind-the-scenes snapshot of our design workshop. Exciting designs coming soon!",
                platform_targets=json.dumps([db_accounts["instagram"].id]),
                schedule_type="draft",
                scheduled_at=None,
                status="scheduled",
                campaign_id=campaign.id,
                created_at=datetime.utcnow()
            )
            db.add(draft_post)
            db.commit()

        # D. Failed post to show logs & notifications
        fail_post = db.query(Post).filter(
            Post.team_id == team.id,
            Post.content_text == "Simulating expired access credentials to demonstrate warning logs and notification bell systems."
        ).first()
        if not fail_post:
            import json
            fail_post = Post(
                team_id=team.id,
                user_id=db_users["marketing@socialpilot.com"].id,
                content_text="Simulating expired access credentials to demonstrate warning logs and notification bell systems.",
                platform_targets=json.dumps([db_accounts["instagram"].id]),
                schedule_type="scheduled",
                scheduled_at=datetime.utcnow() - timedelta(minutes=10),
                status="failed",
                campaign_id=campaign.id,
                created_at=datetime.utcnow() - timedelta(hours=1)
            )
            db.add(fail_post)
            db.commit()
            db.refresh(fail_post)
            
            # Seed failed log
            log = PublishingLog(
                post_id=fail_post.id,
                team_id=team.id,
                platform="instagram",
                status="failed",
                error_message="Connection expired for channel Company Instagram Feed. Please re-authenticate.",
                published_at=datetime.utcnow() - timedelta(minutes=10)
            )
            db.add(log)
            
            # Seed notifications for Admin and Marketing Team
            for email in ["admin@socialpilot.com", "marketing@socialpilot.com"]:
                notif = Notification(
                    team_id=team.id,
                    user_id=db_users[email].id,
                    title="Publishing Dispatch Failed",
                    message="We were unable to publish your post to Instagram because the connection expired.",
                    type="error",
                    is_read=False,
                    created_at=datetime.utcnow() - timedelta(minutes=10)
                )
                db.add(notif)
            db.commit()

            # Seed mock Audit Logs
            existing_logs = db.query(AuditLog).first()
            if not existing_logs:
                mock_logs = [
                    {"user_name": "Admin Owner", "email": "admin@socialpilot.com", "role": "Administrator", "action": "LOGIN", "offset_hours": 5},
                    {"user_name": "Content Producer", "email": "creator@socialpilot.com", "role": "Content Creator", "action": "LOGIN", "offset_hours": 4},
                    {"user_name": "Content Producer", "email": "creator@socialpilot.com", "role": "Content Creator", "action": "LOGOUT", "offset_hours": 3},
                    {"user_name": "Marketing Specialist", "email": "marketing@socialpilot.com", "role": "Marketing Team", "action": "LOGIN", "offset_hours": 2},
                    {"user_name": "Admin Owner", "email": "admin@socialpilot.com", "role": "Administrator", "action": "LOGOUT", "offset_hours": 1},
                    {"user_name": "Admin Owner", "email": "admin@socialpilot.com", "role": "Administrator", "action": "LOGIN", "offset_minutes": 10}
                ]
                for log_spec in mock_logs:
                    created = datetime.utcnow()
                    if "offset_hours" in log_spec:
                        created -= timedelta(hours=log_spec["offset_hours"])
                    elif "offset_minutes" in log_spec:
                        created -= timedelta(minutes=log_spec["offset_minutes"])
                    
                    log = AuditLog(
                        user_name=log_spec["user_name"],
                        user_email=log_spec["email"],
                        role_name=log_spec["role"],
                        action=log_spec["action"],
                        ip_address="192.168.1.45" if log_spec["role"] == "Administrator" else "10.0.4.12",
                        created_at=created
                    )
                    db.add(log)
                db.commit()

    except Exception as e:
        print(f"Error seeding database: {e}")
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    # Initialize SQLite tables automatically on startup
    Base.metadata.create_all(bind=engine)
    seed_database()
    
    # Start background scheduler loop
    scheduler_task = asyncio.create_task(scheduler_loop())
    
    yield
    # Shutdown actions
    scheduler_task.cancel()
    try:
        await scheduler_task
    except asyncio.CancelledError:
        pass

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
)

# Set CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def custom_exception_handler(request: Request, exc: Exception):
    # Retrieve details for HTTPException
    status_code = getattr(exc, "status_code", None) or status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = getattr(exc, "detail", str(exc) if str(exc) else "Internal server error")
    
    return JSONResponse(
        status_code=status_code,
        content={
            "status_code": status_code,
            "error": "Error",
            "detail": detail
        }
    )

from app.social.webhooks.webhook_router import router as webhook_router
from app.campaigns.router import router as v4_campaigns_router
from app.publishing.router import router as v4_publishing_router
from app.dashboard.router import router as v5_dashboard_router
from app.analytics.router import router as v5_analytics_router
from app.notifications.router import router as v5_notifications_router
from app.reports.router import router as v5_reports_router
from app.health.router import router as v6_health_router
from app.core.security_middleware import SecurityHeadersMiddleware

app.add_middleware(SecurityHeadersMiddleware)

# Register routers
app.include_router(v6_health_router)
app.include_router(webhook_router)
app.include_router(v4_campaigns_router)
app.include_router(v4_publishing_router)
app.include_router(v5_dashboard_router)
app.include_router(v5_analytics_router)
app.include_router(v5_notifications_router)
app.include_router(v5_reports_router)
app.include_router(v2_auth_router, prefix=settings.API_V1_STR)
app.include_router(v2_user_router, prefix=settings.API_V1_STR)
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(user_router, prefix=settings.API_V1_STR)
app.include_router(team_router, prefix=settings.API_V1_STR)
app.include_router(v3_social_router)
app.include_router(social_router, prefix=settings.API_V1_STR)
app.include_router(post_router, prefix=settings.API_V1_STR)
app.include_router(campaign_router, prefix=settings.API_V1_STR)
app.include_router(analytics_router, prefix=settings.API_V1_STR)
app.include_router(notifications_router, prefix=settings.API_V1_STR)
app.include_router(workspace_router)

@app.get("/")
def read_root():
    return {
        "project": settings.PROJECT_NAME,
        "status": "online",
        "docs_url": "/docs"
    }
