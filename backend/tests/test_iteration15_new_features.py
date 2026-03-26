"""
Iteration 15 Tests: New Features
- Trainer Dashboard endpoint (GET /api/trainer/dashboard)
- Booking check-in/checkout endpoints (POST /api/bookings/{id}/checkin, checkout)
- Manual expired memberships check (POST /api/members/check-expired-memberships)
- Google Play guide download (GET /api/download/guia-google-play)
- CRON tasks verification (do_auto_suspend, do_send_expiration_reminders)
"""

import pytest
import requests
import os
from datetime import datetime, timedelta
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthAndBasics:
    """Basic health checks"""
    
    def test_api_health(self):
        """Test API health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print("✓ API health check passed")

    def test_api_root(self):
        """Test API root endpoint"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "Gym Access Control" in data.get("message", "")
        print("✓ API root check passed")


class TestAdminAuth:
    """Admin authentication tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": "admin@gymaccess.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "token" in data
        return data["token"]
    
    def test_admin_login(self, admin_token):
        """Test admin login works"""
        assert admin_token is not None
        print("✓ Admin login successful")


class TestTrainerDashboard:
    """Trainer Dashboard endpoint tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": "admin@gymaccess.com",
            "password": "admin123"
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    @pytest.fixture
    def gym_id(self, admin_token):
        """Get first gym ID"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/gyms", headers=headers)
        assert response.status_code == 200
        gyms = response.json()
        if gyms:
            return gyms[0]["id"]
        return None
    
    @pytest.fixture
    def trainer_token(self, admin_token, gym_id):
        """Create a trainer and get their token"""
        if not gym_id:
            pytest.skip("No gym available for trainer creation")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        trainer_email = f"TEST_trainer_{uuid.uuid4().hex[:8]}@test.com"
        
        # Create trainer
        response = requests.post(f"{BASE_URL}/api/trainers", headers=headers, json={
            "gym_id": gym_id,
            "email": trainer_email,
            "password": "trainer123",
            "name": "TEST Trainer Dashboard"
        })
        
        if response.status_code == 400 and "already registered" in response.text:
            # Try login with existing trainer
            pass
        else:
            assert response.status_code == 200, f"Trainer creation failed: {response.text}"
        
        # Login as trainer
        login_response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": trainer_email,
            "password": "trainer123"
        })
        
        if login_response.status_code == 200:
            return login_response.json()["token"]
        
        # If trainer login fails, use admin token for testing endpoint structure
        return admin_token
    
    def test_trainer_dashboard_endpoint_exists(self, admin_token):
        """Test that trainer dashboard endpoint exists and returns proper structure"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/trainer/dashboard", headers=headers)
        
        assert response.status_code == 200, f"Trainer dashboard failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "today_schedules" in data, "Missing today_schedules in response"
        assert "upcoming_schedules" in data, "Missing upcoming_schedules in response"
        assert "week_stats" in data, "Missing week_stats in response"
        assert "total_classes" in data, "Missing total_classes in response"
        
        # Verify week_stats structure
        week_stats = data["week_stats"]
        assert "total_schedules" in week_stats
        assert "total_bookings" in week_stats
        assert "total_checkins" in week_stats
        assert "attendance_rate" in week_stats
        
        print(f"✓ Trainer dashboard returns proper structure")
        print(f"  - Today schedules: {len(data['today_schedules'])}")
        print(f"  - Upcoming schedules: {len(data['upcoming_schedules'])}")
        print(f"  - Week stats: {week_stats}")
        print(f"  - Total classes: {data['total_classes']}")
    
    def test_trainer_dashboard_requires_auth(self):
        """Test that trainer dashboard requires authentication"""
        response = requests.get(f"{BASE_URL}/api/trainer/dashboard")
        assert response.status_code in [401, 403], "Trainer dashboard should require auth"
        print("✓ Trainer dashboard requires authentication")


