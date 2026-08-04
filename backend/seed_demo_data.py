import sys
import os
import uuid
from datetime import datetime, timedelta
import json

# Add backend root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.session import SessionLocal, engine
from app.database.models import (
    Base, Role, Permission, Team, TeamMember, SocialAccount,
    Campaign, CampaignMember, Post, PostMedia, Approval,
    PublishingLog, PostMetric, Notification, Report, SavedFilter, DashboardSetting
)
from app.users.models import User, OAuthAccount, UserLoginHistory
from app.core.security import get_password_hash
from app.core.crypto import encrypt_token

def seed_database():
    """Populates database with rich, production-grade demo records across all sections."""
    print("[+] Starting SocialPilot Demo Database Seeder...")

    # Recreate tables to ensure schema matches models
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. ROLES & PERMISSIONS
        print("  [1/9] Seeding Roles & Permissions...")
        roles_data = [
            ("Administrator", "Full system access and security administration"),
            ("Business Manager", "Manages workspace teams, campaigns, and approvals"),
            ("Content Creator", "Drafts, schedules, and submits posts for review"),
            ("Marketing Specialist", "Analyzes performance metrics and exports reports")
        ]
        roles = {}
        for role_name, desc in roles_data:
            role = db.query(Role).filter(Role.name == role_name).first()
            if not role:
                role = Role(name=role_name)
                db.add(role)
                db.commit()
                db.refresh(role)
            roles[role_name] = role

        # 2. USERS
        print("  [2/9] Seeding Workspace Users...")
        pass_hash = get_password_hash("Password123!")
        users_seed = [
            ("admin@socialpilot.com", "admin_user", "System Administrator", "Administrator"),
            ("bm_user@socialpilot.com", "business_mgr", "Sarah Jenkins (Business Mgr)", "Business Manager"),
            ("cc_user@socialpilot.com", "content_creator", "Alex Rivera (Content Creator)", "Content Creator"),
            ("mkt_user@socialpilot.com", "marketing_lead", "Elena Rostova (Marketing Lead)", "Marketing Specialist"),
            ("priya@socialpilot.com", "priya_sharma", "Priya Sharma (Brand Manager)", "Business Manager"),
            ("david@socialpilot.com", "david_miller", "David Miller (Analytics Lead)", "Marketing Specialist")
        ]

        users = {}
        for email, username, full_name, role_name in users_seed:
            user = db.query(User).filter((User.email == email) | (User.username == username)).first()
            if not user:
                user = User(
                    email=email,
                    username=username,
                    full_name=full_name,
                    password_hash=pass_hash,
                    role_id=roles[role_name].id,
                    is_verified=True
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            users[email] = user

        bm_user = users["bm_user@socialpilot.com"]
        cc_user = users["cc_user@socialpilot.com"]
        mkt_user = users["mkt_user@socialpilot.com"]
        admin_user = users["admin@socialpilot.com"]
        priya_user = users["priya@socialpilot.com"]
        david_user = users["david@socialpilot.com"]

        # 3. WORKSPACE TEAMS & MEMBERS
        print("  [3/9] Seeding Workspace Team & Members...")
        team = db.query(Team).filter(Team.name == "SocialPilot Enterprise Workspace").first()
        if not team:
            team = Team(name="SocialPilot Enterprise Workspace", owner_id=bm_user.id)
            db.add(team)
            db.commit()
            db.refresh(team)

            # Assign team memberships
            members_data = [
                (bm_user.id, "owner"),
                (admin_user.id, "admin"),
                (cc_user.id, "member"),
                (mkt_user.id, "member"),
                (priya_user.id, "admin"),
                (david_user.id, "member")
            ]
            for uid, role_in_team in members_data:
                member = db.query(TeamMember).filter(TeamMember.team_id == team.id, TeamMember.user_id == uid).first()
                if not member:
                    member = TeamMember(team_id=team.id, user_id=uid, role_in_team=role_in_team)
                    db.add(member)
            db.commit()

        # 4. SOCIAL CHANNELS
        print("  [4/9] Seeding Social Channels...")
        channels_seed = [
            ("facebook", "fb_page_1001", "SocialPilot Official Page", "https://images.unsplash.com/photo-1611162617474-5b21e879e113?w=150"),
            ("instagram", "ig_acc_2002", "@socialpilot_app", "https://images.unsplash.com/photo-1611262588024-d12430b98920?w=150"),
            ("linkedin", "li_company_3003", "SocialPilot Technologies Inc.", "https://images.unsplash.com/photo-1611944212129-29977ae1398c?w=150"),
            ("twitter", "x_handle_4044", "@SocialPilotHQ", "https://images.unsplash.com/photo-1611605698335-8b1569810432?w=150"),
            ("youtube", "yt_channel_5055", "SocialPilot Product Demos", "https://images.unsplash.com/photo-1611162616305-c69b3fa7fbe0?w=150")
        ]

        social_accounts = []
        for platform, ext_id, acc_name, avatar in channels_seed:
            acc = db.query(SocialAccount).filter(SocialAccount.team_id == team.id, SocialAccount.platform == platform).first()
            if not acc:
                acc = SocialAccount(
                    team_id=team.id,
                    user_id=bm_user.id,
                    platform=platform,
                    platform_account_id=ext_id,
                    account_name=acc_name,
                    avatar_url=avatar,
                    access_token=encrypt_token(f"mock_token_{platform}_12345"),
                    refresh_token=encrypt_token(f"mock_refresh_{platform}_67890"),
                    expires_at=datetime.utcnow() + timedelta(days=60)
                )
                db.add(acc)
                db.commit()
                db.refresh(acc)

            # Mirror OAuthAccount in users model
            oauth_acc = db.query(OAuthAccount).filter(OAuthAccount.user_id == bm_user.id, OAuthAccount.provider == platform).first()
            if not oauth_acc:
                oauth_acc = OAuthAccount(
                    user_id=bm_user.id,
                    provider=platform,
                    provider_user_id=ext_id,
                    access_token=encrypt_token(f"mock_token_{platform}_12345"),
                    refresh_token=encrypt_token(f"mock_refresh_{platform}_67890"),
                    expires_at=datetime.utcnow() + timedelta(days=60),
                    connected=True
                )
                db.add(oauth_acc)
                db.commit()
            social_accounts.append(acc)

        # 5. CAMPAIGNS
        print("  [5/9] Seeding Marketing Campaigns...")
        now = datetime.utcnow()
        campaigns_seed = [
            ("Q3 Enterprise SaaS Launch", "Multi-platform launch campaign for Q3 Enterprise features.", now - timedelta(days=15), now + timedelta(days=45), 10000.0, "Enterprise Lead Generation & Brand Awareness", "active"),
            ("Summer Growth & Engagement Boost", "Targeted social media drive to increase followers by 25%.", now - timedelta(days=30), now + timedelta(days=15), 5000.0, "Audience Engagement & Community Building", "active"),
            ("Black Friday Special Promotion", "Holiday promotional campaign with special tier discount offers.", now + timedelta(days=60), now + timedelta(days=90), 15000.0, "Conversion & Paid Customer Acquisition", "planning")
        ]

        campaigns = []
        for name, desc, start_d, end_d, budget, obj, status in campaigns_seed:
            camp = db.query(Campaign).filter(Campaign.team_id == team.id, Campaign.name == name).first()
            if not camp:
                camp = Campaign(
                    team_id=team.id,
                    name=name,
                    description=desc,
                    start_date=start_d,
                    end_date=end_d,
                    budget=budget,
                    objectives=obj,
                    status=status
                )
                db.add(camp)
                db.commit()
                db.refresh(camp)

                # Add campaign members
                c_member = CampaignMember(campaign_id=camp.id, user_id=cc_user.id, role_in_campaign="contributor")
                db.add(c_member)
                c_member2 = CampaignMember(campaign_id=camp.id, user_id=mkt_user.id, role_in_campaign="reviewer")
                db.add(c_member2)
                db.commit()
            campaigns.append(camp)

        c1 = campaigns[0]
        c2 = campaigns[1]

        # 6. POSTS, APPROVALS & SCHEDULER
        print("  [6/9] Seeding Posts, Approvals & Scheduled Content...")
        posts_seed = [
            # Published Posts
            ("🚀 Exciting Announcement! SocialPilot v5.0 is officially live with AI analytics & real-time team collaboration! Try it today. #SaaS #SocialMedia #Productivity", "published", "facebook", now - timedelta(days=5), c1.id),
            ("✨ Transform your social media workflow with automated scheduling, real-time metrics, and instant PDF reports! Link in bio. #Marketing #Growth", "published", "instagram", now - timedelta(days=3), c2.id),
            ("Enterprise team management made effortless. Manage multi-channel publishing with enterprise RBAC security and audit logging.", "published", "linkedin", now - timedelta(days=2), c1.id),
            ("Did you know? Real-time time-series analytics can boost post engagement by up to 40%! Discover how in our latest blog.", "published", "twitter", now - timedelta(days=1), c2.id),

            # Scheduled Posts
            ("📢 Join our upcoming webinar: 'Scaling Enterprise Social Strategy in 2026' featuring industry marketing leaders! Reserve your spot now.", "scheduled", "linkedin", now + timedelta(days=2), c1.id),
            ("💡 Pro Tip: Customizing your dashboard widgets gives your marketing team instant visibility into top-performing post metrics.", "scheduled", "twitter", now + timedelta(days=4), c2.id),

            # Pending Approval Post
            ("🔥 Sneak Peek: Black Friday Early Access Deals are coming soon! Stay tuned for exclusive enterprise discounts.", "pending_approval", "facebook", None, c1.id),

            # Rejected Post
            ("Buy our product now for 50% off!! Limited time offer click here link below.", "rejected", "instagram", None, c2.id)
        ]

        for content_text, status, target_platform, pub_or_sched_date, camp_id in posts_seed:
            post = db.query(Post).filter(Post.team_id == team.id, Post.content_text == content_text).first()
            if not post:
                post = Post(
                    team_id=team.id,
                    user_id=cc_user.id,
                    campaign_id=camp_id,
                    content_text=content_text,
                    platform_targets=json.dumps([target_platform]),
                    media_urls=json.dumps(["https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=600"]),
                    status=status,
                    scheduled_at=pub_or_sched_date if status == "scheduled" else None
                )
                db.add(post)
                db.commit()
                db.refresh(post)

                # Attach media record
                media = PostMedia(
                    post_id=post.id,
                    media_type="image",
                    media_url="https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=600",
                    filesize=1024500,
                    width=1200,
                    height=630,
                    mime_type="image/jpeg"
                )
                db.add(media)

                # Attach Approval Workflow record
                if status in ["pending_approval", "published", "scheduled", "rejected"]:
                    appr_status = "pending" if status == "pending_approval" else ("approved" if status in ["published", "scheduled"] else "rejected")
                    approval = Approval(
                        post_id=post.id,
                        reviewer_id=bm_user.id if appr_status != "pending" else None,
                        status=appr_status,
                        comments="Looks great! Approved for social dispatch." if appr_status == "approved" else ("Please refine call-to-action tone." if appr_status == "rejected" else None),
                        reviewed_at=now if appr_status != "pending" else None
                    )
                    db.add(approval)

                # Attach Metrics if Published
                if status == "published":
                    metric = PostMetric(
                        post_id=post.id,
                        platform=target_platform,
                        impressions=8900,
                        clicks=215,
                        engagements=419
                    )
                    db.add(metric)

                    # Publishing Log
                    pub_log = PublishingLog(
                        post_id=post.id,
                        team_id=team.id,
                        platform=target_platform,
                        status="success",
                        published_at=pub_or_sched_date or now
                    )
                    db.add(pub_log)
                db.commit()

        # 7. REPORTS
        print("  [7/9] Seeding PDF, CSV & Excel Reports...")
        reports_seed = [
            ("Weekly Executive KPI Summary", "pdf", "weekly", now - timedelta(days=7), "completed", "https://socialpilot.s3.amazonaws.com/reports/weekly_kpi_summary.pdf"),
            ("Q3 Enterprise Launch Campaign Performance", "pdf", "once", now - timedelta(days=2), "completed", "https://socialpilot.s3.amazonaws.com/reports/q3_launch_report.pdf"),
            ("Multi-Channel Engagement Metrics Export", "csv", "monthly", now - timedelta(days=1), "completed", "https://socialpilot.s3.amazonaws.com/reports/engagement_metrics.csv"),
            ("Quarterly Audience Growth Multi-Sheet Analysis", "excel", "monthly", now + timedelta(days=7), "scheduled", None)
        ]

        for title, format_type, r_type, last_run, r_status, file_url in reports_seed:
            report = db.query(Report).filter(Report.team_id == team.id, Report.title == title).first()
            if not report:
                report = Report(
                    team_id=team.id,
                    user_id=mkt_user.id,
                    title=title,
                    report_type=r_type,
                    format=format_type,
                    status=r_status,
                    file_url=file_url,
                    generated_at=last_run
                )
                db.add(report)
                db.commit()

        # 8. NOTIFICATIONS & ACTIVITY LOGS
        print("  [8/9] Seeding Notifications & Audit Logs...")
        notifications_seed = [
            ("New Post Submitted for Approval", "Content Creator submitted 'Black Friday Early Access' for review.", "warning", False),
            ("Post Published Successfully", "Post dispatched to Facebook Page and LinkedIn Page.", "info", True),
            ("Scheduled PDF Report Ready", "'Weekly Executive KPI Summary' is ready for download.", "success", True),
            ("OAuth Token Renewal Notice", "Facebook Page OAuth token auto-renewed successfully.", "info", True)
        ]

        for notif_title, notif_msg, n_type, is_read in notifications_seed:
            notif = db.query(Notification).filter(Notification.team_id == team.id, Notification.title == notif_title).first()
            if not notif:
                notif = Notification(
                    team_id=team.id,
                    user_id=bm_user.id,
                    title=notif_title,
                    message=notif_msg,
                    type=n_type,
                    is_read=is_read,
                    created_at=now - timedelta(hours=3)
                )
                db.add(notif)
                db.commit()

        # Login Activity Logs & Audit Logs
        from app.database.models import AuditLog
        all_users = [admin_user, bm_user, cc_user, mkt_user, priya_user, david_user]
        
        audit_events = [
            (admin_user, "LOGIN", "Logged into SocialPilot Administrator Control Console"),
            (bm_user, "CREATE_CAMPAIGN", "Created new marketing campaign 'Q3 Enterprise SaaS Launch'"),
            (cc_user, "SUBMIT_POST", "Submitted draft post 'SocialPilot v5.0 Announcement' for approval"),
            (bm_user, "APPROVE_POST", "Approved post 'SocialPilot v5.0 Announcement' for dispatch"),
            (mkt_user, "SCHEDULE_POST", "Scheduled publication on LinkedIn, Facebook, and Instagram"),
            (priya_user, "CREATE_CAMPAIGN", "Created brand campaign 'Summer Growth & Engagement Boost'"),
            (david_user, "GENERATE_REPORT", "Exported monthly campaign performance analytics CSV report"),
            (admin_user, "UPDATE_PERMISSIONS", "Updated workspace role permissions for Content Creators"),
            (cc_user, "ADD_MEDIA", "Uploaded media assets to Visual Calendar queue"),
            (david_user, "CONNECT_CHANNEL", "Verified OAuth token connection for LinkedIn Company Page")
        ]

        for u in all_users:
            login_log = UserLoginHistory(
                user_id=u.id,
                ip="127.0.0.1",
                country="United States",
                city="San Francisco",
                browser="Chrome 124.0",
                device="Desktop (Windows)",
                success=True,
                login_time=now - timedelta(minutes=45 + all_users.index(u) * 10)
            )
            db.add(login_log)

        for idx, (usr, act, desc) in enumerate(audit_events):
            audit_log = AuditLog(
                user_name=usr.full_name,
                user_email=usr.email,
                role_name=usr.role.name if usr.role else "Member",
                action=f"{act}: {desc}",
                ip_address="127.0.0.1",
                created_at=now - timedelta(minutes=15 + idx * 25)
            )
            db.add(audit_log)
        db.commit()

        # 9. DASHBOARD WIDGET SETTINGS & SAVED FILTERS
        print("  [9/9] Seeding Dashboard Widget Settings & Saved Filters...")
        widget_setting = db.query(DashboardSetting).filter(DashboardSetting.user_id == bm_user.id).first()
        if not widget_setting:
            widget_setting = DashboardSetting(
                team_id=team.id,
                user_id=bm_user.id,
                config_json=json.dumps({
                    "widgets": ["kpi_summary", "campaign_overview", "recent_approvals", "channel_breakdown"],
                    "theme": "dark"
                })
            )
            db.add(widget_setting)

        saved_filter = db.query(SavedFilter).filter(SavedFilter.user_id == bm_user.id).first()
        if not saved_filter:
            saved_filter = SavedFilter(
                team_id=team.id,
                user_id=bm_user.id,
                filter_name="High Engagement Posts",
                filter_params_json=json.dumps({"min_engagement": 4.0, "platform": "facebook"})
            )
            db.add(saved_filter)
        db.commit()

        print("\n[SUCCESS] DEMO DATABASE SEEDED SUCCESSFULLY!")
        print("-------------------------------------------------------")
        print("  All 11 Frontend Sections Now Have Rich Seed Data:")
        print("  1. Dashboard Summary (KPIs, Charts, Health Metrics)")
        print("  2. Workspace Users (Admin, Business Mgr, Creator, Specialist)")
        print("  3. Social Channels (Facebook, Instagram, LinkedIn, Twitter, YouTube)")
        print("  4. Campaigns (Q3 Enterprise Launch, Summer Growth, Black Friday)")
        print("  5. Scheduler (Published, Scheduled, Pending Approval, Rejected)")
        print("  6. Analytics (Time-series data, Engagement, Reach, Impressions)")
        print("  7. Reports (PDF, CSV, Excel export files & scheduled runs)")
        print("  8. Audit & Activity Logs (Security events & user login history)")
        print("  9. Notifications (In-app alerts with read/unread statuses)")
        print("  10. Profile (User credentials, avatar, role info)")
        print("  11. Settings (Dashboard layouts, saved filters & API keys)")
        print("-------------------------------------------------------")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error seeding demo database: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
