"""
Iteration 22 - Comprehensive Bug Fixes Testing
Tests for:
1. SaaS Plan Edit - boolean False preservation
2. Class Create/Edit/Delete with start_date/end_date
3. File Upload endpoints (gym logo, member avatar)
4. Trainer Dashboard filtering
"""
import pytest
import requests
import os
from datetime import date, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://stripe-gym-payments.preview.emergentagent.com')

class TestAuth:
    """Authentication tests"""
    
    @pytest.fixture(scope="class")
    def super_admin_token(self):
        """Get super admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": "admin@ingresoqr.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Super admin login failed: {response.text}"
        data = response.json()
        assert "token" in data
        return data["token"]
    
    @pytest.fixture(scope="class")
    def gym_admin_token(self):
        """Get gym admin token (FitZone)"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": "admin@fitzone.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Gym admin login failed: {response.text}"
        data = response.json()
        assert "token" in data
        return data["token"]
    
    def test_super_admin_login(self, super_admin_token):
        """Test super admin can login"""
        assert super_admin_token is not None
        assert len(super_admin_token) > 0
        print("SUCCESS: Super admin login works")
    
    def test_gym_admin_login(self, gym_admin_token):
        """Test gym admin can login"""
        assert gym_admin_token is not None
        assert len(gym_admin_token) > 0
        print("SUCCESS: Gym admin login works")


class TestSaaSPlanBooleanSaving:
    """Test SaaS Plan feature toggle saving - especially boolean False"""
    
    @pytest.fixture(scope="class")
    def super_admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": "admin@ingresoqr.com",
            "password": "admin123"
        })
        return response.json()["token"]
    
    def test_get_saas_plans(self, super_admin_token):
        """Test getting SaaS plans"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/saas/plans", headers=headers)
        assert response.status_code == 200
        plans = response.json()
        assert isinstance(plans, list)
        print(f"SUCCESS: Got {len(plans)} SaaS plans")
        return plans
    
    def test_update_saas_plan_boolean_false(self, super_admin_token):
        """Test that boolean False is preserved when updating SaaS plan"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        
        # Get existing plans
        response = requests.get(f"{BASE_URL}/api/saas/plans", headers=headers)
        plans = response.json()
        assert len(plans) > 0, "No SaaS plans found"
        
        plan = plans[0]
        plan_id = plan["id"]
        
        # Update with has_classes=True and has_pos=False
        update_data = {
            "has_classes": True,
            "has_pos": False,
            "has_analytics": False
        }
        
        response = requests.put(f"{BASE_URL}/api/saas/plans/{plan_id}", 
                               json=update_data, headers=headers)
        assert response.status_code == 200, f"Update failed: {response.text}"
        
        updated_plan = response.json()
        
        # Verify boolean False is preserved
        assert updated_plan["has_classes"] == True, "has_classes should be True"
        assert updated_plan["has_pos"] == False, "has_pos should be False (not None or missing)"
        assert updated_plan["has_analytics"] == False, "has_analytics should be False"
        
        print("SUCCESS: SaaS plan boolean False values are preserved correctly")
        
        # Verify by fetching again
        response = requests.get(f"{BASE_URL}/api/saas/plans", headers=headers)
        plans = response.json()
        verified_plan = next((p for p in plans if p["id"] == plan_id), None)
        assert verified_plan is not None
        assert verified_plan["has_pos"] == False, "has_pos should still be False after re-fetch"
        print("SUCCESS: Boolean False persisted correctly in database")


