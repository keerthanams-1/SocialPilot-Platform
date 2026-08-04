from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from app.database.models import User, Role, Permission, UserSession, Team, TeamMember, SocialAccount, Post, Campaign, PublishingLog, PostMetric, Notification
from app.core.security import get_password_hash
from app.database.schemas import UserRegister, UserProfileUpdate, TeamCreate, TeamMemberAdd, PostCreate, PostUpdate, CampaignCreate, CampaignUpdate, PublishingLogCreate, PostMetricCreate, NotificationCreate
from app.core.crypto import encrypt_token, decrypt_token

class UserRepository:
    @staticmethod
    def get_by_id(db: Session, user_id: str) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def create(db: Session, user_in: UserRegister, role_id: str) -> User:
        hashed_password = get_password_hash(user_in.password)
        db_user = User(
            name=user_in.name,
            email=user_in.email,
            password_hash=hashed_password,
            phone=user_in.phone,
            role_id=role_id,
            status="active"
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def update(db: Session, db_user: User, user_update: UserProfileUpdate) -> User:
        update_data = user_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_user, key, value)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def update_password(db: Session, db_user: User, new_password_hash: str) -> User:
        db_user.password_hash = new_password_hash
        db_user.updated_at = datetime.utcnow()
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

class RoleRepository:
    @staticmethod
    def get_by_name(db: Session, name: str) -> Optional[Role]:
        return db.query(Role).filter(Role.name == name).first()

    @staticmethod
    def get_all(db: Session) -> List[Role]:
        return db.query(Role).all()

    @staticmethod
    def create(db: Session, name: str) -> Role:
        db_role = Role(name=name)
        db.add(db_role)
        db.commit()
        db.refresh(db_role)
        return db_role

class SessionRepository:
    @staticmethod
    def create_session(
        db: Session, user_id: str, refresh_token: str, expires_in_days: int, ip: str = None, ua: str = None
    ) -> UserSession:
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        db_session = UserSession(
            user_id=user_id,
            refresh_token=refresh_token,
            expires_at=expires_at,
            ip_address=ip,
            user_agent=ua
        )
        db.add(db_session)
        db.commit()
        db.refresh(db_session)
        return db_session

    @staticmethod
    def get_session_by_token(db: Session, refresh_token: str) -> Optional[UserSession]:
        token_hash = hashlib.sha256(refresh_token.encode('utf-8')).hexdigest()
        session = db.query(UserSession).filter(UserSession.refresh_token_hash == token_hash).first()
        if not session and hasattr(UserSession, 'refresh_token'):
            session = db.query(UserSession).filter(UserSession.refresh_token == refresh_token).first()
        return session

    @staticmethod
    def revoke_session(db: Session, refresh_token: str) -> None:
        db_session = SessionRepository.get_session_by_token(db, refresh_token)
        if db_session:
            db_session.is_revoked = True
            db.commit()
            db_session.is_revoked = True
            db.commit()

    @staticmethod
    def revoke_all_user_sessions(db: Session, user_id: str) -> None:
        db.query(UserSession).filter(
            UserSession.user_id == user_id, 
            UserSession.is_revoked == False
        ).update({"is_revoked": True})
        db.commit()

class TeamRepository:
    @staticmethod
    def get_team_by_id(db: Session, team_id: str) -> Optional[Team]:
        return db.query(Team).filter(Team.id == team_id).first()

    @staticmethod
    def create_team(db: Session, team_in: TeamCreate, owner_id: str) -> Team:
        db_team = Team(name=team_in.name, owner_id=owner_id)
        db.add(db_team)
        db.commit()
        db.refresh(db_team)
        
        # Add owner as an admin of the team
        owner_member = TeamMember(
            team_id=db_team.id,
            user_id=owner_id,
            role_in_team="owner"
        )
        db.add(owner_member)
        db.commit()
        db.refresh(db_team)
        return db_team

    @staticmethod
    def add_member(db: Session, team_id: str, user_id: str, role_in_team: str = "member") -> TeamMember:
        db_member = TeamMember(
            team_id=team_id,
            user_id=user_id,
            role_in_team=role_in_team
        )
        db.add(db_member)
        db.commit()
        db.refresh(db_member)
        return db_member

    @staticmethod
    def get_member(db: Session, team_id: str, user_id: str) -> Optional[TeamMember]:
        return db.query(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id
        ).first()

    @staticmethod
    def remove_member(db: Session, team_id: str, user_id: str) -> bool:
        member = TeamRepository.get_member(db, team_id, user_id)
        if member:
            db.delete(member)
            db.commit()
            return True
        return False

