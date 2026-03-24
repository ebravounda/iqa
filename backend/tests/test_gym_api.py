"""
Comprehensive Backend API Tests for Gym Access Control System
Tests: Auth, Classes, Schedules, Notifications, Guests, Members, Plans, Staff, Dashboard
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://stripe-gym-payments.preview.emergentagent.com').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@gymaccess.com"
ADMIN_PASSWORD = "admin123"
MEMBER_CODE = "LRF4HL"


class TestHealthCheck:
    """Health check endpoint tests"""
    
    def test_health_endpoint(self):
        """Test that health endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health check failed: {response.text}"
        print("✓ Health endpoint working")


class TestAdminAuth:
    """Admin authentication tests"""
    
    def test_admin_login_success(self):
        """Test admin login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "token" in data, "Token not in response"
        assert "admin" in data, "Admin data not in response"
        assert data["admin"]["email"] == ADMIN_EMAIL
        print(f"✓ Admin login successful - Role: {data['admin']['role']}")
        return data["token"]
    
    def test_admin_login_invalid_credentials(self):
        """Test admin login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": "wrong@email.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Invalid credentials correctly rejected")


class TestMemberAuth:
    """Member authentication tests"""
    
    def test_member_login_success(self):
        """Test member login with valid code"""
        response = requests.post(f"{BASE_URL}/api/auth/member/login?code={MEMBER_CODE}")
        assert response.status_code == 200, f"Member login failed: {response.text}"
        data = response.json()
        assert "token" in data, "Token not in response"
        assert "member" in data, "Member data not in response"
        assert data["member"]["code"] == MEMBER_CODE
        print(f"✓ Member login successful - Name: {data['member']['name']}")
        return data["token"]
    
    def test_member_login_invalid_code(self):
        """Test member login with invalid code"""
        response = requests.post(f"{BASE_URL}/api/auth/member/login?code=INVALID")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Invalid member code correctly rejected")


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json()["token"]
    pytest.skip("Admin authentication failed")