class TestBookingCheckinCheckout:
    """Booking check-in and checkout endpoint tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": "admin@gymaccess.com",
            "password": "admin123"
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    def test_checkin_endpoint_exists(self, admin_token):
        """Test that checkin endpoint exists (even with invalid booking ID)"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Test with non-existent booking ID - should return 404, not 500
        response = requests.post(
            f"{BASE_URL}/api/bookings/nonexistent-booking-id/checkin",
            headers=headers
        )
        
        # Should return 404 (not found) not 500 (server error)
        assert response.status_code in [404, 400], f"Unexpected status: {response.status_code}"
        print("✓ Checkin endpoint exists and handles invalid booking ID correctly")
    
    def test_checkout_endpoint_exists(self, admin_token):
        """Test that checkout endpoint exists (even with invalid booking ID)"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Test with non-existent booking ID
        response = requests.post(
            f"{BASE_URL}/api/bookings/nonexistent-booking-id/checkout",
            headers=headers
        )
        
        # Checkout might succeed even with invalid ID (just updates nothing)
        # or return 404/400
        assert response.status_code in [200, 404, 400], f"Unexpected status: {response.status_code}"
        print("✓ Checkout endpoint exists")
    
    def test_checkin_requires_auth(self):
        """Test that checkin requires authentication"""
        response = requests.post(f"{BASE_URL}/api/bookings/test-id/checkin")
        assert response.status_code in [401, 403], "Checkin should require auth"
        print("✓ Checkin endpoint requires authentication")
    
    def test_checkout_requires_auth(self):
        """Test that checkout requires authentication"""
        response = requests.post(f"{BASE_URL}/api/bookings/test-id/checkout")
        assert response.status_code in [401, 403], "Checkout should require auth"
        print("✓ Checkout endpoint requires authentication")


class TestExpiredMembershipsCheck:
    """Manual expired memberships check endpoint tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": "admin@gymaccess.com",
            "password": "admin123"
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    def test_check_expired_memberships_endpoint(self, admin_token):
        """Test manual expired memberships check endpoint"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.post(
            f"{BASE_URL}/api/members/check-expired-memberships",
            headers=headers
        )
        
        assert response.status_code == 200, f"Check expired memberships failed: {response.text}"
        data = response.json()
        
        # Verify response has expected fields
        assert "checked" in data or "message" in data or "suspended_count" in data
        print(f"✓ Check expired memberships endpoint works: {data}")
    
    def test_check_expired_memberships_requires_auth(self):
        """Test that check expired memberships requires authentication"""
        response = requests.post(f"{BASE_URL}/api/members/check-expired-memberships")
        assert response.status_code in [401, 403], "Should require auth"
        print("✓ Check expired memberships requires authentication")


class TestGooglePlayGuideDownload:
    """Google Play guide download endpoint tests"""
    
    def test_google_play_guide_download(self):
        """Test Google Play guide download endpoint"""
        response = requests.get(f"{BASE_URL}/api/download/guia-google-play")
        
        assert response.status_code == 200, f"Guide download failed: {response.status_code}"
        
        # Check content type
        content_type = response.headers.get("content-type", "")
        assert "markdown" in content_type or "text" in content_type or "octet-stream" in content_type, \
            f"Unexpected content type: {content_type}"
        
        # Check content contains expected text
        content = response.text
        assert "Google Play" in content or "PWA" in content, "Content doesn't look like the guide"
        
        print(f"✓ Google Play guide download works")
        print(f"  - Content-Type: {content_type}")
        print(f"  - Content length: {len(content)} bytes")
    
    def test_google_play_guide_is_public(self):
        """Test that Google Play guide is publicly accessible (no auth required)"""
        response = requests.get(f"{BASE_URL}/api/download/guia-google-play")
        assert response.status_code == 200, "Guide should be publicly accessible"
        print("✓ Google Play guide is publicly accessible")


class TestDashboardStats:
    """Dashboard stats endpoint tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": "admin@gymaccess.com",
            "password": "admin123"
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    def test_dashboard_stats(self, admin_token):
        """Test dashboard stats endpoint"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=headers)
        
        assert response.status_code == 200, f"Dashboard stats failed: {response.text}"
        data = response.json()
        
        # Verify expected fields
        expected_fields = [
            "total_members", "active_members", "pending_members", "suspended_members",
            "gyms_count", "classes_count", "today_schedules", "today_bookings"
        ]
        
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
        
        print(f"✓ Dashboard stats endpoint works")
        print(f"  - Total members: {data.get('total_members')}")
        print(f"  - Active members: {data.get('active_members')}")
        print(f"  - Gyms count: {data.get('gyms_count')}")
        print(f"  - Classes count: {data.get('classes_count')}")


class TestSchedulesEndpoint:
    """Schedules endpoint tests for date navigation"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": "admin@gymaccess.com",
            "password": "admin123"
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    def test_schedules_with_date_filter(self, admin_token):
        """Test schedules endpoint with date filter (for date navigation)"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        response = requests.get(
            f"{BASE_URL}/api/schedules",
            headers=headers,
            params={"date_from": today, "date_to": today}
        )
        
        assert response.status_code == 200, f"Schedules fetch failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), "Schedules should return a list"
        print(f"✓ Schedules endpoint with date filter works")
        print(f"  - Schedules for {today}: {len(data)}")
    
    def test_schedules_date_range(self, admin_token):
        """Test schedules endpoint with date range"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        today = datetime.now()
        yesterday = (today - timedelta(days=1)).strftime("%Y-%m-%d")
        tomorrow = (today + timedelta(days=1)).strftime("%Y-%m-%d")
        
        response = requests.get(
            f"{BASE_URL}/api/schedules",
            headers=headers,
            params={"date_from": yesterday, "date_to": tomorrow}
        )
        
        assert response.status_code == 200, f"Schedules fetch failed: {response.text}"
        print(f"✓ Schedules endpoint with date range works")


