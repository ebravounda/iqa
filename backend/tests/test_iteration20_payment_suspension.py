"""
Iteration 20 - Payment Suspension Feature Tests
Tests for the payment suspension system that allows Super Admin to suspend gyms for non-payment.
When suspended:
1. Gym Admin sees fullscreen 'Cuenta Suspendida por falta de pago' with contact info
2. Members see 'Cuenta Bloqueada' screen
3. QR access is blocked on Raspberry Pi
4. Badge 'IMPAGO' shown on gym card in Super Admin
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
SUPER_ADMIN_EMAIL = "admin@ingresoqr.com"
SUPER_ADMIN_PASSWORD = "admin123"
GYM_ADMIN_EMAIL = "admin@fitzone.com"
GYM_ADMIN_PASSWORD = "admin123"
MEMBER_CODE = "NEDFJR"


class TestPaymentSuspensionBackend:
    """Tests for payment suspension backend APIs"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
    def get_super_admin_token(self):
        """Get Super Admin authentication token"""
        response = self.session.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Super Admin login failed: {response.text}"
        return response.json()["token"]
    
    def get_gym_admin_token(self):
        """Get Gym Admin authentication token"""
        response = self.session.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": GYM_ADMIN_EMAIL,
            "password": GYM_ADMIN_PASSWORD
        })
        return response
    
    def get_fitzone_gym_id(self, token):
        """Get FitZone Gym ID"""
        response = self.session.get(
            f"{BASE_URL}/api/gyms",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Failed to get gyms: {response.text}"
        gyms = response.json()
        fitzone = next((g for g in gyms if g.get("name") == "FitZone Gym"), None)
        assert fitzone is not None, "FitZone Gym not found"
        return fitzone["id"], fitzone.get("api_token")
    
    def get_gym_status(self, token, gym_id):
        """Get current gym status"""
        response = self.session.get(
            f"{BASE_URL}/api/gyms/{gym_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        return response.json().get("status")
    
    # ==================== PAYMENT SUSPEND ENDPOINT TESTS ====================
    
    def test_01_super_admin_login(self):
        """Test Super Admin can login successfully"""
        response = self.session.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["admin"]["role"] == "super_admin"
        print("✓ Super Admin login successful")
    
    def test_02_get_fitzone_gym(self):
        """Test getting FitZone Gym details"""
        token = self.get_super_admin_token()
        gym_id, api_token = self.get_fitzone_gym_id(token)
        assert gym_id is not None
        assert api_token is not None
        print(f"✓ FitZone Gym found with ID: {gym_id}")
    
    def test_03_payment_suspend_requires_super_admin(self):
        """Test that payment-suspend endpoint requires Super Admin role"""
        # First login as gym admin
        gym_admin_response = self.get_gym_admin_token()
        if gym_admin_response.status_code != 200:
            pytest.skip("Gym admin login failed - gym may be suspended")
        
        gym_admin_token = gym_admin_response.json()["token"]
        
        # Get gym ID using super admin
        super_token = self.get_super_admin_token()
        gym_id, _ = self.get_fitzone_gym_id(super_token)
        
        # Try to suspend as gym admin - should fail
        response = self.session.put(
            f"{BASE_URL}/api/gyms/{gym_id}/payment-suspend",
            headers={"Authorization": f"Bearer {gym_admin_token}"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✓ Payment suspend correctly requires Super Admin role")
    
    def test_04_payment_suspend_toggle_to_suspended(self):
        """Test suspending a gym for non-payment"""
        token = self.get_super_admin_token()
        gym_id, _ = self.get_fitzone_gym_id(token)
        
        # Check current status
        current_status = self.get_gym_status(token, gym_id)
        print(f"Current gym status: {current_status}")
        
        # If already payment_suspended, reactivate first
        if current_status == "payment_suspended":
            response = self.session.put(
                f"{BASE_URL}/api/gyms/{gym_id}/payment-suspend",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 200
            current_status = self.get_gym_status(token, gym_id)
            print(f"Reactivated gym, new status: {current_status}")
        
        # Now suspend for payment
        response = self.session.put(
            f"{BASE_URL}/api/gyms/{gym_id}/payment-suspend",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "payment_suspended", f"Expected 'payment_suspended', got {data['status']}"
        assert "suspendido por falta de pago" in data["message"].lower() or "suspendido" in data["message"].lower()
        print(f"✓ Gym suspended for non-payment: {data['message']}")
    
    def test_05_gym_admin_login_returns_payment_suspended_status(self):
        """Test that gym admin login returns gym_status='payment_suspended'"""
        # First ensure gym is suspended
        super_token = self.get_super_admin_token()
        gym_id, _ = self.get_fitzone_gym_id(super_token)
        
        current_status = self.get_gym_status(super_token, gym_id)
        if current_status != "payment_suspended":
            # Suspend it
            self.session.put(
                f"{BASE_URL}/api/gyms/{gym_id}/payment-suspend",
                headers={"Authorization": f"Bearer {super_token}"}
            )
        
        # Now login as gym admin
        response = self.session.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": GYM_ADMIN_EMAIL,
            "password": GYM_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Gym admin login failed: {response.text}"
        data = response.json()
        assert data["admin"].get("gym_status") == "payment_suspended", \
            f"Expected gym_status='payment_suspended', got {data['admin'].get('gym_status')}"
        print("✓ Gym admin login returns gym_status='payment_suspended'")
    
    def test_06_member_login_blocked_when_gym_suspended(self):
        """Test that member login returns 403 'Cuenta Bloqueada' when gym is suspended"""
        # Ensure gym is suspended
        super_token = self.get_super_admin_token()
        gym_id, _ = self.get_fitzone_gym_id(super_token)
        
        current_status = self.get_gym_status(super_token, gym_id)
        if current_status != "payment_suspended":
            self.session.put(
                f"{BASE_URL}/api/gyms/{gym_id}/payment-suspend",
                headers={"Authorization": f"Bearer {super_token}"}
            )
        
        # Try member login - code is query parameter
        response = self.session.post(f"{BASE_URL}/api/auth/member/login?code={MEMBER_CODE}")
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        data = response.json()
        assert "Bloqueada" in data.get("detail", ""), f"Expected 'Cuenta Bloqueada', got {data}"
        print("✓ Member login blocked with 'Cuenta Bloqueada' when gym suspended")
    
    def test_07_member_me_blocked_when_gym_suspended(self):
        """Test that GET /api/auth/member/me returns 403 when gym is suspended"""
        # First we need a member token - but member login is blocked
        # This test verifies the endpoint behavior if a member had a valid token
        # We'll skip this if we can't get a token
        
        # Reactivate gym temporarily to get member token
        super_token = self.get_super_admin_token()
        gym_id, _ = self.get_fitzone_gym_id(super_token)
        
        # Reactivate
        self.session.put(
            f"{BASE_URL}/api/gyms/{gym_id}/payment-suspend",
            headers={"Authorization": f"Bearer {super_token}"}
        )
        
        # Login as member
        response = self.session.post(f"{BASE_URL}/api/auth/member/login?code={MEMBER_CODE}")
        if response.status_code != 200:
            pytest.skip(f"Could not get member token: {response.text}")
        
        member_token = response.json()["token"]
        
        # Suspend gym again
        self.session.put(
            f"{BASE_URL}/api/gyms/{gym_id}/payment-suspend",
            headers={"Authorization": f"Bearer {super_token}"}
        )
        
        # Now try to access /me endpoint
        response = self.session.get(
            f"{BASE_URL}/api/auth/member/me",
            headers={"Authorization": f"Bearer {member_token}"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        data = response.json()
        assert "Bloqueada" in data.get("detail", ""), f"Expected 'Cuenta Bloqueada', got {data}"
        print("✓ Member /me endpoint blocked when gym suspended")
    
    def test_08_qr_access_blocked_when_gym_suspended(self):
        """Test that QR access validation returns valid=false when gym is suspended"""
        super_token = self.get_super_admin_token()
        gym_id, api_token = self.get_fitzone_gym_id(super_token)
        
        # Ensure gym is suspended
        current_status = self.get_gym_status(super_token, gym_id)
        if current_status != "payment_suspended":
            self.session.put(
                f"{BASE_URL}/api/gyms/{gym_id}/payment-suspend",
                headers={"Authorization": f"Bearer {super_token}"}
            )
        
        # Try to validate QR access
        response = self.session.post(f"{BASE_URL}/api/access/validate", json={
            "qr_code": "test_qr_code_data",
            "gym_token": api_token,
            "direction": "entrada"
        })
        assert response.status_code == 200  # Endpoint returns 200 with valid=false
        data = response.json()
        assert data.get("valid") == False, f"Expected valid=false, got {data}"
        assert "suspendido" in data.get("reason", "").lower() or "pago" in data.get("reason", "").lower(), \
            f"Expected reason about suspension, got {data.get('reason')}"
        print(f"✓ QR access blocked with reason: {data.get('reason')}")
    
    def test_09_payment_suspend_toggle_to_active(self):
        """Test reactivating a gym (toggle back to active)"""
        token = self.get_super_admin_token()
        gym_id, _ = self.get_fitzone_gym_id(token)
        
        # Ensure gym is suspended first
        current_status = self.get_gym_status(token, gym_id)
        if current_status != "payment_suspended":
            self.session.put(
                f"{BASE_URL}/api/gyms/{gym_id}/payment-suspend",
                headers={"Authorization": f"Bearer {token}"}
            )
        
        # Now reactivate
        response = self.session.put(
            f"{BASE_URL}/api/gyms/{gym_id}/payment-suspend",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active", f"Expected 'active', got {data['status']}"
        assert "reactivado" in data["message"].lower()
        print(f"✓ Gym reactivated: {data['message']}")
    
    def test_10_gym_admin_can_access_after_reactivation(self):
        """Test that gym admin can access dashboard normally after reactivation"""
        # Ensure gym is active
        super_token = self.get_super_admin_token()
        gym_id, _ = self.get_fitzone_gym_id(super_token)
        
        current_status = self.get_gym_status(super_token, gym_id)
        if current_status == "payment_suspended":
            self.session.put(
                f"{BASE_URL}/api/gyms/{gym_id}/payment-suspend",
                headers={"Authorization": f"Bearer {super_token}"}
            )
        
        # Login as gym admin
        response = self.session.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": GYM_ADMIN_EMAIL,
            "password": GYM_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        # gym_status should be 'active' or None (not payment_suspended)
        gym_status = data["admin"].get("gym_status")
        assert gym_status != "payment_suspended", f"Expected active status, got {gym_status}"
        print(f"✓ Gym admin can login normally after reactivation (gym_status={gym_status})")
    
    def test_11_member_can_login_after_reactivation(self):
        """Test that member can login normally after gym reactivation"""
        # Ensure gym is active
        super_token = self.get_super_admin_token()
        gym_id, _ = self.get_fitzone_gym_id(super_token)
        
        current_status = self.get_gym_status(super_token, gym_id)
        if current_status == "payment_suspended":
            self.session.put(
                f"{BASE_URL}/api/gyms/{gym_id}/payment-suspend",
                headers={"Authorization": f"Bearer {super_token}"}
            )
        
        # Login as member
        response = self.session.post(f"{BASE_URL}/api/auth/member/login?code={MEMBER_CODE}")
        assert response.status_code == 200, f"Member login failed: {response.text}"
        data = response.json()
        assert "member" in data
        assert "token" in data
        print("✓ Member can login normally after reactivation")
    
    def test_12_gym_list_shows_payment_suspended_status(self):
        """Test that GET /api/gyms returns payment_suspended status for suspended gyms"""
        token = self.get_super_admin_token()
        gym_id, _ = self.get_fitzone_gym_id(token)
        
        # Suspend the gym
        self.session.put(
            f"{BASE_URL}/api/gyms/{gym_id}/payment-suspend",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Get gyms list
        response = self.session.get(
            f"{BASE_URL}/api/gyms",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        gyms = response.json()
        fitzone = next((g for g in gyms if g.get("id") == gym_id), None)
        assert fitzone is not None
        assert fitzone.get("status") == "payment_suspended", \
            f"Expected status='payment_suspended', got {fitzone.get('status')}"
        print("✓ Gym list shows payment_suspended status")
        
        # Reactivate for cleanup
        self.session.put(
            f"{BASE_URL}/api/gyms/{gym_id}/payment-suspend",
            headers={"Authorization": f"Bearer {token}"}
        )
        print("✓ Gym reactivated for cleanup")


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
