import pytest
from datetime import datetime, timedelta
from fastapi import status
from app.database.models import Post

def test_campaign_crud_post_association_and_cleanup(client, db):
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

    # 3. Connect platform channel
    connect_resp = client.get(
        f"/api/v1/social/connect/linkedin?team_id={team_id}", 
        headers=owner_headers
    )
    res_data = connect_resp.json()
    state = res_data.get("data", {}).get("state") or res_data.get("state")
    client.post(
        "/api/v1/social/callback?platform=linkedin", 
        json={"code": "mock_code_1", "state": state, "team_id": team_id}, 
        headers=owner_headers
    )
    chan_resp = client.get(f"/api/v1/social/accounts?team_id={team_id}", headers=owner_headers)
    accounts = chan_resp.json().get("data", {}).get("accounts") or chan_resp.json()
    chan_id = accounts[0]["id"]

    # 4. Attempt creating invalid campaign dates (should fail with HTTP 400)
    today = datetime.utcnow()
    yesterday = today - timedelta(days=1)
    bad_camp_payload = {
        "team_id": team_id,
        "name": "Failed campaign date ordering",
        "start_date": today.isoformat(),
        "end_date": yesterday.isoformat()
    }
    bad_camp_resp = client.post("/api/v1/campaigns", json=bad_camp_payload, headers=owner_headers)
    assert bad_camp_resp.status_code == status.HTTP_400_BAD_REQUEST

    # 5. Create valid campaign (success)
    next_week = today + timedelta(days=7)
    camp_payload = {
        "team_id": team_id,
        "name": "Summer Launch 2026",
        "description": "Launch Digital Marketing updates",
        "start_date": today.isoformat(),
        "end_date": next_week.isoformat(),
        "budget": 5000.0,
        "objectives": "Reach 10k accounts"
    }
    camp_resp = client.post("/api/v1/campaigns", json=camp_payload, headers=owner_headers)
    assert camp_resp.status_code in (status.HTTP_200_OK, status.HTTP_201_CREATED)
    camp_res = camp_resp.json()
    camp_data = camp_res.get("data") or camp_res
    assert camp_data["name"] == "Summer Launch 2026"
    camp_id = camp_data.get("campaign_id") or camp_data.get("id")

    # 6. Schedule a post and link it to the campaign
    tomorrow = today + timedelta(days=1)
    post_payload = {
        "team_id": team_id,
        "content_text": "Linked post campaign test!",
        "platform_targets": [chan_id],
        "schedule_type": "scheduled",
        "scheduled_at": tomorrow.isoformat(),
        "campaign_id": camp_id
    }
    post_resp = client.post("/api/v1/posts", json=post_payload, headers=owner_headers)
    assert post_resp.status_code == status.HTTP_200_OK
    post_res = post_resp.json()
    post_id = post_res.get("data", {}).get("post_id") or post_res.get("id")

    # 7. Fetch campaign details and verify post is grouped
    detail_resp = client.get(f"/api/v1/campaigns/{camp_id}", headers=owner_headers)
    assert detail_resp.status_code == status.HTTP_200_OK
    detail_res = detail_resp.json()
    detail_data = detail_res.get("data") or detail_res
    assert len(detail_data["posts"]) == 1
    assert detail_data["posts"][0]["id"] == post_id

    # 8. Delete campaign
    delete_resp = client.delete(f"/api/v1/campaigns/{camp_id}", headers=owner_headers)
    assert delete_resp.status_code == status.HTTP_200_OK
    del_res = delete_resp.json()
    msg = del_res.get("message") or del_res.get("detail", "")
    assert "deleted" in msg.lower()

    # 9. Verify that post still exists but its campaign_id has been set to NULL (cascade SET NULL)
    db_post = db.query(Post).filter(Post.id == post_id).first()
    assert db_post is not None
    assert db_post.campaign_id is None

def test_campaign_outside_user_forbidden(client):
    # 1. Register/Login owner
    client.post("/api/v1/auth/register", json={
        "name": "Owner User",
        "email": "owner@socialpilot.com",
        "password": "SecurePassword123!",
        "confirm_password": "SecurePassword123!"
    })
    login_owner = client.post("/api/v1/auth/login", json={
        "email": "owner@socialpilot.com",
        "password": "SecurePassword123!"
    })
    owner_headers = {"Authorization": f"Bearer {login_owner.json()['access_token']}"}

    # Create team
    team_resp = client.post("/api/v1/teams", json={"name": "Workspace A"}, headers=owner_headers)
    team_id = team_resp.json()["id"]

    # 2. Register/Login outsider
    client.post("/api/v1/auth/register", json={
        "name": "Outside User",
        "email": "outside@socialpilot.com",
        "password": "SecurePassword123!",
        "confirm_password": "SecurePassword123!"
    })
    login_outside = client.post("/api/v1/auth/login", json={
        "email": "outside@socialpilot.com",
        "password": "SecurePassword123!"
    })
    outside_headers = {"Authorization": f"Bearer {login_outside.json()['access_token']}"}

    # 3. Outsider tries to list campaigns or create campaigns (should fail with HTTP 403)
    bad_list = client.get(f"/api/v1/campaigns?team_id={team_id}", headers=outside_headers)
    assert bad_list.status_code == status.HTTP_403_FORBIDDEN

    bad_create = client.post(
        "/api/v1/campaigns", 
        json={
            "team_id": team_id,
            "name": "Outside Campaign",
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=1)).isoformat()
        }, 
        headers=outside_headers
    )
    assert bad_create.status_code == status.HTTP_403_FORBIDDEN
