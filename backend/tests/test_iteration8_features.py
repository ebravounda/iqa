"""
Test Iteration 8: Class Check-in/Attendance System and SMTP Email Configuration
Features:
1. Class Check-in - POST /api/bookings/{booking_id}/checkin, checkout, attendance endpoints
2. SMTP Configuration - PUT /api/gyms/{gym_id} with SMTP fields, POST /api/email/test, /api/email/welcome
"""

import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
SUPER_ADMIN_EMAIL = "admin@gymaccess.com"
SUPER_ADMIN_PASSWORD = "admin123"
GYM_ADMIN_EMAIL = "admin@fitzone.com"
GYM_ADMIN_PASSWORD = "admin123"
GYM_ID = "efe99507-15d5-4e54-9f07-30d2507894e0"


class TestAuth:
    """Authentication tests for both admin types"""
    
    def test_super_admin_login(self):
        """Test super admin login"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Super admin login failed: {response.text}"
        data = response.json()
        assert "token" in data
        assert data["admin"]["role"] == "super_admin"
        print(f"Super admin login: PASSED")
    
    def test_gym_admin_login(self):
        """Test gym admin login"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": GYM_ADMIN_EMAIL,
            "password": GYM_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Gym admin login failed: {response.text}"
        data = response.json()
        assert "token" in data
        assert data["admin"]["role"] == "gym_admin"
        assert data["admin"]["gym_id"] == GYM_ID
        print(f"Gym admin login: PASSED")


@pytest.fixture
def gym_admin_token():
    """Get gym admin token"""
    response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
        "email": GYM_ADMIN_EMAIL,
        "password": GYM_ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json()["token"]
    pytest.skip("Gym admin login failed")


@pytest.fixture
def super_admin_token():
    """Get super admin token"""
    response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
        "email": SUPER_ADMIN_EMAIL,
        "password": SUPER_ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json()["token"]
    pytest.skip("Super admin login failed")


class TestSMTPConfiguration:
    """Feature 2: SMTP Email Configuration Tests"""
    
    def test_update_gym_with_smtp_config(self, gym_admin_token):
        """Test updating gym with SMTP configuration"""
        headers = {"Authorization": f"Bearer {gym_admin_token}"}
        
        smtp_data = {
            "smtp_host": "smtp.test.com",
            "smtp_port": 587,
            "smtp_user": "test@gym.com",
            "smtp_password": "testpassword123",
            "smtp_from_email": "noreply@gym.com"
        }
        
        response = requests.put(
            f"{BASE_URL}/api/gyms/{GYM_ID}",
            json=smtp_data,
            headers=headers
        )
        assert response.status_code == 200, f"SMTP config update failed: {response.text}"
        
        data = response.json()
        assert data.get("smtp_host") == "smtp.test.com"
        assert data.get("smtp_port") == 587
        assert data.get("smtp_user") == "test@gym.com"
        assert data.get("smtp_from_email") == "noreply@gym.com"
        print("SMTP configuration update: PASSED")
    
    def test_email_test_endpoint_returns_error_without_real_smtp(self, gym_admin_token):
        """Test email test endpoint - should fail without real SMTP but return proper error"""
        headers = {"Authorization": f"Bearer {gym_admin_token}"}
        
        response = requests.post(
            f"{BASE_URL}/api/email/test",
            headers=headers
        )
        # Should return 500 with SMTP error (no real SMTP configured)
        # or 400 if SMTP not configured
        assert response.status_code in [400, 500], f"Unexpected status: {response.status_code}"
        data = response.json()
        assert "detail" in data or "message" in data
        print(f"Email test endpoint (expected error): PASSED - Status {response.status_code}")
    
    def test_email_welcome_endpoint(self, gym_admin_token):
        """Test welcome email endpoint - should fail without real SMTP but return proper error"""
        headers = {"Authorization": f"Bearer {gym_admin_token}"}
        
        # First get a member from the gym
        members_response = requests.get(
            f"{BASE_URL}/api/members",
            headers=headers
        )
        
        if members_response.status_code == 200 and len(members_response.json()) > 0:
            member_id = members_response.json()[0]["id"]
            
            response = requests.post(
                f"{BASE_URL}/api/email/welcome/{member_id}",
                headers=headers
            )
            # Should return 500 with SMTP error (no real SMTP configured)
            assert response.status_code in [400, 500], f"Unexpected status: {response.status_code}"
            print(f"Email welcome endpoint (expected error): PASSED - Status {response.status_code}")
        else:
            print("Email welcome endpoint: SKIPPED (no members found)")


