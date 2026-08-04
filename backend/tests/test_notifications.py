import pytest
from datetime import datetime, timedelta
from fastapi import status
from app.database.models import Post, SocialAccount, Notification
from app.core.scheduler import publish_pending_posts

def test_notifications_lifecycle_and_triggers(client, db):
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

    # 4. Schedule a post in the future
    future_time = datetime.utcnow() + timedelta(days=1)
    post_payload = {
        "team_id": team_id,
        "content_text": "Post that triggers success alerts!",
        "platform_targets": [chan_id],
        "schedule_type": "scheduled",
        "scheduled_at": future_time.isoformat()
    }
    post_resp = client.post("/api/v1/posts", json=post_payload, headers=owner_headers)
    assert post_resp.status_code == status.HTTP_200_OK
    post_id = post_resp.json()["id"]

    # Force time to past inside database
    past_time = datetime.utcnow() - timedelta(minutes=5)
    db_post = db.query(Post).filter(Post.id == post_id).first()
    db_post.scheduled_at = past_time
    db.commit()

    # 5. Execute worker (triggers success publication + notification creation)
    import asyncio
    asyncio.run(publish_pending_posts(db))

    # 6. Retrieve list notifications from route API
    list_resp = client.get(f"/api/v1/notifications?team_id={team_id}", headers=owner_headers)
    assert list_resp.status_code == status.HTTP_200_OK
    notifs = list_resp.json()
    assert len(notifs) == 1
    assert notifs[0]["type"] == "success"
    assert "success" in notifs[0]["title"].lower()
    success_notif_id = notifs[0]["id"]

    # 7. Schedule a second post that will fail due to connection expiry
    post_payload_2 = {
        "team_id": team_id,
        "content_text": "Post that triggers failure alerts!",
        "platform_targets": [chan_id],
        "schedule_type": "scheduled",
        "scheduled_at": future_time.isoformat()
    }
    post_resp_2 = client.post("/api/v1/posts", json=post_payload_2, headers=owner_headers)
    post_id_2 = post_resp_2.json()["id"]

    # Force schedule time to past
    db_post_2 = db.query(Post).filter(Post.id == post_id_2).first()
    db_post_2.scheduled_at = past_time
    db.commit()

    # Simulate expired channel token
    db_chan = db.query(SocialAccount).filter(SocialAccount.id == chan_id).first()
    db_chan.expires_at = datetime.utcnow() - timedelta(hours=1)
    db.commit()

    # Execute worker (triggers failed publication + notification creation)
    asyncio.run(publish_pending_posts(db))

    # 8. Retrieve notifications (expect 2 alerts)
    list_resp2 = client.get(f"/api/v1/notifications?team_id={team_id}", headers=owner_headers)
    notifs2 = list_resp2.json()
    assert len(notifs2) == 2
    
    # Sort to verify error notif (most recent)
    assert notifs2[0]["type"] == "error"
    assert "failed" in notifs2[0]["title"].lower()
    failed_notif_id = notifs2[0]["id"]

    # 9. Mark failed alert as read
    read_resp = client.post(f"/api/v1/notifications/{failed_notif_id}/read", headers=owner_headers)
    assert read_resp.status_code == status.HTTP_200_OK
    assert read_resp.json()["is_read"] is True

    # Get unread only notifications (should return only the success notification)
    unread_resp = client.get(f"/api/v1/notifications?team_id={team_id}&unread_only=True", headers=owner_headers)
    unread_notifs = unread_resp.json()
    assert len(unread_notifs) == 1
    assert unread_notifs[0]["id"] == success_notif_id

    # 10. Mark all as read
    all_read_resp = client.post(f"/api/v1/notifications/read-all?team_id={team_id}", headers=owner_headers)
    assert all_read_resp.status_code == status.HTTP_200_OK
    assert all_read_resp.json()["count"] == 1

    # Verify no unread notifications remain
    final_resp = client.get(f"/api/v1/notifications?team_id={team_id}&unread_only=True", headers=owner_headers)
    assert len(final_resp.json()) == 0