class SocialAccountRepository:
    @staticmethod
    def get_by_id(db: Session, account_id: str) -> Optional[SocialAccount]:
        return db.query(SocialAccount).filter(SocialAccount.id == account_id).first()

    @staticmethod
    def get_by_team_id(db: Session, team_id: str) -> List[SocialAccount]:
        return db.query(SocialAccount).filter(SocialAccount.team_id == team_id).all()

    @staticmethod
    def get_by_platform_and_account_id(
        db: Session, team_id: str, platform: str, platform_account_id: str
    ) -> Optional[SocialAccount]:
        return db.query(SocialAccount).filter(
            SocialAccount.team_id == team_id,
            SocialAccount.platform == platform,
            SocialAccount.platform_account_id == platform_account_id
        ).first()

    @staticmethod
    def connect_account(
        db: Session, 
        team_id: str, 
        user_id: str, 
        platform: str, 
        platform_account_id: str, 
        name: str, 
        avatar: Optional[str], 
        token: str, 
        refresh: Optional[str], 
        expires_at: Optional[datetime]
    ) -> SocialAccount:
        # Encrypt token values for security
        enc_token = encrypt_token(token)
        enc_refresh = encrypt_token(refresh)

        # Check if already connected
        existing = SocialAccountRepository.get_by_platform_and_account_id(
            db, team_id=team_id, platform=platform, platform_account_id=platform_account_id
        )
        if existing:
            # Update credentials
            existing.account_name = name
            existing.avatar_url = avatar
            existing.access_token = enc_token
            existing.refresh_token = enc_refresh
            existing.expires_at = expires_at
            existing.user_id = user_id
            existing.updated_at = datetime.utcnow()
            db.add(existing)
            db.commit()
            db.refresh(existing)
            return existing
            
        # Create new connection
        new_account = SocialAccount(
            team_id=team_id,
            user_id=user_id,
            platform=platform,
            platform_account_id=platform_account_id,
            account_name=name,
            avatar_url=avatar,
            access_token=enc_token,
            refresh_token=enc_refresh,
            expires_at=expires_at
        )
        db.add(new_account)
        db.commit()
        db.refresh(new_account)
        return new_account

    @staticmethod
    def disconnect_account(db: Session, account_id: str) -> bool:
        account = SocialAccountRepository.get_by_id(db, account_id)
        if account:
            db.delete(account)
            db.commit()
            return True
        return False

import json

class PostRepository:
    @staticmethod
    def get_by_id(db: Session, post_id: str) -> Optional[Post]:
        return db.query(Post).filter(Post.id == post_id).first()

    @staticmethod
    def get_by_team(
        db: Session, 
        team_id: str, 
        status: Optional[str] = None, 
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None
    ) -> List[Post]:
        query = db.query(Post).filter(Post.team_id == team_id)
        
        if status:
            query = query.filter(Post.status == status)
            
        if start_date:
            query = query.filter(Post.scheduled_at >= start_date)
            
        if end_date:
            query = query.filter(Post.scheduled_at <= end_date)
            
        return query.order_by(Post.scheduled_at.asc()).all()

    @staticmethod
    def create_post(db: Session, post_data: PostCreate, user_id: str) -> Post:
        media_str = json.dumps(post_data.media_urls or [])
        targets_str = json.dumps(post_data.platform_targets)
        
        # Determine status
        initial_status = "draft" if post_data.schedule_type == "draft" else "scheduled"
        
        db_post = Post(
            team_id=post_data.team_id,
            user_id=user_id,
            content_text=post_data.content_text,
            media_urls=media_str,
            platform_targets=targets_str,
            schedule_type=post_data.schedule_type,
            recurrence_pattern=post_data.recurrence_pattern,
            scheduled_at=post_data.scheduled_at,
            status=initial_status,
            campaign_id=post_data.campaign_id
        )
        db.add(db_post)
        db.commit()
        db.refresh(db_post)
        return db_post

    @staticmethod
    def update_post(db: Session, post_id: str, updates: PostUpdate) -> Optional[Post]:
        db_post = PostRepository.get_by_id(db, post_id)
        if not db_post:
            return None
            
        update_data = updates.model_dump(exclude_unset=True)
        
        if "media_urls" in update_data:
            db_post.media_urls = json.dumps(update_data["media_urls"] or [])
            del update_data["media_urls"]
            
        if "platform_targets" in update_data:
            db_post.platform_targets = json.dumps(update_data["platform_targets"])
            del update_data["platform_targets"]
            
        for key, value in update_data.items():
            setattr(db_post, key, value)
            
        db_post.updated_at = datetime.utcnow()
        db.add(db_post)
        db.commit()
        db.refresh(db_post)
        return db_post

    @staticmethod
    def delete_post(db: Session, post_id: str) -> bool:
        db_post = PostRepository.get_by_id(db, post_id)
        if db_post:
            db.delete(db_post)
            db.commit()
            return True
        return False