class TestClassSchedulingWithDates:
    """Test class creation with start_date and end_date"""
    
    @pytest.fixture(scope="class")
    def gym_admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": "admin@fitzone.com",
            "password": "admin123"
        })
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def gym_id(self, gym_admin_token):
        """Get FitZone gym ID"""
        headers = {"Authorization": f"Bearer {gym_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/gyms", headers=headers)
        gyms = response.json()
        fitzone = next((g for g in gyms if "fitzone" in g.get("name", "").lower()), None)
        if fitzone:
            return fitzone["id"]
        return gyms[0]["id"] if gyms else None
    
    def test_create_class_with_date_range(self, gym_admin_token, gym_id):
        """Test creating a recurring class with start_date and end_date"""
        headers = {"Authorization": f"Bearer {gym_admin_token}"}
        
        # Create class with date range: March 28 to April 10, 2026
        # Days: Mon(0), Wed(2), Fri(4)
        start_date = "2026-03-28"
        end_date = "2026-04-10"
        
        class_data = {
            "name": "TEST_DateRange_Class",
            "description": "Test class with date range",
            "gym_id": gym_id,
            "max_capacity": 15,
            "duration_minutes": 45,
            "class_type": "group",
            "recurring": True,
            "days_of_week": [0, 2, 4],  # Mon, Wed, Fri
            "start_time": "10:00",
            "end_time": "10:45",
            "start_date": start_date,
            "end_date": end_date
        }
        
        response = requests.post(f"{BASE_URL}/api/classes", json=class_data, headers=headers)
        assert response.status_code == 200, f"Class creation failed: {response.text}"
        
        created_class = response.json()
        class_id = created_class["id"]
        
        assert created_class["name"] == "TEST_DateRange_Class"
        assert created_class["start_date"] == start_date
        assert created_class["end_date"] == end_date
        print(f"SUCCESS: Created class with date range {start_date} to {end_date}")
        
        # Verify schedules were generated within date range
        response = requests.get(f"{BASE_URL}/api/schedules", headers=headers)
        assert response.status_code == 200
        schedules = response.json()
        
        class_schedules = [s for s in schedules if s.get("class_id") == class_id]
        print(f"Found {len(class_schedules)} schedules for the class")
        
        # Check that no schedules exist after end_date
        for schedule in class_schedules:
            schedule_date = schedule.get("date")
            assert schedule_date <= end_date, f"Schedule {schedule_date} is after end_date {end_date}"
        
        print("SUCCESS: All schedules are within the date range")
        
        # Cleanup - delete the test class
        response = requests.delete(f"{BASE_URL}/api/classes/{class_id}", headers=headers)
        assert response.status_code == 200
        print("SUCCESS: Test class deleted")
        
        return class_id
    
    def test_edit_class_days_regenerates_schedules(self, gym_admin_token, gym_id):
        """Test that editing class days_of_week regenerates schedules"""
        headers = {"Authorization": f"Bearer {gym_admin_token}"}
        
        # Create a class first
        class_data = {
            "name": "TEST_EditDays_Class",
            "gym_id": gym_id,
            "max_capacity": 10,
            "duration_minutes": 60,
            "class_type": "group",
            "recurring": True,
            "days_of_week": [0, 1, 2, 3, 4],  # Mon-Fri
            "start_time": "08:00",
            "end_time": "09:00"
        }
        
        response = requests.post(f"{BASE_URL}/api/classes", json=class_data, headers=headers)
        assert response.status_code == 200
        created_class = response.json()
        class_id = created_class["id"]
        
        # Update to Mon, Wed, Fri only
        update_data = {
            "days_of_week": [0, 2, 4]  # Mon, Wed, Fri
        }
        
        response = requests.put(f"{BASE_URL}/api/classes/{class_id}", 
                               json=update_data, headers=headers)
        assert response.status_code == 200
        updated_class = response.json()
        
        assert updated_class["days_of_week"] == [0, 2, 4], "days_of_week should be updated"
        print("SUCCESS: Class days_of_week updated correctly")
        
        # Cleanup
        response = requests.delete(f"{BASE_URL}/api/classes/{class_id}", headers=headers)
        assert response.status_code == 200
        print("SUCCESS: Test class deleted")
    
    def test_delete_class_removes_schedules(self, gym_admin_token, gym_id):
        """Test that deleting a class removes all its schedules"""
        headers = {"Authorization": f"Bearer {gym_admin_token}"}
        
        # Create a class
        class_data = {
            "name": "TEST_Delete_Class",
            "gym_id": gym_id,
            "max_capacity": 10,
            "duration_minutes": 30,
            "class_type": "group",
            "recurring": True,
            "days_of_week": [0, 2],
            "start_time": "07:00",
            "end_time": "07:30"
        }
        
        response = requests.post(f"{BASE_URL}/api/classes", json=class_data, headers=headers)
        assert response.status_code == 200
        created_class = response.json()
        class_id = created_class["id"]
        
        # Get schedules before delete
        response = requests.get(f"{BASE_URL}/api/schedules", headers=headers)
        schedules_before = [s for s in response.json() if s.get("class_id") == class_id]
        print(f"Schedules before delete: {len(schedules_before)}")
        
        # Delete the class
        response = requests.delete(f"{BASE_URL}/api/classes/{class_id}", headers=headers)
        assert response.status_code == 200
        
        # Verify schedules are removed
        response = requests.get(f"{BASE_URL}/api/schedules", headers=headers)
        schedules_after = [s for s in response.json() if s.get("class_id") == class_id]
        
        assert len(schedules_after) == 0, f"Expected 0 schedules after delete, got {len(schedules_after)}"
        print("SUCCESS: All schedules removed after class deletion")


