import pytest
from fastapi import status
from app.database.models import SocialAccount
from app.core.crypto import decrypt_token

def test_social_account_connect_and_disconnect(client, db):
    # 1. Register and login team owner
    client.post("/api/v1/auth/register", json={
        "name": "Owner User",
        "email": "owner@socialpilot.com",
        "password": "SecurePassword123!",
        "confirm_password": "SecurePassword123!",
        "role_name": "Administrator"
    })
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "owner@socialpilot.com",
        "password": "SecurePassword123!"
    })
    owner_token = login_resp.json()["access_token"]
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    # 2. Create a team workspace
    team_resp = client.post("/api/v1/teams", json={"name": "Social Team Workspace"}, headers=owner_headers)
    assert team_resp.status_code == status.HTTP_201_CREATED
    team_id = team_resp.json()["id"]

    # 3. Call connect to generate redirect parameters
    connect_resp = client.get(
        f"/api/v1/social/connect/linkedin?team_id={team_id}", 
        headers=owner_headers
    )
    assert connect_resp.status_code == status.HTTP_200_OK
    connect_data = connect_resp.json()
    assert connect_data["platform"] == "linkedin"
    state = connect_data["state"]

    # 4. Process OAuth callback exchange
    callback_payload = {
        "code": "mock_auth_code_987abc",
        "state": state,
        "team_id": team_id
    }
    callback_resp = client.post(
        "/api/v1/social/callback?platform=linkedin", 
        json=callback_payload, 
        headers=owner_headers
    )
    assert callback_resp.status_code == status.HTTP_200_OK
    callback_data = callback_resp.json()
    assert callback_data["platform"] == "linkedin"
    assert callback_data["status"] == "connected"
    account_id = callback_data["id"]

    # 5. Direct DB Check - Verify that access_token is encrypted
    # Query database directly bypassing the repository mapping
    db_record = db.query(SocialAccount).filter(SocialAccount.id == account_id).first()
    assert db_record is not None
    # Token must be stored encrypted (should not start with 'mock_access_token_')
    assert db_record.access_token != "mock_access_token_"
    # Verify decrypt restores the plain mock token
    decrypted = decrypt_token(db_record.access_token)
    assert decrypted.startswith("mock_access_token_")

    # 6. Test Quota Decrement & Custom Response Headers
    api_call_resp = client.post(
        f"/api/v1/social/accounts/{account_id}/trigger-api-call",
        headers=owner_headers
    )
    assert api_call_resp.status_code == status.HTTP_200_OK
    assert api_call_resp.json()["remaining_quota"] == 99
    # Check rate limit headers
    assert api_call_resp.headers["X-RateLimit-Limit"] == "100"
    assert api_call_resp.headers["X-RateLimit-Remaining"] == "99"
    assert api_call_resp.headers["X-RateLimit-Reset"] == "60"

    # 7. Test Expiration Simulation and Expiry Check
    expiry_resp = client.post(
        f"/api/v1/social/accounts/{account_id}/simulate-expiry",
        headers=owner_headers
    )
    assert expiry_resp.status_code == status.HTTP_200_OK
    assert expiry_resp.json()["status"] == "expired"

    # 8. Post-Expiry API Call failure (401 Unauthorized)
    expired_api_call = client.post(
        f"/api/v1/social/accounts/{account_id}/trigger-api-call",
        headers=owner_headers
    )
    assert expired_api_call.status_code == status.HTTP_401_UNAUTHORIZED
    assert "expired" in expired_api_call.json()["detail"].lower()

    # 9. Disconnect channel
    delete_resp = client.delete(
        f"/api/v1/social/accounts/{account_id}", 
        headers=owner_headers
    )
    assert delete_resp.status_code == status.HTTP_200_OK
    assert "disconnected successfully" in delete_resp.json()["detail"]

def test_social_account_non_member_forbidden(client):
    # 1. Register and login owner
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

    # 2. Register and login a separate user who is not a member of Workspace A
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

    # 3. Outside user tries to initiate connection to Workspace A (should fail)
    bad_connect = client.get(
        f"/api/v1/social/connect/facebook?team_id={team_id}", 
        headers=outside_headers
    )
    assert bad_connect.status_code == status.HTTP_403_FORBIDDEN
    assert "must be a member" in bad_connect.json()["detail"]

    # 4. Outside user tries to post callback (should fail)
    bad_callback = client.post(
        "/api/v1/social/callback?platform=facebook",
        json={"code": "mock_code", "state": "mock_state", "team_id": team_id},
        headers=outside_headers
    )
    assert bad_callback.status_code == status.HTTP_403_FORBIDDEN

    # 5. Outside user tries to list accounts (should fail)
    bad_list = client.get(
        f"/api/v1/social/accounts?team_id={team_id}",
        headers=outside_headers
    )
    assert bad_list.status_code == status.HTTP_403_FORBIDDEN
