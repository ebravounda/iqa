"""
Iteration 21 - Bug Fixes Testing
Tests for:
1. AdminClasses: Create/Edit/Delete classes with all fields
2. AdminStaff: Super Admin gym selector in create modal
3. AdminSettings: Mi Plan SaaS section
4. AdminMembers: Email history modal
5. Backend PUT /api/classes/{id} with start_time, end_time, start_date, end_date
6. Backend GET /api/classes returns all fields
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://stripe-gym-payments.preview.emergentagent.com')

# Test credentials
SUPER_ADMIN_EMAIL = "admin@ingresoqr.com"
SUPER_ADMIN_PASSWORD = "admin123"
GYM_ADMIN_EMAIL = "admin@fitzone.com"
GYM_ADMIN_PASSWORD = "admin123"
FITZONE_GYM_ID = "efe99507-15d5-4e54-9f07-30d2507894e0"


@pytest.fixture(scope="module")
def super_admin_token():
    """Get super admin token"""
    response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
        "email": SUPER_ADMIN_EMAIL,
        "password": SUPER_ADMIN_PASSWORD
    })
    assert response.status_code == 200, f"Super admin login failed: {response.text}"
    return response.json()["token"]


@pytest.fixture(scope="module")
def gym_admin_token():
    """Get gym admin token"""
    response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
        "email": GYM_ADMIN_EMAIL,
        "password": GYM_ADMIN_PASSWORD
    })
    assert response.status_code == 200, f"Gym admin login failed: {response.text}"
    return response.json()["token"]


@pytest.fixture
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


class TestClassesAPI:
    """Test class CRUD operations with all fields"""
    
    def test_get_classes_returns_all_fields(self, api_client, gym_admin_token):
        """GET /api/classes returns classes with all fields populated"""
        response = api_client.get(
            f"{BASE_URL}/api/classes",
            headers={"Authorization": f"Bearer {gym_admin_token}"}
        )
        assert response.status_code == 200
        classes = response.json()
        assert isinstance(classes, list)
        print(f"Found {len(classes)} classes")
        
        # Check that classes have expected fields
        if len(classes) > 0:
            cls = classes[0]
            expected_fields = ["id", "name", "gym_id", "max_capacity", "duration_minutes", "class_type"]
            for field in expected_fields:
                assert field in cls, f"Missing field: {field}"
            print(f"Class fields present: {list(cls.keys())}")
    
    def test_create_class_with_all_fields(self, api_client, gym_admin_token):
        """POST /api/classes creates class with all fields"""
        unique_name = f"TEST_Class_{uuid.uuid4().hex[:6]}"
        payload = {
            "gym_id": FITZONE_GYM_ID,
            "name": unique_name,
            "description": "Test class description",
            "trainer_id": None,
            "max_capacity": 25,
            "duration_minutes": 45,
            "class_type": "group",
            "recurring": True,
            "days_of_week": [0, 2, 4],  # Mon, Wed, Fri
            "start_time": "10:00",
            "end_time": "10:45",
            "start_date": "2026-01-15",
            "end_date": "2026-03-15"
        }
        
        response = api_client.post(
            f"{BASE_URL}/api/classes",
            json=payload,
            headers={"Authorization": f"Bearer {gym_admin_token}"}
        )
        assert response.status_code == 200, f"Create class failed: {response.text}"
        
        created = response.json()
        assert created["name"] == unique_name
        assert created["max_capacity"] == 25
        assert created["duration_minutes"] == 45
        assert created["recurring"] == True
        assert created["days_of_week"] == [0, 2, 4]
        assert created["start_time"] == "10:00"
        assert created["end_time"] == "10:45"
        assert created["start_date"] == "2026-01-15"
        assert created["end_date"] == "2026-03-15"
        print(f"Created class: {created['id']}")
        
        # Store for cleanup
        self.__class__.created_class_id = created["id"]
        return created["id"]
    
    def test_update_class_with_time_fields(self, api_client, gym_admin_token):
        """PUT /api/classes/{id} updates class with start_time, end_time, start_date, end_date"""
        # First create a class to update
        unique_name = f"TEST_Update_{uuid.uuid4().hex[:6]}"
        create_response = api_client.post(
            f"{BASE_URL}/api/classes",
            json={
                "gym_id": FITZONE_GYM_ID,
                "name": unique_name,
                "max_capacity": 20,
                "duration_minutes": 60,
                "class_type": "group",
                "recurring": True,
                "days_of_week": [1],
                "start_time": "09:00"
            },
            headers={"Authorization": f"Bearer {gym_admin_token}"}
        )
        assert create_response.status_code == 200
        class_id = create_response.json()["id"]
        
        # Update with new time fields
        update_payload = {
            "name": f"{unique_name}_Updated",
            "start_time": "14:00",
            "end_time": "15:30",
            "start_date": "2026-02-01",
            "end_date": "2026-04-30",
            "days_of_week": [1, 3, 5],  # Tue, Thu, Sat
            "max_capacity": 30
        }
        
        update_response = api_client.put(
            f"{BASE_URL}/api/classes/{class_id}",
            json=update_payload,
            headers={"Authorization": f"Bearer {gym_admin_token}"}
        )
        assert update_response.status_code == 200, f"Update failed: {update_response.text}"
        
        updated = update_response.json()
        assert updated["start_time"] == "14:00"
        assert updated["end_time"] == "15:30"
        assert updated["start_date"] == "2026-02-01"
        assert updated["end_date"] == "2026-04-30"
        assert updated["days_of_week"] == [1, 3, 5]
        assert updated["max_capacity"] == 30
        print(f"Updated class {class_id} with new time fields")
        
        # Cleanup
        api_client.delete(
            f"{BASE_URL}/api/classes/{class_id}",
            headers={"Authorization": f"Bearer {gym_admin_token}"}
        )
    
    def test_delete_class(self, api_client, gym_admin_token):
        """DELETE /api/classes/{id} removes class"""
        # Create a class to delete
        unique_name = f"TEST_Delete_{uuid.uuid4().hex[:6]}"
        create_response = api_client.post(
            f"{BASE_URL}/api/classes",
            json={
                "gym_id": FITZONE_GYM_ID,
                "name": unique_name,
                "max_capacity": 15,
                "duration_minutes": 30,
                "class_type": "personal"
            },
            headers={"Authorization": f"Bearer {gym_admin_token}"}
        )
        assert create_response.status_code == 200
        class_id = create_response.json()["id"]
        
        # Delete the class
        delete_response = api_client.delete(
            f"{BASE_URL}/api/classes/{class_id}",
            headers={"Authorization": f"Bearer {gym_admin_token}"}
        )
        assert delete_response.status_code == 200
        assert "deleted" in delete_response.json().get("message", "").lower()
        print(f"Deleted class {class_id}")
        
        # Verify it's no longer in active classes
        get_response = api_client.get(
            f"{BASE_URL}/api/classes",
            headers={"Authorization": f"Bearer {gym_admin_token}"}
        )
        classes = get_response.json()
        class_ids = [c["id"] for c in classes]
        assert class_id not in class_ids, "Deleted class should not appear in active classes"


class TestStaffAPI:
    """Test staff creation with gym_id for super admin"""
    
    def test_get_gyms_for_super_admin(self, api_client, super_admin_token):
        """GET /api/gyms returns list of gyms for super admin"""
        response = api_client.get(
            f"{BASE_URL}/api/gyms",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        gyms = response.json()
        assert isinstance(gyms, list)
        assert len(gyms) > 0, "Should have at least one gym"
        
        # Check FitZone exists
        gym_ids = [g["id"] for g in gyms]
        assert FITZONE_GYM_ID in gym_ids, "FitZone gym should exist"
        print(f"Found {len(gyms)} gyms")
    
    def test_create_staff_with_gym_id_super_admin(self, api_client, super_admin_token):
        """POST /api/staff with gym_id works for super admin"""
        unique_email = f"test_staff_{uuid.uuid4().hex[:6]}@test.com"
        payload = {
            "gym_id": FITZONE_GYM_ID,
            "name": "Test Staff Member",
            "email": unique_email,
            "password": "testpass123",
            "role": "gym_manager"
        }
        
        response = api_client.post(
            f"{BASE_URL}/api/staff",
            json=payload,
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200, f"Create staff failed: {response.text}"
        
        created = response.json()
        assert created["email"] == unique_email
        assert created["gym_id"] == FITZONE_GYM_ID
        assert created["role"] == "gym_manager"
        print(f"Created staff member: {created['id']}")
    
    def test_get_trainers(self, api_client, gym_admin_token):
        """GET /api/trainers returns trainers list"""
        response = api_client.get(
            f"{BASE_URL}/api/trainers",
            headers={"Authorization": f"Bearer {gym_admin_token}"}
        )
        assert response.status_code == 200
        trainers = response.json()
        assert isinstance(trainers, list)
        print(f"Found {len(trainers)} trainers")


class TestSaaSSubscription:
    """Test SaaS subscription endpoints for gym admin"""
    
    def test_get_my_subscription(self, api_client, gym_admin_token):
        """GET /api/saas/my-subscription returns subscription info"""
        response = api_client.get(
            f"{BASE_URL}/api/saas/my-subscription",
            headers={"Authorization": f"Bearer {gym_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should have plan info if assigned
        if data.get("plan"):
            plan = data["plan"]
            assert "name" in plan
            assert "max_members" in plan
            print(f"Current plan: {plan['name']}, max members: {plan['max_members']}")
        else:
            print("No plan assigned to this gym")
        
        # Should have member count
        assert "member_count" in data
        print(f"Member count: {data['member_count']}")
    
    def test_get_available_saas_plans(self, api_client, gym_admin_token):
        """GET /api/saas/available-plans returns available plans"""
        response = api_client.get(
            f"{BASE_URL}/api/saas/available-plans",
            headers={"Authorization": f"Bearer {gym_admin_token}"}
        )
        assert response.status_code == 200
        plans = response.json()
        assert isinstance(plans, list)
        print(f"Found {len(plans)} available SaaS plans")
        
        # Check plan structure
        if len(plans) > 0:
            plan = plans[0]
            expected_fields = ["id", "name", "max_members", "price_monthly"]
            for field in expected_fields:
                assert field in plan, f"Missing field: {field}"


class TestEmailHistory:
    """Test email history endpoints"""
    
    def test_get_member_emails(self, api_client, gym_admin_token):
        """GET /api/emails/member/{id} returns email history"""
        # First get a member
        members_response = api_client.get(
            f"{BASE_URL}/api/members",
            headers={"Authorization": f"Bearer {gym_admin_token}"}
        )
        assert members_response.status_code == 200
        members = members_response.json()
        
        if len(members) > 0:
            member_id = members[0]["id"]
            
            # Get email history
            response = api_client.get(
                f"{BASE_URL}/api/emails/member/{member_id}",
                headers={"Authorization": f"Bearer {gym_admin_token}"}
            )
            assert response.status_code == 200
            emails = response.json()
            assert isinstance(emails, list)
            print(f"Found {len(emails)} emails for member {member_id}")
            
            # Check email structure if any exist
            if len(emails) > 0:
                email = emails[0]
                expected_fields = ["id", "subject", "status", "sent_at"]
                for field in expected_fields:
                    assert field in email, f"Missing field: {field}"
        else:
            pytest.skip("No members found to test email history")


class TestTrainersAPI:
    """Test trainer creation with gym_id"""
    
    def test_create_trainer_with_gym_id(self, api_client, super_admin_token):
        """POST /api/trainers with gym_id works for super admin"""
        unique_email = f"test_trainer_{uuid.uuid4().hex[:6]}@test.com"
        payload = {
            "gym_id": FITZONE_GYM_ID,
            "name": "Test Trainer",
            "email": unique_email,
            "password": "testpass123",
            "phone": "+1234567890",
            "specialties": ["Yoga", "Pilates"],
            "bio": "Test trainer bio"
        }
        
        response = api_client.post(
            f"{BASE_URL}/api/trainers",
            json=payload,
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200, f"Create trainer failed: {response.text}"
        
        created = response.json()
        assert created["email"] == unique_email
        assert created["gym_id"] == FITZONE_GYM_ID
        assert created["role"] == "trainer"
        assert created["specialties"] == ["Yoga", "Pilates"]
        print(f"Created trainer: {created['id']}")


class TestClassWithTrainer:
    """Test class creation with trainer assignment"""
    
    def test_create_class_with_trainer(self, api_client, gym_admin_token):
        """Create class and verify trainer info is returned"""
        # Get trainers first
        trainers_response = api_client.get(
            f"{BASE_URL}/api/trainers",
            headers={"Authorization": f"Bearer {gym_admin_token}"}
        )
        trainers = trainers_response.json()
        
        if len(trainers) > 0:
            trainer_id = trainers[0]["id"]
            unique_name = f"TEST_WithTrainer_{uuid.uuid4().hex[:6]}"
            
            payload = {
                "gym_id": FITZONE_GYM_ID,
                "name": unique_name,
                "trainer_id": trainer_id,
                "max_capacity": 20,
                "duration_minutes": 60,
                "class_type": "group"
            }
            
            response = api_client.post(
                f"{BASE_URL}/api/classes",
                json=payload,
                headers={"Authorization": f"Bearer {gym_admin_token}"}
            )
            assert response.status_code == 200
            created = response.json()
            assert created["trainer_id"] == trainer_id
            print(f"Created class with trainer: {created['id']}")
            
            # Verify trainer info in GET
            get_response = api_client.get(
                f"{BASE_URL}/api/classes",
                headers={"Authorization": f"Bearer {gym_admin_token}"}
            )
            classes = get_response.json()
            test_class = next((c for c in classes if c["id"] == created["id"]), None)
            assert test_class is not None
            assert "trainer" in test_class or test_class.get("trainer_id") == trainer_id
            
            # Cleanup
            api_client.delete(
                f"{BASE_URL}/api/classes/{created['id']}",
                headers={"Authorization": f"Bearer {gym_admin_token}"}
            )
        else:
            pytest.skip("No trainers found to test class with trainer")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
