"""
Test suite for Iteration 5 features:
1. POST /api/auth/admin/impersonate/{gym_id} - Super admin impersonation
2. POST /api/gyms with admin_email/admin_password - Auto gym admin creation
3. GET /api/gyms returns gym_admin_email and gym_admin_name
4. New gym_admin can login with created credentials
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
SUPER_ADMIN_EMAIL = "admin@gymaccess.com"
SUPER_ADMIN_PASSWORD = "admin123"
GYM_ADMIN_EMAIL = "admin@fitzone.com"
GYM_ADMIN_PASSWORD = "admin123"
FITZONE_GYM_ID = "efe99507-15d5-4e54-9f07-30d2507894e0"
POWERFIT_GYM_ID = "20968094-669f-4a1e-a275-7b7fac4af3a0"


class TestSuperAdminImpersonation:
    """Test super admin impersonation feature"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login as super admin"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as super admin
        response = self.session.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Super admin login failed: {response.text}"
        data = response.json()
        self.super_admin_token = data["token"]
        self.super_admin = data["admin"]
        self.session.headers.update({"Authorization": f"Bearer {self.super_admin_token}"})
        
    def test_super_admin_can_impersonate_gym(self):
        """Test POST /api/auth/admin/impersonate/{gym_id} - super admin can impersonate"""
        response = self.session.post(f"{BASE_URL}/api/auth/admin/impersonate/{FITZONE_GYM_ID}")
        
        assert response.status_code == 200, f"Impersonation failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "admin" in data, "Response should contain admin data"
        assert "token" in data, "Response should contain new token"
        assert "gym" in data, "Response should contain gym data"
        
        # Verify admin data has impersonation flags
        admin = data["admin"]
        assert admin.get("impersonating") == True, "Admin should have impersonating=True"
        assert admin.get("original_role") == "super_admin", "Original role should be super_admin"
        assert admin.get("role") == "gym_admin", "Role should be gym_admin when impersonating"
        assert admin.get("gym_id") == FITZONE_GYM_ID, "gym_id should match impersonated gym"
        assert "gym_name" in admin, "Admin should have gym_name"
        
        # Verify gym data
        gym = data["gym"]
        assert gym.get("id") == FITZONE_GYM_ID, "Gym ID should match"
        
        print(f"SUCCESS: Super admin impersonated gym '{gym.get('name')}' successfully")
        
    def test_impersonation_token_has_gym_scope(self):
        """Test that impersonation token is scoped to the gym"""
        # Impersonate FitZone
        response = self.session.post(f"{BASE_URL}/api/auth/admin/impersonate/{FITZONE_GYM_ID}")
        assert response.status_code == 200
        
        impersonation_token = response.json()["token"]
        
        # Use impersonation token to get members - should only see FitZone members
        headers = {"Authorization": f"Bearer {impersonation_token}"}
        members_response = requests.get(f"{BASE_URL}/api/members", headers=headers)
        
        assert members_response.status_code == 200, f"Failed to get members: {members_response.text}"
        members = members_response.json()
        
        # All members should belong to FitZone gym
        for member in members:
            assert member.get("gym_id") == FITZONE_GYM_ID, f"Member {member.get('id')} should belong to FitZone"
        
        print(f"SUCCESS: Impersonation token correctly scoped - found {len(members)} members for FitZone")
        
    def test_impersonate_nonexistent_gym_returns_404(self):
        """Test impersonating a non-existent gym returns 404"""
        fake_gym_id = str(uuid.uuid4())
        response = self.session.post(f"{BASE_URL}/api/auth/admin/impersonate/{fake_gym_id}")
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("SUCCESS: Impersonating non-existent gym returns 404")


