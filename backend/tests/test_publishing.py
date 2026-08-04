import pytest
import json
from datetime import datetime, timedelta
from fastapi import status
from app.database.models import Post, PublishingLog, SocialAccount
from app.core.scheduler import publish_pending_posts

def test_publishing_loop_success_and_failure_retry(client, db):
    # 1. Register and login team owner
    client.post("/api/v1/auth/register", json={
        "name": "Owner User",
        "email": "owner@socialpilot.com",
        "password": "SecurePassword123!",
        "confirm_password": "SecurePassword123!"
    })
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "owner@socialpilot.com",
        "password": "SecurePassword123!"
    })
    owner_headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    # 2. Create team
    team_resp = client.post("/api/v1/teams", json={"name": "Workspace A"}, headers=owner_headers)
    team_id = team_resp.json()["id"]

    # 3. Connect LinkedIn channel
    connect_resp = client.get(f"/api/v1/social/connect/linkedin?team_id={team_id}", headers=owner_headers)
    state = connect_resp.json()["state"]
    client.post(
        "/api/v1/social/callback?platform=linkedin", 
        json={"code": "mock_code_1", "state": state, "team_id": team_id}, 
        headers=owner_headers
    )
    chan_resp = client.get(f"/api/v1/social/accounts?team_id={team_id}", headers=owner_headers)
    chan_id = chan_resp.json()[0]["id"]

    # 4. Schedule a post in the future (passes validation)
    future_time = datetime.utcnow() + timedelta(days=1)
    post_payload = {
        "team_id": team_id,
        "content_text": "Automated dispatcher check!",
        "platform_targets": [chan_id],
        "schedule_type": "scheduled",
        "scheduled_at": future_time.isoformat()
    }
    
    post_resp = client.post("/api/v1/posts", json=post_payload, headers=owner_headers)
    assert post_resp.status_code == status.HTTP_200_OK
    post_id = post_resp.json()["id"]
    
    # Force schedule time to past inside database to simulate elapsed time
    past_time = datetime.utcnow() - timedelta(minutes=5)
    db_post = db.query(Post).filter(Post.id == post_id).first()
    db_post.scheduled_at = past_time
    db.commit()

    # 5. Execute the background worker publisher task manually
    import asyncio
    asyncio.run(publish_pending_posts(db))

    # 6. Verify post status updated to published and logs recorded
    db.refresh(db_post)
    assert db_post.status == "published"
    logs = db.query(PublishingLog).filter(PublishingLog.post_id == post_id).all()
    assert len(logs) == 1
    assert logs[0].status == "success"
    assert logs[0].platform == "linkedin"

    # 7. Schedule a second post in the future
    post_payload_2 = {
        "team_id": team_id,
        "content_text": "Failed connection dispatch check!",
        "platform_targets": [chan_id],
        "schedule_type": "scheduled",
        "scheduled_at": future_time.isoformat()
    }
    post_resp_2 = client.post("/api/v1/posts", json=post_payload_2, headers=owner_headers)
    assert post_resp_2.status_code == status.HTTP_200_OK
    post_id_2 = post_resp_2.json()["id"]
    
    # Force schedule time to past inside database
    db_post_2 = db.query(Post).filter(Post.id == post_id_2).first()
    db_post_2.scheduled_at = past_time
    db.commit()

    # Trigger Connection Expiry simulation on LinkedIn
    client.post(f"/api/v1/social/accounts/{chan_id}/simulate-expiry", headers=owner_headers)

    # Execute background worker publisher task manually
    asyncio.run(publish_pending_posts(db))

    # Verify second post status updated to failed and logged with error
    db.refresh(db_post_2)
    assert db_post_2.status == "failed"
    logs_2 = db.query(PublishingLog).filter(PublishingLog.post_id == post_id_2).all()
    assert len(logs_2) == 1
    assert logs_2[0].status == "failed"
    assert "expired" in logs_2[0].error_message.lower()

    # 8. Attempt manual retry route (while LinkedIn is still expired, should stay failed)
    retry_resp = client.post(f"/api/v1/posts/{post_id_2}/retry", headers=owner_headers)
    assert retry_resp.status_code == status.HTTP_200_OK
    assert retry_resp.json()["status"] == "failed"
    
    # Assert second log added
    assert len(db.query(PublishingLog).filter(PublishingLog.post_id == post_id_2).all()) == 2

    # Re-connect/restore active token on original channel directly in the database to allow retry success
    db_chan = db.query(SocialAccount).filter(SocialAccount.id == chan_id).first()
    db_chan.expires_at = datetime.utcnow() + timedelta(days=30)
    db.commit()

    # 9. Attempt manual retry route again (should now succeed)
    retry_resp_2 = client.post(f"/api/v1/posts/{post_id_2}/retry", headers=owner_headers)
    assert retry_resp_2.status_code == status.HTTP_200_OK
    assert retry_resp_2.json()["status"] == "published"

    # Assert third log is success
    logs_final = db.query(PublishingLog).filter(PublishingLog.post_id == post_id_2).order_by(PublishingLog.published_at.desc()).all()
    assert len(logs_final) == 3
    assert logs_final[0].status == "success"
