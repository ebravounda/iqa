"""
Iteration 30 Tests - QR Code, JWT Token, and PWA Login Changes
Tests:
1. JWT token expiration is now 30 days (720 hours)
2. /me endpoint returns fresh token for silent refresh
3. Admin login works correctly
4. Member login with invalid code returns error
5. Member login with blocked account returns blocked error
"""
import pytest
import requests
import os
import jwt
from datetime import datetime, timezone

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestJWTExpiration:
    """Test JWT token expiration is 30 days"""
    
    def test_admin_login_returns_valid_token(self):
        """Admin login should return a valid JWT token"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": "admin@gymaccess.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        
        data = response.json()
        assert "token" in data, "Token not in response"
        assert "admin" in data, "Admin data not in response"
        
        # Decode token to check expiration (without verification)
        token = data["token"]
        decoded = jwt.decode(token, options={"verify_signature": False})
        
        assert "exp" in decoded, "Token missing expiration"
        assert "sub" in decoded, "Token missing subject"
        
        # Check expiration is approximately 30 days from now
        exp_timestamp = decoded["exp"]
        now = datetime.now(timezone.utc).timestamp()
        days_until_expiry = (exp_timestamp - now) / (24 * 60 * 60)
        
        print(f"Token expires in {days_until_expiry:.1f} days")
        
        # Should be between 29 and 31 days (allowing for test execution time)
        assert 29 <= days_until_expiry <= 31, f"Token expiration should be ~30 days, got {days_until_expiry:.1f} days"
        print("SUCCESS: JWT token expiration is correctly set to ~30 days")


class TestMemberMeEndpoint:
    """Test /me endpoint returns fresh token"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token for creating test member"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": "admin@gymaccess.com",
            "password": "admin123"
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin login failed")
    
    def test_me_endpoint_returns_fresh_token(self, admin_token):
        """Test that /me endpoint returns a fresh token for silent refresh"""
        # First, we need a member to test with
        # Get list of gyms to find one with members
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        gyms_response = requests.get(f"{BASE_URL}/api/gyms", headers=headers)
        if gyms_response.status_code != 200 or not gyms_response.json():
            pytest.skip("No gyms available for testing")
        
        gym = gyms_response.json()[0]
        gym_id = gym["id"]
        
        # Get members for this gym
        members_response = requests.get(f"{BASE_URL}/api/members?gym_id={gym_id}", headers=headers)
        if members_response.status_code != 200:
            pytest.skip("Could not fetch members")
        
        members = members_response.json()
        if not members:
            pytest.skip("No members available for testing")
        
        # Find an active member
        active_member = None
        for m in members:
            if m.get("status") in ["active", "pending"]:
                active_member = m
                break
        
        if not active_member:
            pytest.skip("No active members available")
        
        # Login as member
        member_code = active_member["code"]
        login_response = requests.post(f"{BASE_URL}/api/auth/member/login?code={member_code}")
        
        if login_response.status_code != 200:
            pytest.skip(f"Member login failed: {login_response.text}")
        
        member_token = login_response.json().get("token")
        assert member_token, "No token in member login response"
        
        # Call /me endpoint
        me_headers = {"Authorization": f"Bearer {member_token}"}
        me_response = requests.get(f"{BASE_URL}/api/auth/member/me", headers=me_headers)
        
        assert me_response.status_code == 200, f"/me endpoint failed: {me_response.text}"
        
        me_data = me_response.json()
        assert "member" in me_data, "Member data not in /me response"
        assert "gym" in me_data, "Gym data not in /me response"
        assert "token" in me_data, "Fresh token not in /me response - CRITICAL: Silent refresh not working"
        
        # Verify the new token is valid and has correct expiration
        new_token = me_data["token"]
        decoded = jwt.decode(new_token, options={"verify_signature": False})
        
        exp_timestamp = decoded["exp"]
        now = datetime.now(timezone.utc).timestamp()
        days_until_expiry = (exp_timestamp - now) / (24 * 60 * 60)
        
        print(f"Fresh token from /me expires in {days_until_expiry:.1f} days")
        assert 29 <= days_until_expiry <= 31, f"Fresh token should have ~30 day expiry"
        
        print("SUCCESS: /me endpoint returns fresh token for silent refresh")


