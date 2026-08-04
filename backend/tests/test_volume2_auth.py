import pytest

def test_volume2_registration_and_login_flow(client):
    """Verify Volume 2 registration with password strength, login, profile, and logout."""
    reg_payload = {
        "email": "volume2_user@socialpilot.com",
        "username": "volume2_user",
        "password": "ProductionPassword123!",
        "confirm_password": "ProductionPassword123!",
        "full_name": "Volume 2 Test User",
        "role_name": "Marketing Specialist"
    }

    # 1. Register new user
    reg_resp = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_resp.status_code == 201
    user_data = reg_resp.json()
    assert user_data["email"] == "volume2_user@socialpilot.com"
    assert user_data["username"] == "volume2_user"
    assert user_data["role_name"] == "Marketing Specialist"

    # 2. Login
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "volume2_user@socialpilot.com",
        "password": "ProductionPassword123!"
    })
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    assert "access_token" in token_data
    assert "refresh_token" in token_data
    access_token = token_data["access_token"]
    refresh_token = token_data["refresh_token"]

    # 3. Get profile via Bearer header
    profile_resp = client.get(
        "/api/v1/users/profile",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert profile_resp.status_code == 200
    profile_data = profile_resp.json()
    assert profile_data["email"] == "volume2_user@socialpilot.com"

    # 4. Update profile
    update_resp = client.put(
        "/api/v1/users/profile",
        json={"phone": "+1-555-0199", "timezone": "America/New_York"},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["phone"] == "+1-555-0199"

    # 5. List active sessions
    sessions_resp = client.get(
        "/api/v1/users/sessions",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert sessions_resp.status_code == 200
    sessions = sessions_resp.json()
    assert len(sessions) >= 1
    session_id = sessions[0]["id"]

    # 6. Perform Refresh Token Rotation (RTR)
    client.cookies.set("refresh_token", refresh_token)
    refresh_resp = client.post("/api/v1/auth/refresh")
    assert refresh_resp.status_code == 200
    new_tokens = refresh_resp.json()
    assert new_tokens["access_token"] != access_token

    # 7. RTR Security Breach Detection: Reusing old refresh token must trigger 401
    client.cookies.set("refresh_token", refresh_token)
    reuse_resp = client.post("/api/v1/auth/refresh")
    assert reuse_resp.status_code == 401

    # 8. Revoke device session
    del_resp = client.delete(
        f"/api/v1/users/sessions/{session_id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert del_resp.status_code == 200

    # 9. Clean logout
    logout_resp = client.post("/api/v1/auth/logout")
    assert logout_resp.status_code == 200

def test_volume2_password_reset_and_verification(client):
    """Verify password reset request & email verification token endpoints."""
    # 1. Register a user first
    reg_payload = {
        "email": "reset_test@socialpilot.com",
        "username": "reset_user",
        "password": "InitialPassword123!",
        "confirm_password": "InitialPassword123!",
        "full_name": "Reset User"
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    # 2. Request forgot password
    forgot_resp = client.post("/api/v1/auth/forgot-password", json={"email": "reset_test@socialpilot.com"})
    assert forgot_resp.status_code == 200
    reset_token = forgot_resp.json().get("reset_token")
    assert reset_token is not None

    # 3. Reset password
    reset_resp = client.post("/api/v1/auth/reset-password", json={
        "token": reset_token,
        "new_password": "NewSecretPassword123!",
        "confirm_password": "NewSecretPassword123!"
    })
    assert reset_resp.status_code == 200

    # 4. Verify login works with new password
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "reset_test@socialpilot.com",
        "password": "NewSecretPassword123!"
    })
    assert login_resp.status_code == 200
