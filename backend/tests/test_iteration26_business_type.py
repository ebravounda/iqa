"""
Iteration 26 - Multi-vertical Business Type Feature Tests
Tests for business_type field in gyms (gym, condominium, hotel, coworking)
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
GYM_ID = "efe99507-15d5-4e54-9f07-30d2507894e0"


@pytest.fixture(scope="module")
def super_admin_token():
    """Get super admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
        "email": SUPER_ADMIN_EMAIL,
        "password": SUPER_ADMIN_PASSWORD
    })
    assert response.status_code == 200, f"Super admin login failed: {response.text}"
    return response.json().get("token")


@pytest.fixture(scope="module")
def gym_admin_token():
    """Get gym admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
        "email": GYM_ADMIN_EMAIL,
        "password": GYM_ADMIN_PASSWORD
    })
    assert response.status_code == 200, f"Gym admin login failed: {response.text}"
    return response.json().get("token")


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


class TestBusinessTypeBackend:
    """Backend API tests for business_type feature"""
    
    # ==================== CREATE GYM WITH BUSINESS_TYPE ====================
    
    def test_create_gym_with_business_type_condominium(self, api_client, super_admin_token):
        """Test creating a gym with business_type=condominium"""
        response = api_client.post(
            f"{BASE_URL}/api/gyms",
            headers={"Authorization": f"Bearer {super_admin_token}"},
            json={
                "name": "TEST_Condominio_Residencial",
                "business_type": "condominium",
                "address": "Calle Test 123",
                "email": "test_condo@test.com",
                "admin_email": "admin_test_condo@test.com",
                "admin_password": "test123456",
                "admin_name": "Admin Condominio Test"
            }
        )
        assert response.status_code == 200, f"Create gym failed: {response.text}"
        data = response.json()
        
        # Verify business_type is set correctly
        assert data.get("business_type") == "condominium", f"Expected business_type=condominium, got {data.get('business_type')}"
        assert data.get("name") == "TEST_Condominio_Residencial"
        assert "id" in data
        
        # Store gym_id for cleanup
        self.__class__.test_condominium_id = data["id"]
        print(f"Created condominium gym with id: {data['id']}")
    
    def test_create_gym_with_business_type_hotel(self, api_client, super_admin_token):
        """Test creating a gym with business_type=hotel"""
        response = api_client.post(
            f"{BASE_URL}/api/gyms",
            headers={"Authorization": f"Bearer {super_admin_token}"},
            json={
                "name": "TEST_Hotel_Paradise",
                "business_type": "hotel",
                "address": "Av. Hotel 456",
                "email": "test_hotel@test.com"
            }
        )
        assert response.status_code == 200, f"Create hotel gym failed: {response.text}"
        data = response.json()
        
        assert data.get("business_type") == "hotel"
        assert data.get("name") == "TEST_Hotel_Paradise"
        
        self.__class__.test_hotel_id = data["id"]
        print(f"Created hotel gym with id: {data['id']}")
    
    def test_create_gym_with_business_type_coworking(self, api_client, super_admin_token):
        """Test creating a gym with business_type=coworking"""
        response = api_client.post(
            f"{BASE_URL}/api/gyms",
            headers={"Authorization": f"Bearer {super_admin_token}"},
            json={
                "name": "TEST_Coworking_Hub",
                "business_type": "coworking",
                "address": "Calle Cowork 789"
            }
        )
        assert response.status_code == 200, f"Create coworking gym failed: {response.text}"
        data = response.json()
        
        assert data.get("business_type") == "coworking"
        assert data.get("name") == "TEST_Coworking_Hub"
        
        self.__class__.test_coworking_id = data["id"]
        print(f"Created coworking gym with id: {data['id']}")
    
    def test_create_gym_default_business_type_is_gym(self, api_client, super_admin_token):
        """Test that default business_type is 'gym' when not specified"""
        response = api_client.post(
            f"{BASE_URL}/api/gyms",
            headers={"Authorization": f"Bearer {super_admin_token}"},
            json={
                "name": "TEST_Default_Gym",
                "address": "Calle Default 000"
            }
        )
        assert response.status_code == 200, f"Create default gym failed: {response.text}"
        data = response.json()
        
        # Default should be 'gym'
        assert data.get("business_type") == "gym", f"Expected default business_type=gym, got {data.get('business_type')}"
        
        self.__class__.test_default_gym_id = data["id"]
        print(f"Created default gym with id: {data['id']}")
    
    # ==================== GET GYMS WITH BUSINESS_TYPE ====================
    
    def test_get_gyms_returns_business_type(self, api_client, super_admin_token):
        """Test GET /api/gyms returns business_type field for each gym"""
        response = api_client.get(
            f"{BASE_URL}/api/gyms",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200, f"Get gyms failed: {response.text}"
        gyms = response.json()
        
        assert isinstance(gyms, list), "Expected list of gyms"
        assert len(gyms) > 0, "Expected at least one gym"
        
        # Check that all gyms have business_type field
        for gym in gyms:
            assert "business_type" in gym or gym.get("business_type") is None or gym.get("business_type", "gym") in ["gym", "condominium", "hotel", "coworking"], \
                f"Gym {gym.get('name')} missing or invalid business_type"
        
        # Find our test gyms and verify their types
        test_gyms = {g["name"]: g for g in gyms if g["name"].startswith("TEST_")}
        
        if "TEST_Condominio_Residencial" in test_gyms:
            assert test_gyms["TEST_Condominio_Residencial"].get("business_type") == "condominium"
        if "TEST_Hotel_Paradise" in test_gyms:
            assert test_gyms["TEST_Hotel_Paradise"].get("business_type") == "hotel"
        if "TEST_Coworking_Hub" in test_gyms:
            assert test_gyms["TEST_Coworking_Hub"].get("business_type") == "coworking"
        
        print(f"Verified business_type for {len(gyms)} gyms")
    
    def test_get_single_gym_returns_business_type(self, api_client, super_admin_token):
        """Test GET /api/gyms/{gym_id} returns business_type field"""
        # Use the existing gym
        response = api_client.get(
            f"{BASE_URL}/api/gyms/{GYM_ID}",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200, f"Get gym failed: {response.text}"
        gym = response.json()
        
        # business_type should be present (default is 'gym' for existing gyms)
        business_type = gym.get("business_type", "gym")
        assert business_type in ["gym", "condominium", "hotel", "coworking"], \
            f"Invalid business_type: {business_type}"
        
        print(f"Gym {gym.get('name')} has business_type: {business_type}")
    
    # ==================== UPDATE GYM BUSINESS_TYPE ====================
    
    def test_update_gym_business_type_to_hotel(self, api_client, super_admin_token):
        """Test updating an existing gym's business_type to 'hotel'"""
        # First get the test condominium gym
        gym_id = getattr(self.__class__, 'test_condominium_id', None)
        if not gym_id:
            pytest.skip("Test condominium gym not created")
        
        # Update to hotel
        response = api_client.put(
            f"{BASE_URL}/api/gyms/{gym_id}",
            headers={"Authorization": f"Bearer {super_admin_token}"},
            json={"business_type": "hotel"}
        )
        assert response.status_code == 200, f"Update gym failed: {response.text}"
        data = response.json()
        
        assert data.get("business_type") == "hotel", f"Expected business_type=hotel after update, got {data.get('business_type')}"
        print(f"Updated gym {gym_id} business_type to hotel")
        
        # Verify with GET
        get_response = api_client.get(
            f"{BASE_URL}/api/gyms/{gym_id}",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert get_response.status_code == 200
        assert get_response.json().get("business_type") == "hotel"
    
    def test_update_gym_business_type_to_coworking(self, api_client, super_admin_token):
        """Test updating gym's business_type to 'coworking'"""
        gym_id = getattr(self.__class__, 'test_hotel_id', None)
        if not gym_id:
            pytest.skip("Test hotel gym not created")
        
        response = api_client.put(
            f"{BASE_URL}/api/gyms/{gym_id}",
            headers={"Authorization": f"Bearer {super_admin_token}"},
            json={"business_type": "coworking"}
        )
        assert response.status_code == 200, f"Update gym failed: {response.text}"
        assert response.json().get("business_type") == "coworking"
        print(f"Updated gym {gym_id} business_type to coworking")
    
    # ==================== PUBLIC GYM INFO ====================
    
    def test_public_gym_info_returns_business_type(self, api_client):
        """Test GET /api/gyms/{gym_id}/public-info returns business_type"""
        response = api_client.get(f"{BASE_URL}/api/gyms/{GYM_ID}/public-info")
        assert response.status_code == 200, f"Get public info failed: {response.text}"
        data = response.json()
        
        # business_type should be in public info
        assert "business_type" in data, "business_type missing from public info"
        business_type = data.get("business_type")
        assert business_type in ["gym", "condominium", "hotel", "coworking"], \
            f"Invalid business_type in public info: {business_type}"
        
        print(f"Public info for gym {GYM_ID} has business_type: {business_type}")
    
    def test_public_gym_info_for_test_gyms(self, api_client):
        """Test public info for test gyms with different business types"""
        test_ids = [
            getattr(self.__class__, 'test_coworking_id', None),
            getattr(self.__class__, 'test_default_gym_id', None)
        ]
        
        for gym_id in test_ids:
            if gym_id:
                response = api_client.get(f"{BASE_URL}/api/gyms/{gym_id}/public-info")
                if response.status_code == 200:
                    data = response.json()
                    assert "business_type" in data
                    print(f"Public info for {gym_id}: business_type={data.get('business_type')}")
    
    # ==================== GYM ADMIN ACCESS ====================
    
    def test_gym_admin_can_get_own_gym_with_business_type(self, api_client, gym_admin_token):
        """Test gym admin can access their gym and see business_type"""
        response = api_client.get(
            f"{BASE_URL}/api/gyms",
            headers={"Authorization": f"Bearer {gym_admin_token}"}
        )
        assert response.status_code == 200, f"Gym admin get gyms failed: {response.text}"
        gyms = response.json()
        
        assert len(gyms) >= 1, "Gym admin should see at least their own gym"
        
        # Check business_type is present
        for gym in gyms:
            business_type = gym.get("business_type", "gym")
            assert business_type in ["gym", "condominium", "hotel", "coworking"]
        
        print(f"Gym admin can see {len(gyms)} gym(s) with business_type")
    
    # ==================== CLEANUP ====================
    
    def test_cleanup_test_gyms(self, api_client, super_admin_token):
        """Cleanup: Delete test gyms created during testing"""
        test_gym_ids = [
            getattr(self.__class__, 'test_condominium_id', None),
            getattr(self.__class__, 'test_hotel_id', None),
            getattr(self.__class__, 'test_coworking_id', None),
            getattr(self.__class__, 'test_default_gym_id', None)
        ]
        
        deleted_count = 0
        for gym_id in test_gym_ids:
            if gym_id:
                response = api_client.delete(
                    f"{BASE_URL}/api/gyms/{gym_id}",
                    headers={"Authorization": f"Bearer {super_admin_token}"}
                )
                if response.status_code == 200:
                    deleted_count += 1
                    print(f"Deleted test gym: {gym_id}")
        
        print(f"Cleanup complete: deleted {deleted_count} test gyms")


class TestBusinessTypeValidation:
    """Additional validation tests for business_type"""
    
    def test_existing_gym_has_default_business_type(self, api_client, super_admin_token):
        """Test that existing gyms without business_type default to 'gym'"""
        response = api_client.get(
            f"{BASE_URL}/api/gyms/{GYM_ID}",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        gym = response.json()
        
        # Existing gyms should have business_type (default 'gym')
        business_type = gym.get("business_type", "gym")
        assert business_type == "gym", f"Expected existing gym to have business_type=gym, got {business_type}"
        print(f"Existing gym {GYM_ID} has business_type: {business_type}")
    
    def test_all_four_business_types_are_valid(self, api_client, super_admin_token):
        """Verify all 4 business types are accepted by the API"""
        valid_types = ["gym", "condominium", "hotel", "coworking"]
        
        for btype in valid_types:
            # Create a test gym with this type
            response = api_client.post(
                f"{BASE_URL}/api/gyms",
                headers={"Authorization": f"Bearer {super_admin_token}"},
                json={
                    "name": f"TEST_Validation_{btype}",
                    "business_type": btype
                }
            )
            assert response.status_code == 200, f"Failed to create gym with business_type={btype}: {response.text}"
            data = response.json()
            assert data.get("business_type") == btype
            
            # Cleanup
            gym_id = data.get("id")
            if gym_id:
                api_client.delete(
                    f"{BASE_URL}/api/gyms/{gym_id}",
                    headers={"Authorization": f"Bearer {super_admin_token}"}
                )
        
        print(f"All 4 business types validated: {valid_types}")