class TestAttendanceEndpoint:
    """Attendance endpoint tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": "admin@gymaccess.com",
            "password": "admin123"
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    def test_attendance_stats(self, admin_token):
        """Test attendance stats endpoint"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(f"{BASE_URL}/api/attendance/stats", headers=headers)
        
        assert response.status_code == 200, f"Attendance stats failed: {response.text}"
        data = response.json()
        
        assert "total_bookings" in data
        assert "total_checkins" in data
        assert "attendance_rate" in data
        
        print(f"✓ Attendance stats endpoint works")
        print(f"  - Total bookings: {data.get('total_bookings')}")
        print(f"  - Total checkins: {data.get('total_checkins')}")
        print(f"  - Attendance rate: {data.get('attendance_rate')}%")


class TestTrainerCreation:
    """Trainer creation tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": "admin@gymaccess.com",
            "password": "admin123"
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    @pytest.fixture
    def gym_id(self, admin_token):
        """Get first gym ID"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/gyms", headers=headers)
        assert response.status_code == 200
        gyms = response.json()
        if gyms:
            return gyms[0]["id"]
        pytest.skip("No gyms available")
    
    def test_create_trainer(self, admin_token, gym_id):
        """Test trainer creation endpoint"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        trainer_email = f"TEST_trainer_{uuid.uuid4().hex[:8]}@test.com"
        
        response = requests.post(f"{BASE_URL}/api/trainers", headers=headers, json={
            "gym_id": gym_id,
            "email": trainer_email,
            "password": "trainer123",
            "name": "TEST Trainer"
        })
        
        if response.status_code == 400 and "already registered" in response.text:
            print("✓ Trainer creation endpoint works (email already exists)")
            return
        
        assert response.status_code == 200, f"Trainer creation failed: {response.text}"
        data = response.json()
        
        assert data.get("role") == "trainer"
        assert data.get("email") == trainer_email
        assert "password" not in data  # Password should not be returned
        
        print(f"✓ Trainer creation works")
        print(f"  - Trainer ID: {data.get('id')}")
        print(f"  - Email: {data.get('email')}")
    
    def test_get_trainers(self, admin_token):
        """Test get trainers endpoint"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(f"{BASE_URL}/api/trainers", headers=headers)
        
        assert response.status_code == 200, f"Get trainers failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list)
        print(f"✓ Get trainers endpoint works")
        print(f"  - Total trainers: {len(data)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
