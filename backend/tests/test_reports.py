import pytest
from datetime import datetime, timedelta
from fastapi import status

def test_reports_csv_export_endpoint(client, db):
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
    chan_name = chan_resp.json()[0]["account_name"]

    # 4. Schedule a post
    future_time = datetime.utcnow() + timedelta(days=1)
    post_payload = {
        "team_id": team_id,
        "content_text": "CSV log post dispatch test content!",
        "platform_targets": [chan_id],
        "schedule_type": "scheduled",
        "scheduled_at": future_time.isoformat()
    }
    post_resp = client.post("/api/v1/posts", json=post_payload, headers=owner_headers)
    assert post_resp.status_code == status.HTTP_200_OK

    # 5. Call export-csv endpoint
    csv_resp = client.get(f"/api/v1/analytics/export-csv?team_id={team_id}", headers=owner_headers)
    assert csv_resp.status_code == status.HTTP_200_OK
    assert "text/csv" in csv_resp.headers["content-type"]
    assert "attachment" in csv_resp.headers["content-disposition"]
    
    # Assert CSV text data mapping content
    csv_text = csv_resp.text
    assert "SOCIALPILOT WORKSPACE ANALYTICS REPORT" in csv_text
    assert team_id in csv_text
    assert chan_name in csv_text
    assert "CSV log post dispatch test content!" in csv_text

def test_reports_csv_export_unauthorized_user(client):
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

    # 3. Requesting CSV export should return 403 Forbidden
    bad_resp = client.get(f"/api/v1/analytics/export-csv?team_id={team_id}", headers=outside_headers)
    assert bad_resp.status_code == status.HTTP_403_FORBIDDEN