class TestClassCheckinAttendance:
    """Feature 1: Class Check-in/Attendance System Tests"""
    
    def test_attendance_stats_endpoint(self, gym_admin_token):
        """Test attendance stats endpoint"""
        headers = {"Authorization": f"Bearer {gym_admin_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/attendance/stats",
            headers=headers
        )
        assert response.status_code == 200, f"Attendance stats failed: {response.text}"
        
        data = response.json()
        assert "total_bookings" in data
        assert "total_checkins" in data
        assert "attendance_rate" in data
        print(f"Attendance stats: PASSED - {data}")
    
    def test_get_schedules_for_today(self, gym_admin_token):
        """Test getting schedules for today"""
        headers = {"Authorization": f"Bearer {gym_admin_token}"}
        today = datetime.now().strftime("%Y-%m-%d")
        
        response = requests.get(
            f"{BASE_URL}/api/schedules",
            params={"date_from": today, "date_to": today},
            headers=headers
        )
        assert response.status_code == 200, f"Get schedules failed: {response.text}"
        
        data = response.json()
        print(f"Today's schedules: PASSED - Found {len(data)} schedules")
        return data
    
    def test_attendance_schedule_endpoint(self, gym_admin_token):
        """Test attendance for a specific schedule"""
        headers = {"Authorization": f"Bearer {gym_admin_token}"}
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Get schedules
        schedules_response = requests.get(
            f"{BASE_URL}/api/schedules",
            params={"date_from": today, "date_to": today},
            headers=headers
        )
        
        if schedules_response.status_code == 200 and len(schedules_response.json()) > 0:
            schedule_id = schedules_response.json()[0]["id"]
            
            response = requests.get(
                f"{BASE_URL}/api/attendance/schedule/{schedule_id}",
                headers=headers
            )
            assert response.status_code == 200, f"Attendance schedule failed: {response.text}"
            
            data = response.json()
            assert "schedule" in data
            assert "bookings" in data
            assert "total_booked" in data
            assert "checked_in" in data
            assert "pending" in data
            print(f"Attendance schedule endpoint: PASSED - {data['total_booked']} bookings")
        else:
            print("Attendance schedule endpoint: SKIPPED (no schedules for today)")
    
    def test_checkin_checkout_flow(self, gym_admin_token):
        """Test check-in and checkout flow for a booking"""
        headers = {"Authorization": f"Bearer {gym_admin_token}"}
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Get schedules
        schedules_response = requests.get(
            f"{BASE_URL}/api/schedules",
            params={"date_from": today, "date_to": today},
            headers=headers
        )
        
        if schedules_response.status_code != 200 or len(schedules_response.json()) == 0:
            print("Check-in/checkout flow: SKIPPED (no schedules for today)")
            return
        
        schedule_id = schedules_response.json()[0]["id"]
        
        # Get attendance for this schedule
        attendance_response = requests.get(
            f"{BASE_URL}/api/attendance/schedule/{schedule_id}",
            headers=headers
        )
        
        if attendance_response.status_code != 200:
            print("Check-in/checkout flow: SKIPPED (could not get attendance)")
            return
        
        bookings = attendance_response.json().get("bookings", [])
        
        if len(bookings) == 0:
            print("Check-in/checkout flow: SKIPPED (no bookings for this schedule)")
            return
        
        booking_id = bookings[0]["id"]
        
        # Test check-in
        checkin_response = requests.post(
            f"{BASE_URL}/api/bookings/{booking_id}/checkin",
            headers=headers
        )
        assert checkin_response.status_code == 200, f"Check-in failed: {checkin_response.text}"
        print(f"Check-in: PASSED")
        
        # Verify check-in
        verify_response = requests.get(
            f"{BASE_URL}/api/attendance/schedule/{schedule_id}",
            headers=headers
        )
        verified_bookings = verify_response.json().get("bookings", [])
        checked_in_booking = next((b for b in verified_bookings if b["id"] == booking_id), None)
        assert checked_in_booking is not None
        assert checked_in_booking.get("checked_in") == True
        print(f"Check-in verification: PASSED")
        
        # Test checkout (undo check-in)
        checkout_response = requests.post(
            f"{BASE_URL}/api/bookings/{booking_id}/checkout",
            headers=headers
        )
        assert checkout_response.status_code == 200, f"Checkout failed: {checkout_response.text}"
        print(f"Checkout (undo): PASSED")
        
        # Verify checkout
        verify_response2 = requests.get(
            f"{BASE_URL}/api/attendance/schedule/{schedule_id}",
            headers=headers
        )
        verified_bookings2 = verify_response2.json().get("bookings", [])
        checked_out_booking = next((b for b in verified_bookings2 if b["id"] == booking_id), None)
        assert checked_out_booking is not None
        assert checked_out_booking.get("checked_in") == False
        print(f"Checkout verification: PASSED")


