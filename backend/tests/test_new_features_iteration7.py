"""
Test suite for Iteration 7 - New Features:
1. Public Registration Page APIs
2. QR Mode (Static/Dynamic) APIs
3. Super Admin Dashboard with gym-specific accesses
4. Excel Export (frontend feature - tested via UI)
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://stripe-gym-payments.preview.emergentagent.com').rstrip('/')

# Test credentials
SUPER_ADMIN_EMAIL = "admin@gymaccess.com"
SUPER_ADMIN_PASSWORD = "admin123"
GYM_ADMIN_EMAIL = "admin@fitzone.com"
GYM_ADMIN_PASSWORD = "admin123"
GYM_ID = "efe99507-15d5-4e54-9f07-30d2507894e0"


class TestPublicRegistrationAPIs:
    """Feature 1: Public Registration Page APIs"""
    
    def test_get_gym_public_info_no_auth(self):
        """GET /api/gyms/{gym_id}/public-info should return gym info without auth"""
        response = requests.get(f"{BASE_URL}/api/gyms/{GYM_ID}/public-info")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "id" in data, "Response should contain 'id'"
        assert "name" in data, "Response should contain 'name'"
        assert "primary_color" in data, "Response should contain 'primary_color'"
        assert data["id"] == GYM_ID, f"Expected gym_id {GYM_ID}, got {data['id']}"
        print(f"✓ Public gym info: {data['name']}")
    
    def test_get_gym_public_info_invalid_gym(self):
        """GET /api/gyms/{invalid_id}/public-info should return 404"""
        response = requests.get(f"{BASE_URL}/api/gyms/invalid-gym-id/public-info")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Invalid gym returns 404")
    
    def test_get_plans_public_no_auth(self):
        """GET /api/plans/public/{gym_id} should return plans without auth"""
        response = requests.get(f"{BASE_URL}/api/plans/public/{GYM_ID}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ Public plans: {len(data)} plans found")
        
        # Verify plan structure if plans exist
        if len(data) > 0:
            plan = data[0]
            assert "id" in plan, "Plan should have 'id'"
            assert "name" in plan, "Plan should have 'name'"
            assert "price" in plan, "Plan should have 'price'"
            print(f"  - First plan: {plan['name']} - ${plan['price']}")
    
    def test_member_public_registration(self):
        """POST /api/members/register should create member and return token"""
        unique_email = f"test_register_{uuid.uuid4().hex[:8]}@test.com"
        
        payload = {
            "name": "Test Registration User",
            "email": unique_email,
            "phone": "+34 600 000 001",
            "gym_id": GYM_ID,
            "plan_id": None  # Optional plan
        }
        
        response = requests.post(f"{BASE_URL}/api/members/register", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "member" in data, "Response should contain 'member'"
        assert "token" in data, "Response should contain 'token'"
        assert "message" in data, "Response should contain 'message'"
        
        member = data["member"]
        assert member["email"] == unique_email, f"Email mismatch"
        assert member["name"] == "Test Registration User", "Name mismatch"
        assert "code" in member, "Member should have a code"
        assert len(member["code"]) == 6, "Member code should be 6 characters"
        
        print(f"✓ Member registered: {member['name']} - Code: {member['code']}")
        print(f"  - Token received: {data['token'][:20]}...")
        
        # Store for cleanup
        return member["id"]
    
    def test_member_registration_duplicate_email(self):
        """POST /api/members/register with existing email should fail"""
        # First, register a member
        unique_email = f"test_dup_{uuid.uuid4().hex[:8]}@test.com"
        
        payload = {
            "name": "First User",
            "email": unique_email,
            "gym_id": GYM_ID
        }
        
        response1 = requests.post(f"{BASE_URL}/api/members/register", json=payload)
        assert response1.status_code == 200, f"First registration failed: {response1.text}"
        
        # Try to register again with same email
        payload["name"] = "Second User"
        response2 = requests.post(f"{BASE_URL}/api/members/register", json=payload)
        assert response2.status_code == 400, f"Expected 400 for duplicate, got {response2.status_code}"
        
        print("✓ Duplicate email registration correctly rejected")
    
    def test_member_registration_with_plan(self):
        """POST /api/members/register with plan_id should create membership"""
        # First get available plans
        plans_response = requests.get(f"{BASE_URL}/api/plans/public/{GYM_ID}")
        plans = plans_response.json()
        
        if len(plans) == 0:
            pytest.skip("No plans available for testing")
        
        plan_id = plans[0]["id"]
        unique_email = f"test_plan_{uuid.uuid4().hex[:8]}@test.com"
        
        payload = {
            "name": "Test Plan User",
            "email": unique_email,
            "gym_id": GYM_ID,
            "plan_id": plan_id
        }
        
        response = requests.post(f"{BASE_URL}/api/members/register", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "membership" in data, "Response should contain 'membership'"
        
        if data["membership"]:
            assert data["membership"]["plan_id"] == plan_id, "Plan ID mismatch"
            assert data["membership"]["status"] == "active", "Membership should be active"
            print(f"✓ Member registered with plan: {plans[0]['name']}")
        else:
            print("✓ Member registered (membership may be pending payment)")


class TestQRModeAPIs:
    """Feature 2: QR Mode (Static/Dynamic) APIs"""
    
    @pytest.fixture
    def gym_admin_token(self):
        """Get gym admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": GYM_ADMIN_EMAIL,
            "password": GYM_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["token"]
    
    def test_update_gym_qr_mode_static(self, gym_admin_token):
        """PUT /api/gyms/{gym_id} with qr_mode='static' should update"""
        headers = {"Authorization": f"Bearer {gym_admin_token}"}
        
        payload = {"qr_mode": "static"}
        response = requests.put(f"{BASE_URL}/api/gyms/{GYM_ID}", json=payload, headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("qr_mode") == "static", f"QR mode should be 'static', got {data.get('qr_mode')}"
        print("✓ QR mode updated to 'static'")
    
    def test_update_gym_qr_mode_dynamic(self, gym_admin_token):
        """PUT /api/gyms/{gym_id} with qr_mode='dynamic' should update"""
        headers = {"Authorization": f"Bearer {gym_admin_token}"}
        
        payload = {"qr_mode": "dynamic"}
        response = requests.put(f"{BASE_URL}/api/gyms/{GYM_ID}", json=payload, headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("qr_mode") == "dynamic", f"QR mode should be 'dynamic', got {data.get('qr_mode')}"
        print("✓ QR mode updated to 'dynamic'")
    
    def test_qr_generate_static_mode(self, gym_admin_token):
        """GET /api/qr/generate should return static QR when gym is in static mode"""
        headers = {"Authorization": f"Bearer {gym_admin_token}"}
        
        # First set gym to static mode
        requests.put(f"{BASE_URL}/api/gyms/{GYM_ID}", json={"qr_mode": "static"}, headers=headers)
        
        # Login as a member to get member token
        # We need to find a member code first
        members_response = requests.get(f"{BASE_URL}/api/members", headers=headers)
        members = members_response.json()
        
        if len(members) == 0:
            pytest.skip("No members available for QR testing")
        
        member_code = members[0]["code"]
        
        # Login as member
        member_login = requests.post(f"{BASE_URL}/api/auth/member/login?code={member_code}")
        if member_login.status_code != 200:
            pytest.skip(f"Member login failed: {member_login.text}")
        
        member_token = member_login.json()["token"]
        member_headers = {"Authorization": f"Bearer {member_token}"}
        
        # Generate QR
        qr_response = requests.get(f"{BASE_URL}/api/qr/generate", headers=member_headers)
        assert qr_response.status_code == 200, f"QR generation failed: {qr_response.text}"
        
        qr_data = qr_response.json()
        assert "qr_code" in qr_data, "Response should contain 'qr_code'"
        assert "qr_mode" in qr_data, "Response should contain 'qr_mode'"
        assert qr_data["qr_mode"] == "static", f"Expected static mode, got {qr_data['qr_mode']}"
        assert qr_data["refresh_seconds"] == 0, "Static QR should have refresh_seconds=0"
        
        print(f"✓ Static QR generated: refresh_seconds={qr_data['refresh_seconds']}")
        
        # Reset to dynamic mode
        requests.put(f"{BASE_URL}/api/gyms/{GYM_ID}", json={"qr_mode": "dynamic"}, headers=headers)
    
    def test_qr_generate_dynamic_mode(self, gym_admin_token):
        """GET /api/qr/generate should return dynamic QR when gym is in dynamic mode"""
        headers = {"Authorization": f"Bearer {gym_admin_token}"}
        
        # Ensure gym is in dynamic mode
        requests.put(f"{BASE_URL}/api/gyms/{GYM_ID}", json={"qr_mode": "dynamic"}, headers=headers)
        
        # Get a member
        members_response = requests.get(f"{BASE_URL}/api/members", headers=headers)
        members = members_response.json()
        
        if len(members) == 0:
            pytest.skip("No members available for QR testing")
        
        member_code = members[0]["code"]
        
        # Login as member
        member_login = requests.post(f"{BASE_URL}/api/auth/member/login?code={member_code}")
        if member_login.status_code != 200:
            pytest.skip(f"Member login failed: {member_login.text}")
        
        member_token = member_login.json()["token"]
        member_headers = {"Authorization": f"Bearer {member_token}"}
        
        # Generate QR
        qr_response = requests.get(f"{BASE_URL}/api/qr/generate", headers=member_headers)
        assert qr_response.status_code == 200, f"QR generation failed: {qr_response.text}"
        
        qr_data = qr_response.json()
        assert qr_data["qr_mode"] == "dynamic", f"Expected dynamic mode, got {qr_data['qr_mode']}"
        assert qr_data["refresh_seconds"] > 0, "Dynamic QR should have refresh_seconds > 0"
        
        print(f"✓ Dynamic QR generated: refresh_seconds={qr_data['refresh_seconds']}")


class TestSuperAdminDashboard:
    """Feature 3: Super Admin Dashboard with gym-specific accesses"""
    
    @pytest.fixture
    def super_admin_token(self):
        """Get super admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["token"]
    
    def test_dashboard_stats_super_admin(self, super_admin_token):
        """GET /api/dashboard/stats should return recent_accesses_by_gym for super admin"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "recent_accesses_by_gym" in data, "Response should contain 'recent_accesses_by_gym'"
        
        # Check structure of recent_accesses_by_gym
        accesses = data["recent_accesses_by_gym"]
        assert isinstance(accesses, list), "recent_accesses_by_gym should be a list"
        
        if len(accesses) > 0:
            access = accesses[0]
            assert "gym_name" in access, "Each access should have 'gym_name'"
            print(f"✓ Super admin dashboard has gym-specific accesses: {len(accesses)} recent accesses")
            print(f"  - First access gym: {access.get('gym_name', 'N/A')}")
        else:
            print("✓ Super admin dashboard structure correct (no recent accesses)")
    
    def test_dashboard_stats_gym_admin(self):
        """GET /api/dashboard/stats for gym admin should NOT have recent_accesses_by_gym"""
        # Login as gym admin
        login_response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": GYM_ADMIN_EMAIL,
            "password": GYM_ADMIN_PASSWORD
        })
        assert login_response.status_code == 200
        token = login_response.json()["token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        # Gym admin should have empty recent_accesses_by_gym (only super admin gets enriched data)
        accesses = data.get("recent_accesses_by_gym", [])
        assert len(accesses) == 0, "Gym admin should not have recent_accesses_by_gym"
        
        print("✓ Gym admin dashboard does not have gym-specific accesses (correct)")


class TestLoginRegression:
    """Regression: Login flows"""
    
    def test_super_admin_login(self):
        """Super admin login should work"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "token" in data, "Response should contain 'token'"
        assert "admin" in data, "Response should contain 'admin'"
        assert data["admin"]["role"] == "super_admin", "Role should be super_admin"
        
        print(f"✓ Super admin login successful: {data['admin']['email']}")
    
    def test_gym_admin_login(self):
        """Gym admin login should work"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": GYM_ADMIN_EMAIL,
            "password": GYM_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "token" in data, "Response should contain 'token'"
        assert "admin" in data, "Response should contain 'admin'"
        assert data["admin"]["role"] == "gym_admin", "Role should be gym_admin"
        assert data["admin"]["gym_id"] == GYM_ID, f"Gym ID should be {GYM_ID}"
        
        print(f"✓ Gym admin login successful: {data['admin']['email']}")


class TestDeviceDeleteRegression:
    """Regression: Delete device"""
    
    @pytest.fixture
    def gym_admin_token(self):
        """Get gym admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": GYM_ADMIN_EMAIL,
            "password": GYM_ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_delete_device_endpoint_exists(self, gym_admin_token):
        """DELETE /api/devices/{device_id} endpoint should exist"""
        headers = {"Authorization": f"Bearer {gym_admin_token}"}
        
        # Create a test device
        device_payload = {
            "gym_id": GYM_ID,
            "name": "TEST_Device_Iteration7",
            "location": "Test Location"
        }
        create_response = requests.post(f"{BASE_URL}/api/devices", json=device_payload, headers=headers)
        assert create_response.status_code == 200, f"Device creation failed: {create_response.text}"
        
        device_id = create_response.json()["id"]
        
        # Delete the device
        delete_response = requests.delete(f"{BASE_URL}/api/devices/{device_id}", headers=headers)
        assert delete_response.status_code == 200, f"Device deletion failed: {delete_response.text}"
        
        print("✓ Device delete endpoint works correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