class CampaignRepository:
    @staticmethod
    def get_by_id(db: Session, campaign_id: str) -> Optional[Campaign]:
        return db.query(Campaign).filter(Campaign.id == campaign_id).first()

    @staticmethod
    def get_by_team(db: Session, team_id: str) -> List[Campaign]:
        return db.query(Campaign).filter(Campaign.team_id == team_id).order_by(Campaign.created_at.desc()).all()

    @staticmethod
    def create_campaign(db: Session, campaign_data: CampaignCreate) -> Campaign:
        db_campaign = Campaign(
            team_id=campaign_data.team_id,
            name=campaign_data.name,
            description=campaign_data.description,
            start_date=campaign_data.start_date,
            end_date=campaign_data.end_date,
            budget=campaign_data.budget,
            objectives=campaign_data.objectives,
            status="active"
        )
        db.add(db_campaign)
        db.commit()
        db.refresh(db_campaign)
        return db_campaign

    @staticmethod
    def update_campaign(db: Session, campaign_id: str, updates: CampaignUpdate) -> Optional[Campaign]:
        db_campaign = CampaignRepository.get_by_id(db, campaign_id)
        if not db_campaign:
            return None
            
        update_data = updates.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_campaign, key, value)
            
        db_campaign.updated_at = datetime.utcnow()
        db.add(db_campaign)
        db.commit()
        db.refresh(db_campaign)
        return db_campaign

    @staticmethod
    def delete_campaign(db: Session, campaign_id: str) -> bool:
        db_campaign = CampaignRepository.get_by_id(db, campaign_id)
        if db_campaign:
            # Set linked post relations to NULL ( cascade set null is handled by SQLAlchemy ForeignKey configuration on delete='SET NULL' )
            db.delete(db_campaign)
            db.commit()
            return True
        return False

class PublishingLogRepository:
    @staticmethod
    def create_log(db: Session, log_data: PublishingLogCreate) -> PublishingLog:
        db_log = PublishingLog(
            post_id=log_data.post_id,
            team_id=log_data.team_id,
            platform=log_data.platform,
            status=log_data.status,
            error_message=log_data.error_message
        )
        db.add(db_log)
        db.commit()
        db.refresh(db_log)
        return db_log

    @staticmethod
    def get_by_post(db: Session, post_id: str) -> List[PublishingLog]:
        return db.query(PublishingLog).filter(PublishingLog.post_id == post_id).order_by(PublishingLog.published_at.desc()).all()

    @staticmethod
    def get_by_team(db: Session, team_id: str) -> List[PublishingLog]:
        return db.query(PublishingLog).filter(PublishingLog.team_id == team_id).order_by(PublishingLog.published_at.desc()).all()

class PostMetricRepository:
    @staticmethod
    def create_metric(db: Session, metric_data: PostMetricCreate) -> PostMetric:
        db_metric = PostMetric(
            post_id=metric_data.post_id,
            platform=metric_data.platform,
            impressions=metric_data.impressions,
            clicks=metric_data.clicks,
            engagements=metric_data.engagements
        )
        db.add(db_metric)
        db.commit()
        db.refresh(db_metric)
        return db_metric

    @staticmethod
    def get_by_post(db: Session, post_id: str) -> List[PostMetric]:
        return db.query(PostMetric).filter(PostMetric.post_id == post_id).order_by(PostMetric.retrieved_at.desc()).all()

    @staticmethod
    def get_team_metrics(db: Session, team_id: str) -> List[PostMetric]:
        return db.query(PostMetric).join(Post).filter(Post.team_id == team_id).order_by(PostMetric.retrieved_at.asc()).all()

class NotificationRepository:
    @staticmethod
    def create_notification(db: Session, notification_data: NotificationCreate) -> Notification:
        db_notif = Notification(
            team_id=notification_data.team_id,
            user_id=notification_data.user_id,
            title=notification_data.title,
            message=notification_data.message,
            type=notification_data.type
        )
        db.add(db_notif)
        db.commit()
        db.refresh(db_notif)
        return db_notif

    @staticmethod
    def get_user_notifications(db: Session, user_id: str, team_id: str, unread_only: bool = False) -> List[Notification]:
        query = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.team_id == team_id
        )
        if unread_only:
            query = query.filter(Notification.is_read == False)
        return query.order_by(Notification.created_at.desc()).all()

    @staticmethod
    def mark_as_read(db: Session, notification_id: str) -> Optional[Notification]:
        db_notif = db.query(Notification).filter(Notification.id == notification_id).first()
        if db_notif:
            db_notif.is_read = True
            db.add(db_notif)
            db.commit()
            db.refresh(db_notif)
        return db_notif

    @staticmethod
    def mark_all_read(db: Session, user_id: str, team_id: str) -> int:
        unread_notifs = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.team_id == team_id,
            Notification.is_read == False
        ).all()
        for notif in unread_notifs:
            notif.is_read = True
            db.add(notif)
        db.commit()
        return len(unread_notifs)