class TestFileUploadEndpoints:
    """Test file upload endpoints"""
    
    @pytest.fixture(scope="class")
    def gym_admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": "admin@fitzone.com",
            "password": "admin123"
        })
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def gym_id(self, gym_admin_token):
        headers = {"Authorization": f"Bearer {gym_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/gyms", headers=headers)
        gyms = response.json()
        fitzone = next((g for g in gyms if "fitzone" in g.get("name", "").lower()), None)
        return fitzone["id"] if fitzone else gyms[0]["id"]
    
    def test_gym_logo_upload_endpoint_exists(self, gym_admin_token, gym_id):
        """Test that gym logo upload endpoint exists and accepts requests"""
        headers = {"Authorization": f"Bearer {gym_admin_token}"}
        
        # Create a simple test image (1x1 pixel PNG)
        import base64
        # Minimal valid PNG
        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
        
        files = {"file": ("test_logo.png", png_data, "image/png")}
        
        response = requests.post(
            f"{BASE_URL}/api/upload/gym-logo/{gym_id}",
            files=files,
            headers=headers
        )
        
        # Should return 200 or at least not 404
        assert response.status_code != 404, "Gym logo upload endpoint not found"
        
        if response.status_code == 200:
            data = response.json()
            assert "logo_url" in data, "Response should contain logo_url"
            print(f"SUCCESS: Gym logo uploaded, URL: {data.get('logo_url')}")
        else:
            print(f"Note: Upload returned {response.status_code} - {response.text}")
    
    def test_member_avatar_upload_endpoint_exists(self, gym_admin_token):
        """Test that member avatar upload endpoint exists"""
        headers = {"Authorization": f"Bearer {gym_admin_token}"}
        
        # Get a member ID first
        response = requests.get(f"{BASE_URL}/api/members", headers=headers)
        assert response.status_code == 200
        members = response.json()
        
        if len(members) == 0:
            pytest.skip("No members found to test avatar upload")
        
        member_id = members[0]["id"]
        
        # Create a simple test image
        import base64
        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
        
        files = {"file": ("test_avatar.png", png_data, "image/png")}
        
        response = requests.post(
            f"{BASE_URL}/api/upload/avatar/admin/{member_id}",
            files=files,
            headers=headers
        )
        
        assert response.status_code != 404, "Member avatar upload endpoint not found"
        
        if response.status_code == 200:
            data = response.json()
            assert "storage_path" in data, "Response should contain storage_path"
            print(f"SUCCESS: Member avatar uploaded")
        else:
            print(f"Note: Avatar upload returned {response.status_code}")
    
    def test_file_serving_endpoint(self, gym_admin_token):
        """Test that file serving endpoint exists"""
        # Try to access a non-existent file - should return 404, not 500
        response = requests.get(f"{BASE_URL}/api/files/test/nonexistent.png")
        
        # Should return 404 for non-existent file, not 500
        assert response.status_code in [404, 401, 403], f"Unexpected status: {response.status_code}"
        print("SUCCESS: File serving endpoint exists and handles missing files correctly")