class TestGymAdminCannotImpersonate:
    """Test that gym_admin cannot use impersonation"""
    
    def test_gym_admin_cannot_impersonate(self):
        """Test that gym_admin gets 403 when trying to impersonate"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        # Login as gym admin
        response = session.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": GYM_ADMIN_EMAIL,
            "password": GYM_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Gym admin login failed: {response.text}"
        
        token = response.json()["token"]
        session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Try to impersonate - should fail
        response = session.post(f"{BASE_URL}/api/auth/admin/impersonate/{POWERFIT_GYM_ID}")
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("SUCCESS: Gym admin correctly denied impersonation (403)")


class TestGymCreationWithAdminCredentials:
    """Test creating gym with auto-created admin"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login as super admin"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as super admin
        response = self.session.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        token = response.json()["token"]
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Generate unique test data
        self.test_gym_name = f"TEST_Gym_{uuid.uuid4().hex[:8]}"
        self.test_admin_email = f"test_admin_{uuid.uuid4().hex[:8]}@testgym.com"
        self.test_admin_password = "testpass123"
        self.test_admin_name = "Test Admin User"
        self.created_gym_id = None
        
    def teardown_method(self, method):
        """Cleanup - delete test gym if created"""
        if self.created_gym_id:
            try:
                self.session.delete(f"{BASE_URL}/api/gyms/{self.created_gym_id}")
                print(f"Cleanup: Deleted test gym {self.created_gym_id}")
            except:
                pass
    
    def test_create_gym_with_admin_credentials(self):
        """Test POST /api/gyms with admin_email/admin_password creates gym admin"""
        gym_data = {
            "name": self.test_gym_name,
            "address": "Test Address 123",
            "phone": "555-1234",
            "email": "gym@test.com",
            "primary_color": "#FF5500",
            "admin_email": self.test_admin_email,
            "admin_password": self.test_admin_password,
            "admin_name": self.test_admin_name
        }
        
        response = self.session.post(f"{BASE_URL}/api/gyms", json=gym_data)
        
        assert response.status_code == 200, f"Gym creation failed: {response.text}"
        data = response.json()
        
        self.created_gym_id = data.get("id")
        
        # Verify gym was created
        assert data.get("name") == self.test_gym_name
        assert data.get("admin_created") == True, "admin_created flag should be True"
        
        print(f"SUCCESS: Gym '{self.test_gym_name}' created with admin")
        
        # Now verify the admin can login
        login_response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": self.test_admin_email,
            "password": self.test_admin_password
        })
        
        assert login_response.status_code == 200, f"New gym admin login failed: {login_response.text}"
        admin_data = login_response.json()
        
        assert admin_data["admin"]["email"] == self.test_admin_email
        assert admin_data["admin"]["name"] == self.test_admin_name
        assert admin_data["admin"]["role"] == "gym_admin"
        assert admin_data["admin"]["gym_id"] == self.created_gym_id
        
        print(f"SUCCESS: New gym admin can login with created credentials")
        
    def test_create_gym_without_admin_credentials(self):
        """Test POST /api/gyms without admin credentials still works"""
        gym_data = {
            "name": f"TEST_NoAdmin_{uuid.uuid4().hex[:8]}",
            "address": "Test Address"
        }
        
        response = self.session.post(f"{BASE_URL}/api/gyms", json=gym_data)
        
        assert response.status_code == 200, f"Gym creation failed: {response.text}"
        data = response.json()
        
        # Store for cleanup
        gym_id = data.get("id")
        
        # Verify gym was created without admin
        assert "admin_created" not in data or data.get("admin_created") != True
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/gyms/{gym_id}")
        
        print("SUCCESS: Gym created without admin credentials")
        
    def test_create_gym_with_duplicate_admin_email_fails(self):
        """Test that creating gym with existing admin email fails"""
        # First create a gym with admin
        gym_data = {
            "name": f"TEST_First_{uuid.uuid4().hex[:8]}",
            "admin_email": self.test_admin_email,
            "admin_password": self.test_admin_password,
            "admin_name": "First Admin"
        }
        
        response = self.session.post(f"{BASE_URL}/api/gyms", json=gym_data)
        assert response.status_code == 200
        first_gym_id = response.json().get("id")
        self.created_gym_id = first_gym_id
        
        # Try to create another gym with same admin email
        gym_data2 = {
            "name": f"TEST_Second_{uuid.uuid4().hex[:8]}",
            "admin_email": self.test_admin_email,  # Same email
            "admin_password": "different_pass",
            "admin_name": "Second Admin"
        }
        
        response2 = self.session.post(f"{BASE_URL}/api/gyms", json=gym_data2)
        
        assert response2.status_code == 400, f"Expected 400, got {response2.status_code}"
        assert "Ya existe" in response2.json().get("detail", "") or "already" in response2.json().get("detail", "").lower()
        
        print("SUCCESS: Duplicate admin email correctly rejected")


class TestGetGymsReturnsAdminInfo:
    """Test GET /api/gyms returns gym_admin_email and gym_admin_name"""
    
    def test_get_gyms_includes_admin_info(self):
        """Test GET /api/gyms returns gym admin info for super admin"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        # Login as super admin
        response = session.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        token = response.json()["token"]
        session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Get gyms
        response = session.get(f"{BASE_URL}/api/gyms")
        
        assert response.status_code == 200, f"Failed to get gyms: {response.text}"
        gyms = response.json()
        
        assert len(gyms) > 0, "Should have at least one gym"
        
        # Check FitZone gym has admin info
        fitzone = next((g for g in gyms if g.get("id") == FITZONE_GYM_ID), None)
        if fitzone:
            assert "gym_admin_email" in fitzone, "Gym should have gym_admin_email field"
            assert "gym_admin_name" in fitzone, "Gym should have gym_admin_name field"
            
            if fitzone.get("gym_admin_email"):
                print(f"SUCCESS: FitZone has admin: {fitzone.get('gym_admin_email')}")
            else:
                print("INFO: FitZone gym_admin_email is null (no admin assigned)")
        
        # Verify all gyms have the fields
        for gym in gyms:
            assert "gym_admin_email" in gym, f"Gym {gym.get('name')} missing gym_admin_email"
            assert "gym_admin_name" in gym, f"Gym {gym.get('name')} missing gym_admin_name"
        
        print(f"SUCCESS: GET /api/gyms returns admin info for all {len(gyms)} gyms")


class TestExistingGymAdminLogin:
    """Test existing gym admins can still login"""
    
    def test_fitzone_admin_login(self):
        """Test FitZone admin can login"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": GYM_ADMIN_EMAIL,
            "password": GYM_ADMIN_PASSWORD
        })
        
        assert response.status_code == 200, f"FitZone admin login failed: {response.text}"
        data = response.json()
        
        assert data["admin"]["email"] == GYM_ADMIN_EMAIL
        assert data["admin"]["role"] == "gym_admin"
        assert "token" in data
        
        print(f"SUCCESS: FitZone admin login works - {data['admin']['name']}")
        
    def test_powerfit_admin_login(self):
        """Test PowerFit admin can login"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": "admin@powerfit.com",
            "password": "powerfit123"
        })
        
        assert response.status_code == 200, f"PowerFit admin login failed: {response.text}"
        data = response.json()
        
        assert data["admin"]["email"] == "admin@powerfit.com"
        assert data["admin"]["role"] == "gym_admin"
        
        print(f"SUCCESS: PowerFit admin login works - {data['admin']['name']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
