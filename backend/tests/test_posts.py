import pytest
from datetime import datetime, timedelta
from fastapi import status

def test_post_scheduling_validation_and_publishing(client):
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

    # 3. Connect mock LinkedIn platform channel
    connect_resp = client.get(
        f"/api/v1/social/connect/linkedin?team_id={team_id}", 
        headers=owner_headers
    )
    state = connect_resp.json()["state"]
    callback_payload = {
        "code": "mock_code_1",
        "state": state,
        "team_id": team_id
    }
    chan_resp = client.post(
        "/api/v1/social/callback?platform=linkedin", 
        json=callback_payload, 
        headers=owner_headers
    )
    chan_id = chan_resp.json()["id"]

    # 4. Attempt scheduling post in the past (should fail with HTTP 400)
    past_time = (datetime.utcnow() - timedelta(hours=1)).isoformat()
    bad_post_payload = {
        "team_id": team_id,
        "content_text": "Failed past schedule test",
        "platform_targets": [chan_id],
        "schedule_type": "scheduled",
        "scheduled_at": past_time
      }
    bad_resp = client.post("/api/v1/posts", json=bad_post_payload, headers=owner_headers)
    assert bad_resp.status_code == status.HTTP_400_BAD_REQUEST
    assert "cannot be set in the past" in bad_resp.json()["detail"]

    # 5. Schedule valid post for tomorrow (success)
    tomorrow_time = (datetime.utcnow() + timedelta(days=1)).isoformat()
    post_payload = {
        "team_id": team_id,
        "content_text": "Checking content scheduler validations!",
        "media_urls": ["https://images.unsplash.com/photo-1579546929518-9e396f3cc809"],
        "platform_targets": [chan_id],
        "schedule_type": "scheduled",
        "scheduled_at": tomorrow_time
    }
    post_resp = client.post("/api/v1/posts", json=post_payload, headers=owner_headers)
    assert post_resp.status_code == status.HTTP_200_OK
    post_data = post_resp.json()
    assert post_data["status"] == "scheduled"
    assert post_data["content_text"] == "Checking content scheduler validations!"
    assert post_data["media_urls"] == ["https://images.unsplash.com/photo-1579546929518-9e396f3cc809"]
    post_id = post_data["id"]

    # 6. Query workspace posts filtering by status
    list_resp = client.get(
        f"/api/v1/posts?team_id={team_id}&status=scheduled", 
        headers=owner_headers
    )
    assert list_resp.status_code == status.HTTP_200_OK
    assert len(list_resp.json()) == 1
    assert list_resp.json()[0]["id"] == post_id

    # 7. Publish valid post instantly (success status)
    pub_resp = client.post(f"/api/v1/posts/{post_id}/publish", headers=owner_headers)
    assert pub_resp.status_code == status.HTTP_200_OK
    assert pub_resp.json()["status"] == "published"

    # 8. Create another scheduled post
    post_payload2 = {
        "team_id": team_id,
        "content_text": "Failed connection link test",
        "platform_targets": [chan_id],
        "schedule_type": "scheduled",
        "scheduled_at": tomorrow_time
    }
    post_resp2 = client.post("/api/v1/posts", json=post_payload2, headers=owner_headers)
    post_id2 = post_resp2.json()["id"]

    # 9. Force connection token expiration
    client.post(f"/api/v1/social/accounts/{chan_id}/simulate-expiry", headers=owner_headers)

    # 10. Attempt publishing post with expired targets (must fail with HTTP 400 & status fail)
    failed_pub_resp = client.post(f"/api/v1/posts/{post_id2}/publish", headers=owner_headers)
    assert failed_pub_resp.status_code == status.HTTP_400_BAD_REQUEST
    assert "expired" in failed_pub_resp.json()["detail"].lower()

    # Verify status changed to failed in database
    chk_resp = client.get(f"/api/v1/posts?team_id={team_id}&status=failed", headers=owner_headers)
    assert len(chk_resp.json()) == 1
    assert chk_resp.json()[0]["id"] == post_id2
