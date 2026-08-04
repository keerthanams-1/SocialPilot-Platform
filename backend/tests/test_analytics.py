import pytest
from datetime import datetime, timedelta
from fastapi import status
from app.database.models import Post, PostMetric
from app.database.repositories import PostMetricRepository
from app.database.schemas import PostMetricCreate

def test_analytics_dashboard_aggregates_and_validation(client, db):
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

    # 4. Schedule and publish 2 posts directly in the database
    future_time = datetime.utcnow() + timedelta(days=1)
    
    post1_resp = client.post("/api/v1/posts", json={
        "team_id": team_id,
        "content_text": "Post performance leader!",
        "platform_targets": [chan_id],
        "schedule_type": "scheduled",
        "scheduled_at": future_time.isoformat()
    }, headers=owner_headers)
    post1_id = post1_resp.json()["id"]

    post2_resp = client.post("/api/v1/posts", json={
        "team_id": team_id,
        "content_text": "Post performance runner up!",
        "platform_targets": [chan_id],
        "schedule_type": "scheduled",
        "scheduled_at": future_time.isoformat()
    }, headers=owner_headers)
    post2_id = post2_resp.json()["id"]

    # Simulate post published statuses
    db_post1 = db.query(Post).filter(Post.id == post1_id).first()
    db_post2 = db.query(Post).filter(Post.id == post2_id).first()
    db_post1.status = "published"
    db_post2.status = "published"
    db.commit()

    # 5. Populate metric logs (Post 1: high stats; Post 2: medium stats)
    PostMetricRepository.create_metric(db, PostMetricCreate(
        post_id=post1_id,
        platform="linkedin",
        impressions=1000,
        clicks=100,
        engagements=50
    ))
    PostMetricRepository.create_metric(db, PostMetricCreate(
        post_id=post2_id,
        platform="linkedin",
        impressions=500,
        clicks=50,
        engagements=20
    ))

    # 6. Retrieve dashboard metrics
    dash_resp = client.get(f"/api/v1/analytics/dashboard?team_id={team_id}", headers=owner_headers)
    assert dash_resp.status_code == status.HTTP_200_OK
    dash_data = dash_resp.json()

    # 7. Assert summary aggregations
    assert dash_data["summary"]["total_impressions"] == 1500
    assert dash_data["summary"]["total_clicks"] == 150
    assert dash_data["summary"]["total_engagements"] == 70
    assert dash_data["summary"]["published_posts_count"] == 2

    # Assert platform breakdowns
    assert dash_data["platform_breakdown"]["linkedin"]["posts_count"] == 2
    assert dash_data["platform_breakdown"]["linkedin"]["impressions"] == 1500

    # Assert timeline trends
    assert len(dash_data["timeline_trends"]) == 7

    # Assert best performing post matches Post 1 (leader)
    assert dash_data["best_performing_post"]["id"] == post1_id
    assert dash_data["best_performing_post"]["engagements"] == 50

def test_analytics_forbidden_outside_user(client):
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

    # 3. Requesting dashboard should fail with HTTP 403
    bad_resp = client.get(f"/api/v1/analytics/dashboard?team_id={team_id}", headers=outside_headers)
    assert bad_resp.status_code == status.HTTP_403_FORBIDDEN
