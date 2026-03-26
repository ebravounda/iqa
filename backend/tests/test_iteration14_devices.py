"""
Iteration 14: Device Management & Member Visit Statistics Tests
Tests for:
- Member login with device_fingerprint registration
- Device limit enforcement (max devices per gym)
- Admin device management (view, deactivate, deactivate-all)
- Max devices setting update
- Member visit statistics endpoint
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test data
ADMIN_EMAIL = "admin@gymaccess.com"
ADMIN_PASSWORD = "admin123"
GYM_ID = "efe99507-15d5-4e54-9f07-30d2507894e0"
TEST_MEMBER_CODE = "NEDFJR"  # Kiosk Test User
TEST_MEMBER_ID = "86c975e8-7eb5-44cb-9299-198877a60f62"


class TestDeviceManagement:
    """Device management endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get admin token for authenticated requests"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        self.admin_token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.admin_token}"}
    
    def test_01_member_login_without_device_fingerprint(self):
        """Test member login without device_fingerprint - should work, no device registered"""
        response = requests.post(
            f"{BASE_URL}/api/auth/member/login?code={TEST_MEMBER_CODE}"
        )
        assert response.status_code == 200, f"Member login failed: {response.text}"
        data = response.json()
        assert "member" in data
        assert "token" in data
        assert data["member"]["code"] == TEST_MEMBER_CODE
        print(f"✓ Member login without device_fingerprint: 200 OK")
    
    def test_02_member_login_with_device_fingerprint(self):
        """Test member login with device_fingerprint - should register device"""
        fingerprint = f"TEST_FP_{uuid.uuid4().hex[:8]}"
        response = requests.post(
            f"{BASE_URL}/api/auth/member/login?code={TEST_MEMBER_CODE}&device_fingerprint={fingerprint}",
            headers={"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)"}
        )
        assert response.status_code == 200, f"Member login with FP failed: {response.text}"
        data = response.json()
        assert "member" in data
        assert "token" in data
        print(f"✓ Member login with device_fingerprint: 200 OK (FP: {fingerprint})")
        return fingerprint
    
    def test_03_get_member_devices(self):
        """Test GET /api/member-devices/{member_id} - returns list of devices"""
        response = requests.get(
            f"{BASE_URL}/api/member-devices/{TEST_MEMBER_ID}",
            headers=self.headers
        )
        assert response.status_code == 200, f"Get devices failed: {response.text}"
        devices = response.json()
        assert isinstance(devices, list)
        print(f"✓ GET /api/member-devices/{TEST_MEMBER_ID}: 200 OK ({len(devices)} devices)")
        return devices
    
    def test_04_update_max_devices_to_1(self):
        """Test PUT /api/gyms/{gym_id}/max-devices - set to 1"""
        response = requests.put(
            f"{BASE_URL}/api/gyms/{GYM_ID}/max-devices",
            json={"max_devices_per_member": 1},
            headers=self.headers
        )
        assert response.status_code == 200, f"Update max devices failed: {response.text}"
        data = response.json()
        assert data["max_devices_per_member"] == 1
        print(f"✓ PUT /api/gyms/{GYM_ID}/max-devices: 200 OK (set to 1)")
    
    def test_05_deactivate_all_devices_for_member(self):
        """Test PUT /api/member-devices/member/{member_id}/deactivate-all"""
        response = requests.put(
            f"{BASE_URL}/api/member-devices/member/{TEST_MEMBER_ID}/deactivate-all",
            headers=self.headers
        )
        assert response.status_code == 200, f"Deactivate all failed: {response.text}"
        data = response.json()
        assert "message" in data
        print(f"✓ PUT /api/member-devices/member/{TEST_MEMBER_ID}/deactivate-all: 200 OK")
    
    def test_06_login_first_device_with_limit_1(self):
        """Login with first device when max=1 - should succeed"""
        fingerprint1 = f"TEST_LIMIT_FP1_{uuid.uuid4().hex[:8]}"
        response = requests.post(
            f"{BASE_URL}/api/auth/member/login?code={TEST_MEMBER_CODE}&device_fingerprint={fingerprint1}",
            headers={"User-Agent": "Mozilla/5.0 (Android 12; Samsung Galaxy S21)"}
        )
        assert response.status_code == 200, f"First device login failed: {response.text}"
        print(f"✓ First device login with max=1: 200 OK (FP: {fingerprint1})")
        return fingerprint1
    
    def test_07_login_second_device_with_limit_1_should_fail(self):
        """Login with second device when max=1 - should return 403"""
        # First ensure we have one active device
        fingerprint1 = f"TEST_LIMIT_FP1_{uuid.uuid4().hex[:8]}"
        requests.post(
            f"{BASE_URL}/api/auth/member/login?code={TEST_MEMBER_CODE}&device_fingerprint={fingerprint1}",
            headers={"User-Agent": "Mozilla/5.0 (Android 12; Samsung Galaxy S21)"}
        )
        
        # Try second device
        fingerprint2 = f"TEST_LIMIT_FP2_{uuid.uuid4().hex[:8]}"
        response = requests.post(
            f"{BASE_URL}/api/auth/member/login?code={TEST_MEMBER_CODE}&device_fingerprint={fingerprint2}",
            headers={"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)"}
        )
        assert response.status_code == 403, f"Expected 403 for second device, got {response.status_code}: {response.text}"
        data = response.json()
        assert "detail" in data
        assert "Limite" in data["detail"] or "limite" in data["detail"].lower()
        print(f"✓ Second device login with max=1: 403 Forbidden (limit enforced)")
    
    def test_08_reset_max_devices_to_2(self):
        """Reset max devices to 2 for cleanup"""
        response = requests.put(
            f"{BASE_URL}/api/gyms/{GYM_ID}/max-devices",
            json={"max_devices_per_member": 2},
            headers=self.headers
        )
        assert response.status_code == 200, f"Reset max devices failed: {response.text}"
        print(f"✓ PUT /api/gyms/{GYM_ID}/max-devices: 200 OK (reset to 2)")
    
    def test_09_deactivate_single_device(self):
        """Test PUT /api/member-devices/{device_id}/deactivate"""
        # First register a device
        fingerprint = f"TEST_DEACT_{uuid.uuid4().hex[:8]}"
        requests.post(
            f"{BASE_URL}/api/auth/member/login?code={TEST_MEMBER_CODE}&device_fingerprint={fingerprint}",
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
        
        # Get devices to find the one we just created
        devices_response = requests.get(
            f"{BASE_URL}/api/member-devices/{TEST_MEMBER_ID}",
            headers=self.headers
        )
        devices = devices_response.json()
        active_devices = [d for d in devices if d.get("active")]
        
        if active_devices:
            device_id = active_devices[0]["id"]
            response = requests.put(
                f"{BASE_URL}/api/member-devices/{device_id}/deactivate",
                headers=self.headers
            )
            assert response.status_code == 200, f"Deactivate device failed: {response.text}"
            print(f"✓ PUT /api/member-devices/{device_id}/deactivate: 200 OK")
        else:
            print("⚠ No active devices to deactivate (test skipped)")
    
    def test_10_max_devices_validation_range(self):
        """Test max devices validation - must be 1-10"""
        # Test below range
        response = requests.put(
            f"{BASE_URL}/api/gyms/{GYM_ID}/max-devices",
            json={"max_devices_per_member": 0},
            headers=self.headers
        )
        assert response.status_code == 400, f"Expected 400 for max=0, got {response.status_code}"
        
        # Test above range
        response = requests.put(
            f"{BASE_URL}/api/gyms/{GYM_ID}/max-devices",
            json={"max_devices_per_member": 11},
            headers=self.headers
        )
        assert response.status_code == 400, f"Expected 400 for max=11, got {response.status_code}"
        print(f"✓ Max devices validation: 400 for out-of-range values (0, 11)")


class TestMemberVisitStatistics:
    """Member visit statistics endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get admin token for authenticated requests"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        self.admin_token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.admin_token}"}
    
    def test_01_get_member_visit_stats(self):
        """Test GET /api/stats/member-visits/{member_id}"""
        response = requests.get(
            f"{BASE_URL}/api/stats/member-visits/{TEST_MEMBER_ID}",
            headers=self.headers
        )
        assert response.status_code == 200, f"Get visit stats failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "total_visits" in data, "Missing total_visits"
        assert "this_month" in data, "Missing this_month"
        assert "this_week" in data, "Missing this_week"
        assert "monthly" in data, "Missing monthly array"
        
        # Verify monthly is an array with 6 months
        assert isinstance(data["monthly"], list)
        assert len(data["monthly"]) == 6, f"Expected 6 months, got {len(data['monthly'])}"
        
        # Verify monthly structure
        for month_data in data["monthly"]:
            assert "month" in month_data
            assert "visits" in month_data
        
        print(f"✓ GET /api/stats/member-visits/{TEST_MEMBER_ID}: 200 OK")
        print(f"  - total_visits: {data['total_visits']}")
        print(f"  - this_month: {data['this_month']}")
        print(f"  - this_week: {data['this_week']}")
        print(f"  - monthly: {data['monthly']}")
    
    def test_02_visit_stats_requires_auth(self):
        """Test that visit stats endpoint requires authentication"""
        response = requests.get(
            f"{BASE_URL}/api/stats/member-visits/{TEST_MEMBER_ID}"
        )
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print(f"✓ GET /api/stats/member-visits requires auth: {response.status_code}")


class TestDeviceManagementAuth:
    """Test that device management endpoints require admin auth"""
    
    def test_01_get_devices_requires_auth(self):
        """GET /api/member-devices/{member_id} requires auth"""
        response = requests.get(f"{BASE_URL}/api/member-devices/{TEST_MEMBER_ID}")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"✓ GET /api/member-devices requires auth: {response.status_code}")
    
    def test_02_deactivate_device_requires_auth(self):
        """PUT /api/member-devices/{device_id}/deactivate requires auth"""
        response = requests.put(f"{BASE_URL}/api/member-devices/fake-id/deactivate")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"✓ PUT /api/member-devices/deactivate requires auth: {response.status_code}")
    
    def test_03_deactivate_all_requires_auth(self):
        """PUT /api/member-devices/member/{member_id}/deactivate-all requires auth"""
        response = requests.put(f"{BASE_URL}/api/member-devices/member/{TEST_MEMBER_ID}/deactivate-all")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"✓ PUT /api/member-devices/deactivate-all requires auth: {response.status_code}")
    
    def test_04_update_max_devices_requires_auth(self):
        """PUT /api/gyms/{gym_id}/max-devices requires auth"""
        response = requests.put(
            f"{BASE_URL}/api/gyms/{GYM_ID}/max-devices",
            json={"max_devices_per_member": 2}
        )
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"✓ PUT /api/gyms/max-devices requires auth: {response.status_code}")


class TestCleanup:
    """Cleanup test data"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.admin_token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.admin_token}"}
    
    def test_cleanup_deactivate_test_devices(self):
        """Deactivate all test devices for cleanup"""
        response = requests.put(
            f"{BASE_URL}/api/member-devices/member/{TEST_MEMBER_ID}/deactivate-all",
            headers=self.headers
        )
        print(f"✓ Cleanup: Deactivated all test devices for member {TEST_MEMBER_ID}")
    
    def test_cleanup_reset_max_devices(self):
        """Reset max devices to default (2)"""
        response = requests.put(
            f"{BASE_URL}/api/gyms/{GYM_ID}/max-devices",
            json={"max_devices_per_member": 2},
            headers=self.headers
        )
        print(f"✓ Cleanup: Reset max devices to 2")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