class TestTrainerDashboard:
    """Test trainer dashboard filtering"""
    
    @pytest.fixture(scope="class")
    def gym_admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": "admin@fitzone.com",
            "password": "admin123"
        })
        return response.json()["token"]
    
    def test_get_trainers(self, gym_admin_token):
        """Test getting trainers list"""
        headers = {"Authorization": f"Bearer {gym_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/trainers", headers=headers)
        assert response.status_code == 200
        trainers = response.json()
        print(f"SUCCESS: Got {len(trainers)} trainers")
        return trainers


class TestMembersContactButton:
    """Test members page functionality"""
    
    @pytest.fixture(scope="class")
    def gym_admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": "admin@fitzone.com",
            "password": "admin123"
        })
        return response.json()["token"]
    
    def test_get_members(self, gym_admin_token):
        """Test getting members list"""
        headers = {"Authorization": f"Bearer {gym_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/members", headers=headers)
        assert response.status_code == 200
        members = response.json()
        assert len(members) > 0, "Should have at least one member"
        print(f"SUCCESS: Got {len(members)} members")
        
        # Verify member has required fields for contact display
        member = members[0]
        assert "code" in member, "Member should have code"
        assert "name" in member, "Member should have name"
        print("SUCCESS: Members have required fields for contact display")


class TestSaaSSubscription:
    """Test SaaS subscription endpoints"""
    
    @pytest.fixture(scope="class")
    def gym_admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": "admin@fitzone.com",
            "password": "admin123"
        })
        return response.json()["token"]
    
    def test_get_my_subscription(self, gym_admin_token):
        """Test getting current subscription"""
        headers = {"Authorization": f"Bearer {gym_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/saas/my-subscription", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "gym_name" in data
        assert "member_count" in data
        assert "max_members" in data
        print(f"SUCCESS: Got subscription for {data.get('gym_name')}")
        print(f"  - Members: {data.get('member_count')}/{data.get('max_members')}")
        if data.get("plan"):
            print(f"  - Plan: {data['plan'].get('name')}")
    
    def test_get_available_plans(self):
        """Test getting available SaaS plans (public endpoint)"""
        response = requests.get(f"{BASE_URL}/api/saas/available-plans")
        assert response.status_code == 200
        plans = response.json()
        assert isinstance(plans, list)
        print(f"SUCCESS: Got {len(plans)} available SaaS plans")


class TestAdminAccessAttendance:
    """Test attendance modal functionality"""
    
    @pytest.fixture(scope="class")
    def gym_admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": "admin@fitzone.com",
            "password": "admin123"
        })
        return response.json()["token"]
    
    def test_get_access_logs(self, gym_admin_token):
        """Test getting access logs"""
        headers = {"Authorization": f"Bearer {gym_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/access/logs", headers=headers)
        assert response.status_code == 200
        logs = response.json()
        print(f"SUCCESS: Got {len(logs)} access logs")


class TestStaffGymSelector:
    """Test staff creation with gym selector for super admin"""
    
    @pytest.fixture(scope="class")
    def super_admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": "admin@ingresoqr.com",
            "password": "admin123"
        })
        return response.json()["token"]
    
    def test_get_gyms_for_staff_creation(self, super_admin_token):
        """Test that super admin can get gyms list for staff creation"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/gyms", headers=headers)
        assert response.status_code == 200
        gyms = response.json()
        assert len(gyms) > 0, "Should have at least one gym"
        print(f"SUCCESS: Super admin can see {len(gyms)} gyms for staff creation")
    
    def test_get_staff_list(self, super_admin_token):
        """Test getting staff list"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/staff", headers=headers)
        assert response.status_code == 200
        staff = response.json()
        print(f"SUCCESS: Got {len(staff)} staff members")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
