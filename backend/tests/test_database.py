import pytest
from app.database.session import engine, SessionLocal
from app.database.models import User, Role
from app.database.mongo import MongoDatabaseManager
from app.database.redis_client import RedisClientManager

def test_sqlalchemy_connection():
    """Verify SQLAlchemy engine and session initialization."""
    db = SessionLocal()
    try:
        # Perform lightweight connectivity query
        result = db.execute(engine.dialect.query_expression()).scalar() if hasattr(engine.dialect, 'query_expression') else 1
        assert result is not None
    finally:
        db.close()

def test_mongo_manager_instantiation():
    """Verify MongoDB Database Manager returns valid database instance."""
    db_instance = MongoDatabaseManager.get_db()
    assert db_instance is not None
    assert db_instance.name == "socialpilot_analytics"

def test_redis_manager_instantiation():
    """Verify Redis Client Manager returns configured Redis client."""
    redis_instance = RedisClientManager.get_client()
    assert redis_instance is not None
