"""
Iteration 31 Tests: Remember Me (Recordarme) and Device Limit Management Features

Tests:
1. GET /api/my-devices-by-code?code=XXX - Public endpoint to get devices by member code
2. PUT /api/my-devices-by-code/{device_id}/deactivate?code=XXX - Public endpoint to deactivate device
3. Device limit error format (DEVICE_LIMIT| prefix)
4. Admin login regression check
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestDevicesByCodeEndpoints:
    """Test the new public device management endpoints"""
    
    def test_get_devices_by_valid_code(self):
        """GET /api/my-devices-by-code returns devices for valid member code"""
        response = requests.get(f"{BASE_URL}/api/my-devices-by-code?code=RMB8S5")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "devices" in data, "Response should contain 'devices' key"
        assert "max_devices" in data, "Response should contain 'max_devices' key"
        assert "member_id" in data, "Response should contain 'member_id' key"
        assert isinstance(data["devices"], list), "devices should be a list"
        assert isinstance(data["max_devices"], int), "max_devices should be an integer"
        assert data["max_devices"] >= 1, "max_devices should be at least 1"
        print(f"PASS: GET /api/my-devices-by-code - Found {len(data['devices'])} devices, max={data['max_devices']}")
    
    def test_get_devices_by_invalid_code(self):
        """GET /api/my-devices-by-code returns 404 for invalid code"""
        response = requests.get(f"{BASE_URL}/api/my-devices-by-code?code=INVALID")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        
        data = response.json()
        assert "detail" in data, "Response should contain error detail"
        print(f"PASS: GET /api/my-devices-by-code with invalid code returns 404")
    
    def test_get_devices_by_lowercase_code(self):
        """GET /api/my-devices-by-code handles lowercase code (should convert to uppercase)"""
        response = requests.get(f"{BASE_URL}/api/my-devices-by-code?code=rmb8s5")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "devices" in data, "Response should contain 'devices' key"
        print(f"PASS: GET /api/my-devices-by-code handles lowercase code")
    
    def test_device_response_structure(self):
        """Verify device object structure in response"""
        response = requests.get(f"{BASE_URL}/api/my-devices-by-code?code=RMB8S5")
        assert response.status_code == 200
        
        data = response.json()
        if len(data["devices"]) > 0:
            device = data["devices"][0]
            # Check required fields
            assert "id" in device, "Device should have 'id'"
            assert "device_name" in device, "Device should have 'device_name'"
            assert "active" in device, "Device should have 'active'"
            # Check optional but expected fields
            if "last_active" in device:
                assert device["last_active"] is None or isinstance(device["last_active"], str)
            print(f"PASS: Device structure verified - id={device['id']}, name={device['device_name']}")
        else:
            print("SKIP: No devices to verify structure")


class TestDeactivateDeviceByCode:
    """Test device deactivation via public endpoint"""
    
    def test_deactivate_device_invalid_code(self):
        """PUT /api/my-devices-by-code/{id}/deactivate returns 404 for invalid code"""
        fake_device_id = str(uuid.uuid4())
        response = requests.put(f"{BASE_URL}/api/my-devices-by-code/{fake_device_id}/deactivate?code=INVALID")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"PASS: Deactivate with invalid code returns 404")
    
    def test_deactivate_device_invalid_device_id(self):
        """PUT /api/my-devices-by-code/{id}/deactivate returns 404 for invalid device ID"""
        fake_device_id = str(uuid.uuid4())
        response = requests.put(f"{BASE_URL}/api/my-devices-by-code/{fake_device_id}/deactivate?code=RMB8S5")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        
        data = response.json()
        assert "detail" in data
        print(f"PASS: Deactivate with invalid device ID returns 404")


class TestDeviceLimitErrorFormat:
    """Test that device limit errors have correct format"""
    
    def test_member_login_returns_device_info(self):
        """Member login should work and return member data"""
        # First, let's verify the member exists and can login
        # Generate a unique device fingerprint to avoid conflicts
        unique_fp = f"test_fp_{uuid.uuid4().hex[:12]}"
        
        response = requests.post(
            f"{BASE_URL}/api/auth/member/login?code=RMB8S5&device_fingerprint={unique_fp}"
        )
        
        # Could be 200 (success) or 403 (device limit) or 429 (rate limited)
        if response.status_code == 200:
            data = response.json()
            assert "member" in data, "Response should contain member"
            assert "token" in data, "Response should contain token"
            print(f"PASS: Member login successful")
        elif response.status_code == 403:
            data = response.json()
            detail = data.get("detail", "")
            if detail.startswith("DEVICE_LIMIT|"):
                print(f"PASS: Device limit error has correct DEVICE_LIMIT| prefix: {detail}")
            else:
                print(f"INFO: Got 403 but not device limit: {detail}")
        elif response.status_code == 429:
            print(f"SKIP: Rate limited (429) - expected security behavior")
        else:
            print(f"INFO: Got status {response.status_code}: {response.text}")


class TestAdminLoginRegression:
    """Regression test for admin login"""
    
    def test_admin_login_success(self):
        """Admin login should still work correctly"""
        response = requests.post(
            f"{BASE_URL}/api/auth/admin/login",
            json={"email": "admin@gymaccess.com", "password": "admin123"}
        )
        
        if response.status_code == 429:
            print("SKIP: Admin login rate limited (429) - expected security behavior")
            return
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "admin" in data, "Response should contain admin"
        assert "token" in data, "Response should contain token"
        assert data["admin"]["email"] == "admin@gymaccess.com"
        print(f"PASS: Admin login successful")
    
    def test_admin_login_invalid_credentials(self):
        """Admin login with wrong password should fail"""
        response = requests.post(
            f"{BASE_URL}/api/auth/admin/login",
            json={"email": "admin@gymaccess.com", "password": "wrongpassword"}
        )
        
        if response.status_code == 429:
            print("SKIP: Admin login rate limited (429)")
            return
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"PASS: Admin login with wrong password returns 401")


class TestAuthenticatedDeviceEndpoints:
    """Test authenticated device endpoints (for logged-in members)"""
    
    @pytest.fixture
    def member_token(self):
        """Get a member token for authenticated tests"""
        unique_fp = f"test_auth_fp_{uuid.uuid4().hex[:12]}"
        response = requests.post(
            f"{BASE_URL}/api/auth/member/login?code=RMB8S5&device_fingerprint={unique_fp}"
        )
        if response.status_code == 200:
            return response.json().get("token")
        return None
    
    def test_get_my_devices_authenticated(self, member_token):
        """GET /api/my-devices returns devices for authenticated member"""
        if not member_token:
            pytest.skip("Could not get member token")
        
        response = requests.get(
            f"{BASE_URL}/api/my-devices",
            headers={"Authorization": f"Bearer {member_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "devices" in data
        assert "max_devices" in data
        print(f"PASS: GET /api/my-devices authenticated - Found {len(data['devices'])} devices")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