@pytest.fixture(scope="module")
def member_token():
    """Get member authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/member/login?code={MEMBER_CODE}")
    if response.status_code == 200:
        return response.json()["token"]
    pytest.skip("Member authentication failed")


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    """Get headers with admin auth"""
    return {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }


@pytest.fixture(scope="module")
def member_headers(member_token):
    """Get headers with member auth"""
    return {
        "Authorization": f"Bearer {member_token}",
        "Content-Type": "application/json"
    }


class TestClassesAPI:
    """Classes endpoint tests"""
    
    def test_get_classes(self, admin_headers):
        """Test GET /api/classes returns list"""
        response = requests.get(f"{BASE_URL}/api/classes", headers=admin_headers)
        assert response.status_code == 200, f"Get classes failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ GET /api/classes - Found {len(data)} classes")
        return data


class TestSchedulesAPI:
    """Schedules endpoint tests"""
    
    def test_get_schedules(self, admin_headers):
        """Test GET /api/schedules returns list"""
        response = requests.get(f"{BASE_URL}/api/schedules", headers=admin_headers)
        assert response.status_code == 200, f"Get schedules failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ GET /api/schedules - Found {len(data)} schedules")
        return data
    
    def test_create_schedule(self, admin_headers):
        """Test POST /api/schedules creates a new schedule"""
        # First get a class to use
        classes_response = requests.get(f"{BASE_URL}/api/classes", headers=admin_headers)
        if classes_response.status_code != 200 or not classes_response.json():
            pytest.skip("No classes available to create schedule")
        
        class_id = classes_response.json()[0]["id"]
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        schedule_data = {
            "class_id": class_id,
            "date": tomorrow,
            "start_time": "10:00",
            "end_time": "11:00"
        }
        
        response = requests.post(f"{BASE_URL}/api/schedules", json=schedule_data, headers=admin_headers)
        assert response.status_code == 200, f"Create schedule failed: {response.text}"
        data = response.json()
        assert "id" in data, "Schedule ID not in response"
        assert data["date"] == tomorrow
        print(f"✓ POST /api/schedules - Created schedule for {tomorrow}")
        return data


class TestNotificationsAPI:
    """Notifications endpoint tests"""
    
    def test_get_notifications_admin(self, admin_headers):
        """Test GET /api/notifications returns list for admin"""
        response = requests.get(f"{BASE_URL}/api/notifications", headers=admin_headers)
        assert response.status_code == 200, f"Get notifications failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ GET /api/notifications (admin) - Found {len(data)} notifications")
        return data
    
    def test_get_notifications_member(self, member_headers):
        """Test GET /api/notifications/member returns list for member"""
        response = requests.get(f"{BASE_URL}/api/notifications/member", headers=member_headers)
        assert response.status_code == 200, f"Get member notifications failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ GET /api/notifications/member - Found {len(data)} notifications")
        return data


class TestGuestsAPI:
    """Guests endpoint tests"""
    
    def test_get_guests_admin(self, admin_headers):
        """Test GET /api/guests returns list for admin"""
        response = requests.get(f"{BASE_URL}/api/guests", headers=admin_headers)
        assert response.status_code == 200, f"Get guests failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ GET /api/guests (admin) - Found {len(data)} guests")
        return data
    
    def test_get_member_guests(self, member_headers):
        """Test GET /api/guests/member returns list for member"""
        response = requests.get(f"{BASE_URL}/api/guests/member", headers=member_headers)
        assert response.status_code == 200, f"Get member guests failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ GET /api/guests/member - Found {len(data)} guests")
        return data


class TestMembersAPI:
    """Members endpoint tests"""
    
    def test_get_members(self, admin_headers):
        """Test GET /api/members returns list"""
        response = requests.get(f"{BASE_URL}/api/members", headers=admin_headers)
        assert response.status_code == 200, f"Get members failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ GET /api/members - Found {len(data)} members")
        return data


class TestPlansAPI:
    """Plans endpoint tests"""
    
    def test_get_plans(self, admin_headers):
        """Test GET /api/plans returns list"""
        response = requests.get(f"{BASE_URL}/api/plans", headers=admin_headers)
        assert response.status_code == 200, f"Get plans failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ GET /api/plans - Found {len(data)} plans")
        return data


class TestStaffAPI:
    """Staff endpoint tests"""
    
    def test_get_staff(self, admin_headers):
        """Test GET /api/staff returns list"""
        response = requests.get(f"{BASE_URL}/api/staff", headers=admin_headers)
        assert response.status_code == 200, f"Get staff failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ GET /api/staff - Found {len(data)} staff members")
        return data


class TestTrainersAPI:
    """Trainers endpoint tests"""
    
    def test_get_trainers(self, admin_headers):
        """Test GET /api/trainers returns list"""
        response = requests.get(f"{BASE_URL}/api/trainers", headers=admin_headers)
        assert response.status_code == 200, f"Get trainers failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ GET /api/trainers - Found {len(data)} trainers")
        return data


class TestDashboardAPI:
    """Dashboard endpoint tests"""
    
    def test_get_dashboard_stats(self, admin_headers):
        """Test GET /api/dashboard/stats returns stats"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=admin_headers)
        assert response.status_code == 200, f"Get dashboard stats failed: {response.text}"
        data = response.json()
        assert "total_members" in data, "total_members not in response"
        assert "active_members" in data, "active_members not in response"
        print(f"✓ GET /api/dashboard/stats - Total members: {data['total_members']}, Active: {data['active_members']}")
        return data


class TestQRAPI:
    """QR code endpoint tests"""
    
    def test_generate_qr(self, member_headers):
        """Test GET /api/qr/generate returns QR code"""
        response = requests.get(f"{BASE_URL}/api/qr/generate", headers=member_headers)
        assert response.status_code == 200, f"Generate QR failed: {response.text}"
        data = response.json()
        assert "qr_code" in data, "qr_code not in response"
        assert "expires_at" in data, "expires_at not in response"
        assert "refresh_seconds" in data, "refresh_seconds not in response"
        print(f"✓ GET /api/qr/generate - QR generated, expires in {data['refresh_seconds']}s")
        return data


class TestGymsAPI:
    """Gyms endpoint tests"""
    
    def test_get_gyms(self, admin_headers):
        """Test GET /api/gyms returns list"""
        response = requests.get(f"{BASE_URL}/api/gyms", headers=admin_headers)
        assert response.status_code == 200, f"Get gyms failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ GET /api/gyms - Found {len(data)} gyms")
        return data


class TestBookingsAPI:
    """Bookings endpoint tests"""
    
    def test_get_member_bookings(self, member_headers):
        """Test GET /api/bookings/member returns list"""
        response = requests.get(f"{BASE_URL}/api/bookings/member", headers=member_headers)
        assert response.status_code == 200, f"Get member bookings failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ GET /api/bookings/member - Found {len(data)} bookings")
        return data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
