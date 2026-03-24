"""
Test file for Bug Fixes - Iteration 6
Tests the following bugs:
1. Login flow (super admin and gym admin)
2. Impersonation flow
3. Configuration Save (GymUpdate with filtered empty strings)
4. Stripe Config Save
5. Delete Device endpoint
6. Access log export ordering (timestamp ascending)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
SUPER_ADMIN_EMAIL = "admin@gymaccess.com"
SUPER_ADMIN_PASSWORD = "admin123"
GYM_ADMIN_EMAIL = "admin@fitzone.com"
GYM_ADMIN_PASSWORD = "admin123"
FITZONE_GYM_ID = "efe99507-15d5-4e54-9f07-30d2507894e0"
MEMBER_CODE = "LRF4HL"


class TestAuthLogin:
    """Bug 1: Test login flows for super admin and gym admin"""
    
    def test_super_admin_login(self):
        """Super admin login should work and return token"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Super admin login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in response"
        assert "admin" in data, "No admin in response"
        assert data["admin"]["role"] == "super_admin", f"Expected super_admin role, got {data['admin']['role']}"
        print(f"✓ Super admin login successful, role: {data['admin']['role']}")
    
    def test_gym_admin_login(self):
        """Gym admin login should work and return token with gym_id"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": GYM_ADMIN_EMAIL,
            "password": GYM_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Gym admin login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in response"
        assert "admin" in data, "No admin in response"
        assert data["admin"]["role"] == "gym_admin", f"Expected gym_admin role, got {data['admin']['role']}"
        assert data["admin"]["gym_id"] == FITZONE_GYM_ID, f"Expected gym_id {FITZONE_GYM_ID}, got {data['admin'].get('gym_id')}"
        print(f"✓ Gym admin login successful, gym_id: {data['admin']['gym_id']}")
    
    def test_invalid_login(self):
        """Invalid credentials should return 401"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": "invalid@test.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Invalid login correctly returns 401")


