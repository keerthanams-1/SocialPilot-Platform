import pytest
from fastapi import status

def test_user_registration_and_duplicate_email(client):
    # 1. Register a new user
    register_payload = {
        "name": "Alice Developer",
        "email": "alice@socialpilot.com",
        "password": "SecurePassword123!",
        "confirm_password": "SecurePassword123!",
        "phone": "+1555123456",
        "role_name": "Content Creator"
    }
    response = client.post("/api/v1/auth/register", json=register_payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == "alice@socialpilot.com"
    assert data["name"] == "Alice Developer"
    assert "password_hash" not in data

    # 2. Try registering with same email again
    response_dup = client.post("/api/v1/auth/register", json=register_payload)
    assert response_dup.status_code == status.HTTP_400_BAD_REQUEST
    assert "already registered" in response_dup.json()["detail"]

def test_user_login_success_and_failure(client):
    # Register user first
    register_payload = {
        "name": "Bob Marketer",
        "email": "bob@socialpilot.com",
        "password": "SecurePassword123!",
        "confirm_password": "SecurePassword123!",
        "role_name": "Marketing Team"
    }
    client.post("/api/v1/auth/register", json=register_payload)

    # 1. Login with incorrect password
    response_fail = client.post("/api/v1/auth/login", json={
        "email": "bob@socialpilot.com",
        "password": "WrongPassword!"
    })
    assert response_fail.status_code == status.HTTP_400_BAD_REQUEST
    assert "Incorrect email or password" in response_fail.json()["detail"]

    # 2. Login successfully
    response_success = client.post("/api/v1/auth/login", json={
        "email": "bob@socialpilot.com",
        "password": "SecurePassword123!"
    })
    assert response_success.status_code == status.HTTP_200_OK
    data = response_success.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    
    # Assert HttpOnly cookies are set
    cookies = response_success.cookies
    assert "access_token" in cookies
    assert "refresh_token" in cookies

def test_profile_retrieval_and_updates(client):
    # Register and login
    register_payload = {
        "name": "Charlie Manager",
        "email": "charlie@socialpilot.com",
        "password": "SecurePassword123!",
        "confirm_password": "SecurePassword123!",
        "role_name": "Business User"
    }
    client.post("/api/v1/auth/register", json=register_payload)
    
    login_response = client.post("/api/v1/auth/login", json={
        "email": "charlie@socialpilot.com",
        "password": "SecurePassword123!"
    })
    access_token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # 1. Retrieve profile
    profile_response = client.get("/api/v1/profile", headers=headers)
    assert profile_response.status_code == status.HTTP_200_OK
    assert profile_response.json()["name"] == "Charlie Manager"
    assert profile_response.json()["role"]["name"] == "Business User"

    # 2. Update profile name and phone
    update_response = client.put("/api/v1/profile", json={
        "name": "Charlie Updated",
        "phone": "+9999999"
    }, headers=headers)
    assert update_response.status_code == status.HTTP_200_OK
    assert update_response.json()["name"] == "Charlie Updated"
    assert update_response.json()["phone"] == "+9999999"

    # 3. Change password
    pwd_response = client.put("/api/v1/profile/change-password", json={
        "old_password": "SecurePassword123!",
        "new_password": "NewSecretPassword123!",
        "confirm_new_password": "NewSecretPassword123!"
    }, headers=headers)
    assert pwd_response.status_code == status.HTTP_200_OK
    assert "Password successfully updated" in pwd_response.json()["detail"]

def test_refresh_token_rotation_and_logout(client):
    # Register & Login
    register_payload = {
        "name": "RTR Test User",
        "email": "rtr@socialpilot.com",
        "password": "SecurePassword123!",
        "confirm_password": "SecurePassword123!",
        "role_name": "Content Creator"
    }
    client.post("/api/v1/auth/register", json=register_payload)
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "rtr@socialpilot.com",
        "password": "SecurePassword123!"
    })
    refresh_token = login_resp.json()["refresh_token"]

    # 1. Trigger token refresh (using cookie simulation via Bearer header or cookies dict)
    client.cookies.set("refresh_token", refresh_token)
    refresh_resp = client.post("/api/v1/auth/refresh-token")
    assert refresh_resp.status_code == status.HTTP_200_OK
    new_data = refresh_resp.json()
    assert "access_token" in new_data
    assert "refresh_token" in new_data
    
    new_refresh = new_data["refresh_token"]
    assert new_refresh != refresh_token  # Verified Token Rotation!

    # 2. Try reusing the old refresh token (should trigger RTR security block)
    client.cookies.set("refresh_token", refresh_token)
    reuse_resp = client.post("/api/v1/auth/refresh-token")
    assert reuse_resp.status_code == status.HTTP_401_UNAUTHORIZED
    assert "reuse detected" in reuse_resp.json()["detail"].lower()

    # 3. Verify new refresh token is also revoked because reuse revoked all sessions
    client.cookies.set("refresh_token", new_refresh)
    revoked_resp = client.post("/api/v1/auth/refresh-token")
    assert revoked_resp.status_code == status.HTTP_401_UNAUTHORIZED

def test_team_workspace_and_member_flows(client):
    # Register owner and member
    client.post("/api/v1/auth/register", json={
        "name": "Owner User",
        "email": "owner@socialpilot.com",
        "password": "SecurePassword123!",
        "confirm_password": "SecurePassword123!",
        "role_name": "Administrator"
    })
    client.post("/api/v1/auth/register", json={
        "name": "Invited User",
        "email": "invited@socialpilot.com",
        "password": "SecurePassword123!",
        "confirm_password": "SecurePassword123!",
        "role_name": "Content Creator"
    })

    # Login owner
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "owner@socialpilot.com",
        "password": "SecurePassword123!"
    })
    owner_token = login_resp.json()["access_token"]
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    # 1. Create a Team
    team_resp = client.post("/api/v1/teams", json={"name": "SaaS Launch Team"}, headers=owner_headers)
    assert team_resp.status_code == status.HTTP_201_CREATED
    team_data = team_resp.json()
    team_id = team_data["id"]
    assert team_data["name"] == "SaaS Launch Team"
    
    # Assert owner is automatically mapped inside memberships
    assert len(team_data["members"]) == 1
    assert team_data["members"][0]["role_in_team"] == "owner"

    # 2. Invite a member
    invite_resp = client.post(
        f"/api/v1/teams/{team_id}/members", 
        json={"email": "invited@socialpilot.com", "role_in_team": "Marketing Team"}, 
        headers=owner_headers
    )
    assert invite_resp.status_code == status.HTTP_201_CREATED
    assert invite_resp.json()["email"] == "invited@socialpilot.com"
    assert invite_resp.json()["role_in_team"] == "Marketing Team"
    invited_id = invite_resp.json()["user_id"]

    # 3. Remove the member
    remove_resp = client.delete(
        f"/api/v1/teams/{team_id}/members/{invited_id}", 
        headers=owner_headers
    )
    assert remove_resp.status_code == status.HTTP_200_OK
    assert "removed from team successfully" in remove_resp.json()["detail"]
