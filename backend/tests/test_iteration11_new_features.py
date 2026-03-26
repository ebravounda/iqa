"""
Iteration 11 Tests: Excel Export, Phone Column, Datos Page, Gym Selector for Super Admin, Static QR Validation
Tests for new features: Excel member export, phone number column, 'Datos' menu, gym selector in Analytics/POS/Forms pages.
"""
import pytest
import requests
import os
import uuid
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://stripe-gym-payments.preview.emergentagent.com')

# Test credentials
SUPER_ADMIN_EMAIL = "admin@gymaccess.com"
SUPER_ADMIN_PASSWORD = "admin123"


class TestAuthAndHealth:
    """Basic health and authentication tests"""
    
    def test_health_endpoint(self):
        """Test /api/health returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✓ Health endpoint working")
    
    def test_super_admin_login(self):
        """Test super admin login at /api/auth/admin/login"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["admin"]["role"] == "super_admin"
        # Super admin should have gym_id = null
        assert data["admin"].get("gym_id") is None
        print(f"✓ Super admin login successful, role: {data['admin']['role']}, gym_id: {data['admin'].get('gym_id')}")
        return data["token"]


class TestExcelExport:
    """Tests for Excel member export endpoint"""
    
    @pytest.fixture
    def auth_token(self):
        """Get super admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    @pytest.fixture
    def gym_id(self, auth_token):
        """Get first available gym ID"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/gyms", headers=headers)
        gyms = response.json()
        if gyms:
            return gyms[0]["id"]
        return None
    
    def test_export_members_excel_endpoint_exists(self, auth_token, gym_id):
        """GET /api/members/export/excel - endpoint exists and returns Excel file"""
        if not gym_id:
            pytest.skip("No gym available for testing")
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/members/export/excel?gym_id={gym_id}", headers=headers)
        
        assert response.status_code == 200
        # Check content type is Excel
        content_type = response.headers.get("Content-Type", "")
        assert "spreadsheetml" in content_type or "application/vnd.openxmlformats" in content_type
        
        # Check content-disposition header for filename
        content_disposition = response.headers.get("Content-Disposition", "")
        assert "attachment" in content_disposition
        assert ".xlsx" in content_disposition
        
        # Check that we got actual content
        assert len(response.content) > 0
        
        print(f"✓ GET /api/members/export/excel returns Excel file, size: {len(response.content)} bytes")
        print(f"  Content-Disposition: {content_disposition}")
    
    def test_export_members_excel_without_gym_id(self, auth_token):
        """GET /api/members/export/excel - super admin can export without gym_id (all gyms)"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/members/export/excel", headers=headers)
        
        assert response.status_code == 200
        content_type = response.headers.get("Content-Type", "")
        assert "spreadsheetml" in content_type or "application/vnd.openxmlformats" in content_type
        
        print(f"✓ Super admin can export all members without gym_id filter")


class TestMemberPhoneField:
    """Tests for phone number field in members"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    @pytest.fixture
    def gym_id(self, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/gyms", headers=headers)
        gyms = response.json()
        return gyms[0]["id"] if gyms else None
    
    def test_create_member_with_phone(self, auth_token, gym_id):
        """POST /api/members - create member with phone number"""
        if not gym_id:
            pytest.skip("No gym available")
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        member_data = {
            "name": f"TEST_Phone_Member_{uuid.uuid4().hex[:6]}",
            "email": f"test_phone_{uuid.uuid4().hex[:6]}@test.com",
            "phone": "+1 555 123 4567",
            "gym_id": gym_id,
            "gender": "prefer_not_to_say"
        }
        response = requests.post(f"{BASE_URL}/api/members", json=member_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["phone"] == "+1 555 123 4567"
        assert "id" in data
        print(f"✓ Created member with phone: {data['phone']}")
        return data
    
    def test_update_member_phone(self, auth_token, gym_id):
        """PUT /api/members/{id} - update member phone number"""
        if not gym_id:
            pytest.skip("No gym available")
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create member first
        member_data = {
            "name": f"TEST_Update_Phone_{uuid.uuid4().hex[:6]}",
            "email": f"test_update_phone_{uuid.uuid4().hex[:6]}@test.com",
            "gym_id": gym_id
        }
        create_response = requests.post(f"{BASE_URL}/api/members", json=member_data, headers=headers)
        member_id = create_response.json()["id"]
        
        # Update phone
        update_response = requests.put(
            f"{BASE_URL}/api/members/{member_id}",
            json={"phone": "+34 612 345 678"},
            headers=headers
        )
        assert update_response.status_code == 200
        updated_data = update_response.json()
        assert updated_data["phone"] == "+34 612 345 678"
        print(f"✓ Updated member phone to: {updated_data['phone']}")
    
    def test_get_members_includes_phone(self, auth_token, gym_id):
        """GET /api/members - response includes phone field"""
        if not gym_id:
            pytest.skip("No gym available")
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create member with phone
        member_data = {
            "name": f"TEST_Get_Phone_{uuid.uuid4().hex[:6]}",
            "email": f"test_get_phone_{uuid.uuid4().hex[:6]}@test.com",
            "phone": "+52 55 1234 5678",
            "gym_id": gym_id
        }
        requests.post(f"{BASE_URL}/api/members", json=member_data, headers=headers)
        
        # Get members
        response = requests.get(f"{BASE_URL}/api/members?gym_id={gym_id}", headers=headers)
        assert response.status_code == 200
        members = response.json()
        
        # Find our test member
        test_member = next((m for m in members if m["email"] == member_data["email"]), None)
        assert test_member is not None
        assert "phone" in test_member
        assert test_member["phone"] == "+52 55 1234 5678"
        print(f"✓ GET /api/members includes phone field")


class TestStaticQRValidation:
    """Tests for static QR validation (for Raspberry Pi)"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    @pytest.fixture
    def gym_with_member(self, auth_token):
        """Create a gym with a member that has static QR enabled"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get gyms
        response = requests.get(f"{BASE_URL}/api/gyms", headers=headers)
        gyms = response.json()
        if not gyms:
            pytest.skip("No gyms available")
        
        gym = gyms[0]
        gym_id = gym["id"]
        api_token = gym.get("api_token")
        
        # Create a member
        member_data = {
            "name": f"TEST_Static_QR_{uuid.uuid4().hex[:6]}",
            "email": f"test_static_qr_{uuid.uuid4().hex[:6]}@test.com",
            "gym_id": gym_id
        }
        member_response = requests.post(f"{BASE_URL}/api/members", json=member_data, headers=headers)
        member = member_response.json()
        
        # Create a plan and membership for the member
        plan_response = requests.get(f"{BASE_URL}/api/plans?gym_id={gym_id}", headers=headers)
        plans = plan_response.json()
        
        if plans:
            plan_id = plans[0]["id"]
            # Create membership
            membership_data = {
                "member_id": member["id"],
                "plan_id": plan_id
            }
            requests.post(f"{BASE_URL}/api/memberships", json=membership_data, headers=headers)
        
        return {
            "gym_id": gym_id,
            "api_token": api_token,
            "member": member
        }
    
    def test_set_member_qr_mode_static(self, auth_token, gym_with_member):
        """PUT /api/members/{id}/qr-mode - set member to static QR mode"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        member_id = gym_with_member["member"]["id"]
        
        response = requests.put(
            f"{BASE_URL}/api/members/{member_id}/qr-mode",
            json={"qr_mode": "static"},
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "static" in data["message"]
        print(f"✓ Set member QR mode to static: {data['message']}")
    
    def test_access_self_test_static_qr(self, auth_token):
        """GET /api/access/self-test - verify static QR validation works"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/access/self-test", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "static_qr_test" in data
        assert data["static_qr_test"]["valid"] == True
        
        print(f"✓ Static QR self-test passed: {data['static_qr_test']}")
    
    def test_dynamic_qr_validation(self, auth_token):
        """GET /api/access/self-test - verify dynamic QR validation works"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/access/self-test", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "dynamic_qr_test" in data
        assert data["dynamic_qr_test"]["valid"] == True
        
        print(f"✓ Dynamic QR self-test passed: {data['dynamic_qr_test']}")


class TestAnalyticsEndpoints:
    """Tests for Analytics endpoints with gym_id parameter"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    @pytest.fixture
    def gym_id(self, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/gyms", headers=headers)
        gyms = response.json()
        return gyms[0]["id"] if gyms else None
    
    def test_analytics_overview_with_gym_id(self, auth_token, gym_id):
        """GET /api/analytics/overview - works with gym_id parameter"""
        if not gym_id:
            pytest.skip("No gym available")
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/analytics/overview?gym_id={gym_id}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "active_members" in data
        assert "total_members" in data
        assert "retention_rate" in data
        print(f"✓ GET /api/analytics/overview with gym_id: active_members={data['active_members']}")
    
    def test_hourly_heatmap_with_gym_id(self, auth_token, gym_id):
        """GET /api/analytics/hourly-heatmap - works with gym_id parameter"""
        if not gym_id:
            pytest.skip("No gym available")
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/analytics/hourly-heatmap?gym_id={gym_id}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/analytics/hourly-heatmap with gym_id: {len(data)} data points")
    
    def test_peak_hours_with_gym_id(self, auth_token, gym_id):
        """GET /api/analytics/peak-hours - works with gym_id parameter"""
        if not gym_id:
            pytest.skip("No gym available")
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/analytics/peak-hours?gym_id={gym_id}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "hourly" in data or "peak_hour" in data
        print(f"✓ GET /api/analytics/peak-hours with gym_id")


class TestPOSWithGymSelector:
    """Tests for POS endpoints with gym_id parameter (for super admin)"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    @pytest.fixture
    def gym_id(self, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/gyms", headers=headers)
        gyms = response.json()
        return gyms[0]["id"] if gyms else None
    
    def test_pos_products_with_gym_id(self, auth_token, gym_id):
        """GET /api/pos/products - works with gym_id parameter"""
        if not gym_id:
            pytest.skip("No gym available")
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/pos/products?gym_id={gym_id}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/pos/products with gym_id: {len(data)} products")
    
    def test_pos_stats_with_gym_id(self, auth_token, gym_id):
        """GET /api/pos/stats - works with gym_id parameter"""
        if not gym_id:
            pytest.skip("No gym available")
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/pos/stats?gym_id={gym_id}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "today_sales" in data
        assert "today_revenue" in data
        print(f"✓ GET /api/pos/stats with gym_id: today_sales={data['today_sales']}")


class TestFormsWithGymSelector:
    """Tests for Forms endpoints with gym_id parameter (for super admin)"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    @pytest.fixture
    def gym_id(self, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/gyms", headers=headers)
        gyms = response.json()
        return gyms[0]["id"] if gyms else None
    
    def test_get_forms_with_gym_id(self, auth_token, gym_id):
        """GET /api/forms - works with gym_id parameter"""
        if not gym_id:
            pytest.skip("No gym available")
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/forms?gym_id={gym_id}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/forms with gym_id: {len(data)} forms")
    
    def test_create_form_with_gym_id(self, auth_token, gym_id):
        """POST /api/forms - create form with gym_id"""
        if not gym_id:
            pytest.skip("No gym available")
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        form_data = {
            "name": f"TEST_Form_{uuid.uuid4().hex[:6]}",
            "description": "Test form for iteration 11",
            "gym_id": gym_id,
            "show_on_registration": True,
            "fields": [
                {"label": "Test Question", "field_type": "text", "required": False}
            ]
        }
        response = requests.post(f"{BASE_URL}/api/forms", json=form_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == form_data["name"]
        assert data["gym_id"] == gym_id
        print(f"✓ Created form with gym_id: {data['name']}")


class TestGymsEndpoint:
    """Tests for gyms endpoint (needed for gym selector)"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_get_gyms_as_super_admin(self, auth_token):
        """GET /api/gyms - super admin can get all gyms"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/gyms", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0  # Should have at least one gym
        
        # Each gym should have id and name
        for gym in data:
            assert "id" in gym
            assert "name" in gym
        
        print(f"✓ GET /api/gyms returned {len(data)} gyms")
        for gym in data[:3]:  # Print first 3
            print(f"  - {gym['name']} (id: {gym['id'][:8]}...)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