class TestImpersonation:
    """Bug 1: Test impersonation flow"""
    
    @pytest.fixture
    def super_admin_token(self):
        """Get super admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    @pytest.fixture
    def gym_admin_token(self):
        """Get gym admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": GYM_ADMIN_EMAIL,
            "password": GYM_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    def test_super_admin_can_impersonate(self, super_admin_token):
        """Super admin should be able to impersonate a gym"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        response = requests.post(
            f"{BASE_URL}/api/auth/admin/impersonate/{FITZONE_GYM_ID}",
            headers=headers
        )
        assert response.status_code == 200, f"Impersonation failed: {response.text}"
        data = response.json()
        assert "token" in data, "No impersonation token"
        assert "admin" in data, "No admin data"
        assert data["admin"]["impersonating"] == True, "impersonating flag not set"
        assert data["admin"]["gym_id"] == FITZONE_GYM_ID, "gym_id not set correctly"
        assert data["admin"]["role"] == "gym_admin", "role not changed to gym_admin"
        print(f"✓ Impersonation successful, gym_id: {data['admin']['gym_id']}")
        return data["token"]
    
    def test_impersonation_token_scoped_to_gym(self, super_admin_token):
        """Impersonation token should be scoped to the gym"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        response = requests.post(
            f"{BASE_URL}/api/auth/admin/impersonate/{FITZONE_GYM_ID}",
            headers=headers
        )
        assert response.status_code == 200
        impersonation_token = response.json()["token"]
        
        # Use impersonation token to get members - should only return FitZone members
        headers = {"Authorization": f"Bearer {impersonation_token}"}
        response = requests.get(f"{BASE_URL}/api/members", headers=headers)
        assert response.status_code == 200
        members = response.json()
        # All members should belong to FitZone
        for member in members:
            assert member["gym_id"] == FITZONE_GYM_ID, f"Member {member['id']} has wrong gym_id"
        print(f"✓ Impersonation token correctly scoped, {len(members)} members returned")
    
    def test_gym_admin_cannot_impersonate(self, gym_admin_token):
        """Gym admin should NOT be able to impersonate"""
        headers = {"Authorization": f"Bearer {gym_admin_token}"}
        response = requests.post(
            f"{BASE_URL}/api/auth/admin/impersonate/{FITZONE_GYM_ID}",
            headers=headers
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✓ Gym admin correctly denied impersonation (403)")
    
    def test_impersonate_nonexistent_gym(self, super_admin_token):
        """Impersonating non-existent gym should return 404"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        response = requests.post(
            f"{BASE_URL}/api/auth/admin/impersonate/nonexistent-gym-id",
            headers=headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Non-existent gym impersonation correctly returns 404")


class TestConfigurationSave:
    """Bug 2: Test configuration save with filtered empty strings"""
    
    @pytest.fixture
    def gym_admin_token(self):
        """Get gym admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": GYM_ADMIN_EMAIL,
            "password": GYM_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    def test_update_gym_with_valid_data(self, gym_admin_token):
        """Update gym with valid data should succeed"""
        headers = {"Authorization": f"Bearer {gym_admin_token}"}
        
        # Update with valid data (no empty strings)
        update_data = {
            "qr_refresh_seconds": 15,
            "primary_color": "#FF6B6B"
        }
        response = requests.put(
            f"{BASE_URL}/api/gyms/{FITZONE_GYM_ID}",
            json=update_data,
            headers=headers
        )
        assert response.status_code == 200, f"Update failed: {response.text}"
        data = response.json()
        assert data["qr_refresh_seconds"] == 15, "qr_refresh_seconds not updated"
        assert data["primary_color"] == "#FF6B6B", "primary_color not updated"
        print("✓ Gym update with valid data successful")
        
        # Restore original values
        restore_data = {
            "qr_refresh_seconds": 10,
            "primary_color": "#E1FF01"
        }
        requests.put(f"{BASE_URL}/api/gyms/{FITZONE_GYM_ID}", json=restore_data, headers=headers)
    
    def test_update_gym_empty_data_rejected(self, gym_admin_token):
        """Update gym with no data should return 400"""
        headers = {"Authorization": f"Bearer {gym_admin_token}"}
        
        # Send empty update (all None values)
        update_data = {}
        response = requests.put(
            f"{BASE_URL}/api/gyms/{FITZONE_GYM_ID}",
            json=update_data,
            headers=headers
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✓ Empty update correctly rejected with 400")


class TestStripeConfig:
    """Bug 2: Test Stripe configuration save"""
    
    @pytest.fixture
    def gym_admin_token(self):
        """Get gym admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": GYM_ADMIN_EMAIL,
            "password": GYM_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    def test_get_stripe_config(self, gym_admin_token):
        """Get Stripe config should return status"""
        headers = {"Authorization": f"Bearer {gym_admin_token}"}
        response = requests.get(
            f"{BASE_URL}/api/gyms/{FITZONE_GYM_ID}/stripe-config",
            headers=headers
        )
        assert response.status_code == 200, f"Get stripe config failed: {response.text}"
        data = response.json()
        assert "has_stripe_key" in data, "has_stripe_key not in response"
        assert "currency" in data, "currency not in response"
        print(f"✓ Stripe config retrieved, has_key: {data['has_stripe_key']}, currency: {data['currency']}")
    
    def test_update_stripe_config(self, gym_admin_token):
        """Update Stripe config should succeed"""
        headers = {"Authorization": f"Bearer {gym_admin_token}"}
        
        # Update with test key
        update_data = {
            "stripe_secret_key": "sk_test_iteration6_test",
            "stripe_currency": "mxn"
        }
        response = requests.put(
            f"{BASE_URL}/api/gyms/{FITZONE_GYM_ID}/stripe-config",
            json=update_data,
            headers=headers
        )
        assert response.status_code == 200, f"Update stripe config failed: {response.text}"
        print("✓ Stripe config updated successfully")
        
        # Verify the update
        response = requests.get(
            f"{BASE_URL}/api/gyms/{FITZONE_GYM_ID}/stripe-config",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["has_stripe_key"] == True, "Stripe key not saved"
        assert data["currency"] == "mxn", f"Currency not updated, got {data['currency']}"
        print(f"✓ Stripe config verified, currency: {data['currency']}")
        
        # Restore to USD
        requests.put(
            f"{BASE_URL}/api/gyms/{FITZONE_GYM_ID}/stripe-config",
            json={"stripe_currency": "usd"},
            headers=headers
        )
    
    def test_update_stripe_config_empty_rejected(self, gym_admin_token):
        """Update Stripe config with no data should return 400"""
        headers = {"Authorization": f"Bearer {gym_admin_token}"}
        
        update_data = {}
        response = requests.put(
            f"{BASE_URL}/api/gyms/{FITZONE_GYM_ID}/stripe-config",
            json=update_data,
            headers=headers
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✓ Empty stripe config update correctly rejected with 400")


class TestDeleteDevice:
    """Bug 3: Test DELETE /api/devices/{device_id} endpoint"""
    
    @pytest.fixture
    def gym_admin_token(self):
        """Get gym admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": GYM_ADMIN_EMAIL,
            "password": GYM_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    def test_create_and_delete_device(self, gym_admin_token):
        """Create a device and then delete it"""
        headers = {"Authorization": f"Bearer {gym_admin_token}"}
        
        # Create a test device
        device_data = {
            "gym_id": FITZONE_GYM_ID,
            "name": "TEST_Device_Iteration6",
            "location": "Test Location"
        }
        response = requests.post(
            f"{BASE_URL}/api/devices",
            json=device_data,
            headers=headers
        )
        assert response.status_code == 200, f"Create device failed: {response.text}"
        device = response.json()
        device_id = device["id"]
        print(f"✓ Device created: {device_id}")
        
        # Delete the device
        response = requests.delete(
            f"{BASE_URL}/api/devices/{device_id}",
            headers=headers
        )
        assert response.status_code == 200, f"Delete device failed: {response.text}"
        data = response.json()
        assert data["message"] == "Device deleted", f"Unexpected message: {data}"
        print(f"✓ Device deleted successfully")
        
        # Verify device is gone
        response = requests.get(f"{BASE_URL}/api/devices", headers=headers)
        assert response.status_code == 200
        devices = response.json()
        device_ids = [d["id"] for d in devices]
        assert device_id not in device_ids, "Device still exists after deletion"
        print("✓ Device verified as deleted")
    
    def test_delete_nonexistent_device(self, gym_admin_token):
        """Delete non-existent device should return 404"""
        headers = {"Authorization": f"Bearer {gym_admin_token}"}
        
        response = requests.delete(
            f"{BASE_URL}/api/devices/nonexistent-device-id",
            headers=headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Delete non-existent device correctly returns 404")


class TestAccessLogExport:
    """Bug 6: Test access log export ordering (timestamp ascending)"""
    
    @pytest.fixture
    def gym_admin_token(self):
        """Get gym admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": GYM_ADMIN_EMAIL,
            "password": GYM_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    def test_access_logs_returned(self, gym_admin_token):
        """Access logs should be returned"""
        headers = {"Authorization": f"Bearer {gym_admin_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/access/logs?limit=100",
            headers=headers
        )
        assert response.status_code == 200, f"Get access logs failed: {response.text}"
        logs = response.json()
        print(f"✓ Access logs retrieved: {len(logs)} records")
        
        # Note: The API returns logs sorted by timestamp DESC (newest first)
        # The frontend exportToCSV function sorts them ASC before export
        # We verify the API works, frontend sorting is tested via Playwright
        if len(logs) > 1:
            # API returns DESC order
            for i in range(len(logs) - 1):
                assert logs[i]["timestamp"] >= logs[i+1]["timestamp"], \
                    f"Logs not in DESC order: {logs[i]['timestamp']} < {logs[i+1]['timestamp']}"
            print("✓ Access logs correctly ordered (DESC from API)")


class TestMemberLogin:
    """Test member login with code"""
    
    def test_member_login_with_code(self):
        """Member login with code should work"""
        response = requests.post(f"{BASE_URL}/api/auth/member/login?code={MEMBER_CODE}")
        assert response.status_code == 200, f"Member login failed: {response.text}"
        data = response.json()
        assert "member" in data, "No member in response"
        assert "token" in data, "No token in response"
        assert "gym" in data, "No gym in response"
        print(f"✓ Member login successful, member: {data['member']['name']}")
    
    def test_member_login_invalid_code(self):
        """Member login with invalid code should return 404"""
        response = requests.post(f"{BASE_URL}/api/auth/member/login?code=INVALID")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Invalid member code correctly returns 404")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
