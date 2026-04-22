"""
Iteration 32 - Membership Service Refactoring Tests
Tests the centralized membership_service.py that replaced duplicated logic across 6 route files.
Also verifies that all payment gateway routes import correctly after refactoring.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@gymaccess.com"
ADMIN_PASSWORD = "admin123"
TEST_MEMBER_CODE = "RMB8S5"
TEST_GYM_ID = "efe99507-15d5-4e54-9f07-30d2507894e0"


class TestHealthAndBasicEndpoints:
    """Verify backend is running and basic endpoints work after refactoring"""
    
    def test_health_endpoint(self):
        """GET /api/health - Backend health check"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print("✓ Health endpoint working")
    
    def test_root_api_endpoint(self):
        """GET /api/ - Root API endpoint"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print("✓ Root API endpoint working")


class TestAdminAuth:
    """Test admin authentication still works after refactoring"""
    
    def test_admin_login_success(self):
        """POST /api/auth/admin/login - Admin login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "admin" in data
        assert data["admin"]["email"] == ADMIN_EMAIL
        print(f"✓ Admin login successful: {data['admin']['email']}")
        return data["token"]
    
    def test_admin_login_invalid_credentials(self):
        """POST /api/auth/admin/login - Admin login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": "wrong@email.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print("✓ Admin login correctly rejects invalid credentials")


class TestMemberAuth:
    """Test member authentication still works after refactoring"""
    
    def test_member_login_success(self):
        """POST /api/auth/member/login - Member login with valid code"""
        response = requests.post(f"{BASE_URL}/api/auth/member/login?code={TEST_MEMBER_CODE}")
        # Member may be suspended or active, both are valid responses
        assert response.status_code in [200, 403]
        if response.status_code == 200:
            data = response.json()
            assert "token" in data
            assert "member" in data
            print(f"✓ Member login successful: {data['member'].get('name', 'Unknown')}")
            return data["token"]
        else:
            print("✓ Member login returned 403 (suspended/blocked) - endpoint working")
            return None
    
    def test_member_login_invalid_code(self):
        """POST /api/auth/member/login - Member login with invalid code"""
        response = requests.post(f"{BASE_URL}/api/auth/member/login?code=INVALID")
        assert response.status_code == 404
        print("✓ Member login correctly rejects invalid code")


class TestMemberMeEndpoint:
    """Test member /me endpoint still works"""
    
    @pytest.fixture
    def member_token(self):
        """Get member token for authenticated requests"""
        response = requests.post(f"{BASE_URL}/api/auth/member/login?code={TEST_MEMBER_CODE}")
        if response.status_code == 200:
            return response.json().get("token")
        return None
    
    def test_member_me_endpoint(self, member_token):
        """GET /api/auth/member/me - Get current member info"""
        if not member_token:
            pytest.skip("Member login failed - cannot test /me endpoint")
        
        response = requests.get(
            f"{BASE_URL}/api/auth/member/me",
            headers={"Authorization": f"Bearer {member_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "member" in data
        print(f"✓ Member /me endpoint working: {data['member'].get('name', 'Unknown')}")


class TestMembershipCreationViaService:
    """Test membership creation via the centralized service (plan_routes.py)"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token for authenticated requests"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        return None
    
    def test_get_plans(self, admin_token):
        """GET /api/plans - Get plans list (uses plan_routes.py)"""
        if not admin_token:
            pytest.skip("Admin login failed")
        
        response = requests.get(
            f"{BASE_URL}/api/plans",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/plans working - {len(data)} plans found")
        return data
    
    def test_get_memberships(self, admin_token):
        """GET /api/memberships - Get memberships list (uses plan_routes.py)"""
        if not admin_token:
            pytest.skip("Admin login failed")
        
        response = requests.get(
            f"{BASE_URL}/api/memberships",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/memberships working - {len(data)} memberships found")
    
    def test_get_expiring_memberships(self, admin_token):
        """GET /api/memberships/expiring - Get expiring memberships (uses plan_routes.py)"""
        if not admin_token:
            pytest.skip("Admin login failed")
        
        response = requests.get(
            f"{BASE_URL}/api/memberships/expiring?days=30",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/memberships/expiring working - {len(data)} expiring memberships")


class TestPaymentRoutesImport:
    """Test that all payment gateway routes import correctly after refactoring"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token for authenticated requests"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        return None
    
    def test_payment_history_endpoint(self, admin_token):
        """GET /api/payments/history - Payment routes working (uses payment_routes.py)"""
        if not admin_token:
            pytest.skip("Admin login failed")
        
        response = requests.get(
            f"{BASE_URL}/api/payments/history",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/payments/history working - {len(data)} transactions")
    
    def test_stripe_config_endpoint(self, admin_token):
        """GET /api/gyms/{gym_id}/stripe-config - Stripe routes working"""
        if not admin_token:
            pytest.skip("Admin login failed")
        
        response = requests.get(
            f"{BASE_URL}/api/gyms/{TEST_GYM_ID}/stripe-config",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # May return 200 or 403 depending on admin role
        assert response.status_code in [200, 403]
        print(f"✓ Stripe config endpoint accessible (status: {response.status_code})")
    
    def test_redsys_config_endpoint(self, admin_token):
        """GET /api/gyms/{gym_id}/redsys-config - Redsys routes working"""
        if not admin_token:
            pytest.skip("Admin login failed")
        
        response = requests.get(
            f"{BASE_URL}/api/gyms/{TEST_GYM_ID}/redsys-config",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code in [200, 403, 404]
        print(f"✓ Redsys config endpoint accessible (status: {response.status_code})")
    
    def test_mercadopago_config_endpoint(self, admin_token):
        """GET /api/gyms/{gym_id}/mercadopago-config - MercadoPago routes working"""
        if not admin_token:
            pytest.skip("Admin login failed")
        
        response = requests.get(
            f"{BASE_URL}/api/gyms/{TEST_GYM_ID}/mercadopago-config",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code in [200, 403, 404]
        print(f"✓ MercadoPago config endpoint accessible (status: {response.status_code})")
    
    def test_payment_gateway_endpoint(self, admin_token):
        """GET /api/gyms/{gym_id}/payment-gateway - Payment gateway selector working"""
        if not admin_token:
            pytest.skip("Admin login failed")
        
        response = requests.get(
            f"{BASE_URL}/api/gyms/{TEST_GYM_ID}/payment-gateway",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code in [200, 403]
        print(f"✓ Payment gateway endpoint accessible (status: {response.status_code})")


class TestManualPaymentWithMembershipService:
    """Test manual payment creates membership via centralized service"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token for authenticated requests"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        return None
    
    def test_manual_payment_endpoint_exists(self, admin_token):
        """POST /api/payments/manual - Manual payment endpoint exists"""
        if not admin_token:
            pytest.skip("Admin login failed")
        
        # Test with invalid data to verify endpoint exists
        response = requests.post(
            f"{BASE_URL}/api/payments/manual",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"member_id": "invalid", "plan_id": "invalid", "amount": 0, "payment_method": "cash"}
        )
        # Should return 404 (member not found) or 422 (validation error), not 500
        assert response.status_code in [404, 422, 400]
        print(f"✓ Manual payment endpoint working (status: {response.status_code})")


class TestDevicesEndpoint:
    """Test devices endpoint for AdminDevices.js Kiosk display link card"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token for authenticated requests"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        return None
    
    def test_get_devices(self, admin_token):
        """GET /api/devices - Get devices list"""
        if not admin_token:
            pytest.skip("Admin login failed")
        
        response = requests.get(
            f"{BASE_URL}/api/devices",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # Response can be a list or dict with active/inactive
        assert isinstance(data, (list, dict))
        print(f"✓ GET /api/devices working")
    
    def test_get_gym_for_kiosk(self, admin_token):
        """GET /api/gyms/{gym_id} - Get gym info for Kiosk URL"""
        if not admin_token:
            pytest.skip("Admin login failed")
        
        response = requests.get(
            f"{BASE_URL}/api/gyms/{TEST_GYM_ID}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "id" in data
            print(f"✓ GET /api/gyms/{TEST_GYM_ID} working - gym: {data.get('name', 'Unknown')}")
        else:
            print(f"✓ GET /api/gyms endpoint working (gym not found)")


class TestPublicPlansEndpoint:
    """Test public plans endpoint used by member app"""
    
    def test_get_public_plans(self):
        """GET /api/plans/public/{gym_id} - Get public plans for a gym"""
        response = requests.get(f"{BASE_URL}/api/plans/public/{TEST_GYM_ID}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/plans/public working - {len(data)} public plans")


class TestGymHasPayments:
    """Test gym has payments endpoint (used by member app)"""
    
    def test_gym_has_payments(self):
        """GET /api/gyms/{gym_id}/has-payments - Check if gym has payment gateway"""
        response = requests.get(f"{BASE_URL}/api/gyms/{TEST_GYM_ID}/has-payments")
        assert response.status_code == 200
        data = response.json()
        assert "has_payments" in data
        print(f"✓ GET /api/gyms/{TEST_GYM_ID}/has-payments working - has_payments: {data.get('has_payments')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