class TestRegressions:
    """Regression tests for existing features"""
    
    def test_public_registration_page_endpoint(self):
        """Test public gym info endpoint for registration page"""
        response = requests.get(f"{BASE_URL}/api/gyms/{GYM_ID}/public-info")
        assert response.status_code == 200, f"Public gym info failed: {response.text}"
        
        data = response.json()
        assert "name" in data
        assert "id" in data
        print(f"Public registration endpoint: PASSED - Gym: {data.get('name')}")
    
    def test_public_plans_endpoint(self):
        """Test public plans endpoint"""
        response = requests.get(f"{BASE_URL}/api/plans/public/{GYM_ID}")
        assert response.status_code == 200, f"Public plans failed: {response.text}"
        print(f"Public plans endpoint: PASSED - Found {len(response.json())} plans")
    
    def test_gym_qr_mode_update(self, gym_admin_token):
        """Test QR mode toggle (dynamic/static)"""
        headers = {"Authorization": f"Bearer {gym_admin_token}"}
        
        # Set to static
        response = requests.put(
            f"{BASE_URL}/api/gyms/{GYM_ID}",
            json={"qr_mode": "static"},
            headers=headers
        )
        assert response.status_code == 200
        assert response.json().get("qr_mode") == "static"
        
        # Set back to dynamic
        response = requests.put(
            f"{BASE_URL}/api/gyms/{GYM_ID}",
            json={"qr_mode": "dynamic"},
            headers=headers
        )
        assert response.status_code == 200
        assert response.json().get("qr_mode") == "dynamic"
        print("QR mode toggle: PASSED")
    
    def test_devices_endpoint(self, gym_admin_token):
        """Test devices endpoint"""
        headers = {"Authorization": f"Bearer {gym_admin_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/devices",
            headers=headers
        )
        assert response.status_code == 200, f"Devices endpoint failed: {response.text}"
        print(f"Devices endpoint: PASSED - Found {len(response.json())} devices")
    
    def test_access_logs_endpoint(self, gym_admin_token):
        """Test access logs endpoint"""
        headers = {"Authorization": f"Bearer {gym_admin_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/access/logs",
            headers=headers
        )
        assert response.status_code == 200, f"Access logs failed: {response.text}"
        print(f"Access logs endpoint: PASSED - Found {len(response.json())} logs")
    
    def test_dashboard_stats_super_admin(self, super_admin_token):
        """Test dashboard stats for super admin shows gym column"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers=headers
        )
        assert response.status_code == 200, f"Dashboard stats failed: {response.text}"
        
        data = response.json()
        assert "recent_accesses_by_gym" in data
        print(f"Dashboard stats (super admin): PASSED - Has recent_accesses_by_gym")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