class TestMemberLoginErrors:
    """Test member login error handling"""
    
    def test_invalid_code_returns_404(self):
        """Invalid member code should return 404"""
        response = requests.post(f"{BASE_URL}/api/auth/member/login?code=INVALID")
        
        assert response.status_code == 404, f"Expected 404 for invalid code, got {response.status_code}"
        
        data = response.json()
        assert "detail" in data, "Error detail not in response"
        print(f"Invalid code error message: {data['detail']}")
        print("SUCCESS: Invalid code returns 404 with error message")
    
    def test_blocked_account_returns_403(self):
        """Blocked member account should return 403 with 'Cuenta bloqueada'"""
        # This test requires a blocked member to exist
        # We'll create one using admin API
        
        # Get admin token
        admin_response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": "admin@gymaccess.com",
            "password": "admin123"
        })
        
        if admin_response.status_code != 200:
            pytest.skip("Admin login failed")
        
        admin_token = admin_response.json().get("token")
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Get a gym
        gyms_response = requests.get(f"{BASE_URL}/api/gyms", headers=headers)
        if gyms_response.status_code != 200 or not gyms_response.json():
            pytest.skip("No gyms available")
        
        gym_id = gyms_response.json()[0]["id"]
        
        # Create a test member that we'll block
        import uuid
        test_code = f"BLK{str(uuid.uuid4())[:3].upper()}"
        
        create_response = requests.post(f"{BASE_URL}/api/members", headers=headers, json={
            "name": "TEST_Blocked Member",
            "code": test_code,
            "gym_id": gym_id,
            "status": "blocked",
            "email": f"blocked_{test_code.lower()}@test.com"
        })
        
        if create_response.status_code not in [200, 201]:
            # Try to find an existing blocked member
            members_response = requests.get(f"{BASE_URL}/api/members?gym_id={gym_id}", headers=headers)
            if members_response.status_code == 200:
                for m in members_response.json():
                    if m.get("status") == "blocked":
                        test_code = m["code"]
                        break
                else:
                    pytest.skip("Could not create or find blocked member")
            else:
                pytest.skip("Could not create blocked member")
        
        # Try to login with blocked member
        login_response = requests.post(f"{BASE_URL}/api/auth/member/login?code={test_code}")
        
        # Should return 403 with "Cuenta bloqueada"
        if login_response.status_code == 403:
            data = login_response.json()
            assert "bloqueada" in data.get("detail", "").lower() or "blocked" in data.get("detail", "").lower(), \
                f"Expected 'bloqueada' in error message, got: {data.get('detail')}"
            print(f"Blocked account error message: {data['detail']}")
            print("SUCCESS: Blocked account returns 403 with correct message")
        elif login_response.status_code == 404:
            # Member might not have been created
            pytest.skip("Blocked member not found")
        else:
            pytest.fail(f"Expected 403 for blocked account, got {login_response.status_code}: {login_response.text}")
        
        # Cleanup - delete test member
        if create_response.status_code in [200, 201]:
            member_id = create_response.json().get("id")
            if member_id:
                requests.delete(f"{BASE_URL}/api/members/{member_id}", headers=headers)


class TestAdminLogin:
    """Test admin login functionality"""
    
    def test_admin_login_success(self):
        """Admin login with correct credentials should succeed"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": "admin@gymaccess.com",
            "password": "admin123"
        })
        
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        
        data = response.json()
        assert "token" in data, "Token not in response"
        assert "admin" in data, "Admin data not in response"
        assert data["admin"]["email"] == "admin@gymaccess.com", "Email mismatch"
        
        print("SUCCESS: Admin login works correctly")
    
    def test_admin_login_invalid_credentials(self):
        """Admin login with wrong password should fail"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": "admin@gymaccess.com",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401, f"Expected 401 for invalid credentials, got {response.status_code}"
        print("SUCCESS: Invalid admin credentials return 401")


class TestQRCodeEndpoint:
    """Test QR code generation endpoint"""
    
    @pytest.fixture
    def member_token(self):
        """Get a member token for QR testing"""
        # Get admin token first
        admin_response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": "admin@gymaccess.com",
            "password": "admin123"
        })
        
        if admin_response.status_code != 200:
            pytest.skip("Admin login failed")
        
        admin_token = admin_response.json().get("token")
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Get a gym with members
        gyms_response = requests.get(f"{BASE_URL}/api/gyms", headers=headers)
        if gyms_response.status_code != 200 or not gyms_response.json():
            pytest.skip("No gyms available")
        
        gym_id = gyms_response.json()[0]["id"]
        
        # Get members
        members_response = requests.get(f"{BASE_URL}/api/members?gym_id={gym_id}", headers=headers)
        if members_response.status_code != 200 or not members_response.json():
            pytest.skip("No members available")
        
        # Find active member
        for m in members_response.json():
            if m.get("status") in ["active", "pending"]:
                login_response = requests.post(f"{BASE_URL}/api/auth/member/login?code={m['code']}")
                if login_response.status_code == 200:
                    return login_response.json().get("token")
        
        pytest.skip("No active member found")
    
    def test_qr_generation(self, member_token):
        """Test QR code generation endpoint"""
        headers = {"Authorization": f"Bearer {member_token}"}
        
        response = requests.get(f"{BASE_URL}/api/qr/generate", headers=headers)
        
        assert response.status_code == 200, f"QR generation failed: {response.text}"
        
        data = response.json()
        assert "qr_code" in data, "qr_code not in response"
        assert "expires_at" in data, "expires_at not in response"
        assert "refresh_seconds" in data, "refresh_seconds not in response"
        
        print(f"QR code generated: {data['qr_code'][:20]}...")
        print(f"QR mode: {data.get('qr_mode', 'dynamic')}")
        print(f"Refresh seconds: {data['refresh_seconds']}")
        print("SUCCESS: QR code generation works")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
