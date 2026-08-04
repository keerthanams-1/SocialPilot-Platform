import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app
from app.database.session import Base, get_db
from app.database.models import User, Role, Permission, UserSession, Team, TeamMember, SocialAccount, Post, Campaign, PublishingLog, PostMetric, Notification

# Setup in-memory SQLite database with StaticPool to keep connection alive
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def seed_test_database(db):
    """Seed the test database with required roles and permissions."""
    # 1. Add permissions
    permissions_data = [
        "team:create", "team:invite", "team:remove",
        "post:create", "post:publish", "post:delete",
        "analytics:view", "settings:edit"
    ]
    
    db_permissions = {}
    for p_name in permissions_data:
        new_perm = Permission(name=p_name)
        db.add(new_perm)
        db_permissions[p_name] = new_perm
    db.commit()

    # 2. Add roles and map permissions
    roles_mapping = {
        "Administrator": permissions_data,
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

    for r_name, p_names in roles_mapping.items():
        role = Role(name=r_name)
        role.permissions = [db_permissions[pn] for pn in p_names]
        db.add(role)
    db.commit()

@pytest.fixture(scope="function")
def db():
    # Setup test tables in persistent in-memory DB
    Base.metadata.create_all(bind=engine)
    
    session = TestingSessionLocal()
    seed_test_database(session)
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass
            
    # Override get_db dependency
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
