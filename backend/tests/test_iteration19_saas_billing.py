"""
Iteration 19 - SaaS Billing System Tests
Tests for:
- SaaS Plans CRUD (Super Admin only)
- SaaS Plan assignment to gyms
- Gym Admin subscription endpoints
- Available plans public endpoint
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


class TestSuperAdminLogin:
    """Test Super Admin authentication"""
    
    def test_super_admin_login_success(self):
        """Super Admin login works with correct credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in response"
        assert "admin" in data, "No admin in response"
        assert data["admin"]["role"] == "super_admin", "Not a super admin"
        print(f"Super Admin login successful: {data['admin']['email']}")


class TestGymAdminLogin:
    """Test Gym Admin authentication"""
    
    def test_gym_admin_login_success(self):
        """Gym Admin login works with correct credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": GYM_ADMIN_EMAIL,
            "password": GYM_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in response"
        assert "admin" in data, "No admin in response"
        assert data["admin"]["role"] == "gym_admin", "Not a gym admin"
        assert data["admin"].get("gym_id") is not None, "No gym_id for gym admin"
        print(f"Gym Admin login successful: {data['admin']['email']}, gym_id: {data['admin']['gym_id']}")


@pytest.fixture
def super_admin_token():
    """Get Super Admin auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
        "email": SUPER_ADMIN_EMAIL,
        "password": SUPER_ADMIN_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip("Super Admin login failed")
    return response.json()["token"]


@pytest.fixture
def gym_admin_token():
    """Get Gym Admin auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
        "email": GYM_ADMIN_EMAIL,
        "password": GYM_ADMIN_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip("Gym Admin login failed")
    return response.json()["token"]


@pytest.fixture
def gym_admin_data():
    """Get Gym Admin data including gym_id"""
    response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
        "email": GYM_ADMIN_EMAIL,
        "password": GYM_ADMIN_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip("Gym Admin login failed")
    return response.json()["admin"]


class TestSaaSPlansGet:
    """Test GET /api/saas/plans - List SaaS plans"""
    
    def test_get_saas_plans_authenticated(self, super_admin_token):
        """GET /api/saas/plans returns list of SaaS plans"""
        response = requests.get(
            f"{BASE_URL}/api/saas/plans",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"Found {len(data)} SaaS plans")
        
        # Verify plan structure if plans exist
        if len(data) > 0:
            plan = data[0]
            # Check for 12 feature flags
            feature_keys = [
                "has_qr_access", "has_guest_passes", "has_classes", "has_pos",
                "has_analytics", "has_gamification", "has_routines", "has_email_smtp",
                "has_stripe_members", "has_mercadopago", "has_iframes", "has_advanced_accounting"
            ]
            for key in feature_keys:
                assert key in plan, f"Missing feature flag: {key}"
            assert "name" in plan, "Missing name"
            assert "max_members" in plan, "Missing max_members"
            assert "price_monthly" in plan, "Missing price_monthly"
            assert "currency" in plan, "Missing currency"
            print(f"Plan structure verified with all 12 feature flags")
    
    def test_get_saas_plans_unauthenticated(self):
        """GET /api/saas/plans requires authentication"""
        response = requests.get(f"{BASE_URL}/api/saas/plans")
        # 401 or 403 are both acceptable for unauthenticated requests
        assert response.status_code in [401, 403], f"Should require authentication, got {response.status_code}"


class TestSaaSPlansCRUD:
    """Test SaaS Plans CRUD operations (Super Admin only)"""
    
    def test_create_saas_plan(self, super_admin_token):
        """POST /api/saas/plans creates a new SaaS plan with all feature flags"""
        plan_data = {
            "name": "TEST_Plan_Iteration19",
            "max_members": 100,
            "price_monthly": 19.99,
            "currency": "EUR",
            "description": "Test plan for iteration 19",
            "has_qr_access": True,
            "has_guest_passes": True,
            "has_classes": False,
            "has_pos": False,
            "has_analytics": False,
            "has_gamification": False,
            "has_routines": False,
            "has_email_smtp": False,
            "has_stripe_members": False,
            "has_mercadopago": False,
            "has_iframes": False,
            "has_advanced_accounting": False
        }
        response = requests.post(
            f"{BASE_URL}/api/saas/plans",
            json=plan_data,
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200, f"Create failed: {response.text}"
        data = response.json()
        assert data["name"] == plan_data["name"], "Name mismatch"
        assert data["max_members"] == plan_data["max_members"], "max_members mismatch"
        assert data["price_monthly"] == plan_data["price_monthly"], "price_monthly mismatch"
        assert data["has_qr_access"] == True, "has_qr_access should be True"
        assert data["has_guest_passes"] == True, "has_guest_passes should be True"
        assert "id" in data, "No id in response"
        print(f"Created SaaS plan: {data['name']} with id: {data['id']}")
        return data["id"]
    
    def test_create_saas_plan_gym_admin_forbidden(self, gym_admin_token):
        """POST /api/saas/plans - Gym Admin cannot create SaaS plans"""
        plan_data = {
            "name": "TEST_Unauthorized_Plan",
            "max_members": 50,
            "price_monthly": 9.99,
            "currency": "EUR"
        }
        response = requests.post(
            f"{BASE_URL}/api/saas/plans",
            json=plan_data,
            headers={"Authorization": f"Bearer {gym_admin_token}"}
        )
        assert response.status_code == 403, f"Should be forbidden for gym admin: {response.status_code}"
        print("Gym Admin correctly forbidden from creating SaaS plans")
    
    def test_update_saas_plan(self, super_admin_token):
        """PUT /api/saas/plans/{id} updates a SaaS plan"""
        # First create a plan
        create_response = requests.post(
            f"{BASE_URL}/api/saas/plans",
            json={
                "name": "TEST_Update_Plan",
                "max_members": 200,
                "price_monthly": 29.99,
                "currency": "EUR"
            },
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert create_response.status_code == 200
        plan_id = create_response.json()["id"]
        
        # Update the plan
        update_data = {
            "name": "TEST_Updated_Plan",
            "max_members": 300,
            "has_classes": True
        }
        response = requests.put(
            f"{BASE_URL}/api/saas/plans/{plan_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200, f"Update failed: {response.text}"
        data = response.json()
        assert data["name"] == "TEST_Updated_Plan", "Name not updated"
        assert data["max_members"] == 300, "max_members not updated"
        assert data["has_classes"] == True, "has_classes not updated"
        print(f"Updated SaaS plan: {data['name']}")
        
        # Cleanup - delete the plan
        requests.delete(
            f"{BASE_URL}/api/saas/plans/{plan_id}",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
    
    def test_delete_saas_plan(self, super_admin_token):
        """DELETE /api/saas/plans/{id} soft-deletes a SaaS plan"""
        # First create a plan
        create_response = requests.post(
            f"{BASE_URL}/api/saas/plans",
            json={
                "name": "TEST_Delete_Plan",
                "max_members": 50,
                "price_monthly": 9.99,
                "currency": "EUR"
            },
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert create_response.status_code == 200
        plan_id = create_response.json()["id"]
        
        # Delete the plan
        response = requests.delete(
            f"{BASE_URL}/api/saas/plans/{plan_id}",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200, f"Delete failed: {response.text}"
        data = response.json()
        assert "message" in data, "No message in response"
        print(f"Deleted SaaS plan: {plan_id}")
        
        # Verify plan is no longer in active list
        list_response = requests.get(
            f"{BASE_URL}/api/saas/plans",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        plans = list_response.json()
        plan_ids = [p["id"] for p in plans]
        assert plan_id not in plan_ids, "Deleted plan should not appear in active list"


class TestSaaSPlanAssignment:
    """Test assigning SaaS plans to gyms"""
    
    def test_assign_saas_plan_to_gym(self, super_admin_token):
        """PUT /api/gyms/{id}/saas-plan assigns SaaS plan to gym"""
        # Get list of gyms
        gyms_response = requests.get(
            f"{BASE_URL}/api/gyms",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert gyms_response.status_code == 200
        gyms = gyms_response.json()
        assert len(gyms) > 0, "No gyms found"
        gym_id = gyms[0]["id"]
        
        # Get list of SaaS plans
        plans_response = requests.get(
            f"{BASE_URL}/api/saas/plans",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert plans_response.status_code == 200
        plans = plans_response.json()
        assert len(plans) > 0, "No SaaS plans found"
        plan_id = plans[0]["id"]
        
        # Assign plan to gym
        response = requests.put(
            f"{BASE_URL}/api/gyms/{gym_id}/saas-plan",
            json={"saas_plan_id": plan_id},
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200, f"Assignment failed: {response.text}"
        data = response.json()
        assert "message" in data, "No message in response"
        print(f"Assigned plan {plan_id} to gym {gym_id}")
    
    def test_assign_saas_plan_gym_admin_forbidden(self, gym_admin_token, gym_admin_data):
        """PUT /api/gyms/{id}/saas-plan - Gym Admin cannot assign plans"""
        gym_id = gym_admin_data["gym_id"]
        response = requests.put(
            f"{BASE_URL}/api/gyms/{gym_id}/saas-plan",
            json={"saas_plan_id": "some-plan-id"},
            headers={"Authorization": f"Bearer {gym_admin_token}"}
        )
        assert response.status_code == 403, f"Should be forbidden: {response.status_code}"
        print("Gym Admin correctly forbidden from assigning SaaS plans")


class TestGymSaaSFeatures:
    """Test getting gym's SaaS features"""
    
    def test_get_gym_saas_features(self, super_admin_token):
        """GET /api/gyms/{id}/saas-features returns gym's SaaS features"""
        # Get a gym
        gyms_response = requests.get(
            f"{BASE_URL}/api/gyms",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        gyms = gyms_response.json()
        gym_id = gyms[0]["id"]
        
        response = requests.get(
            f"{BASE_URL}/api/gyms/{gym_id}/saas-features",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Check for feature keys
        feature_keys = [
            "has_qr_access", "has_guest_passes", "has_classes", "has_pos",
            "has_analytics", "has_gamification", "has_routines", "has_email_smtp",
            "has_stripe_members", "has_mercadopago", "has_iframes", "has_advanced_accounting"
        ]
        for key in feature_keys:
            assert key in data, f"Missing feature: {key}"
        assert "max_members" in data, "Missing max_members"
        assert "plan_name" in data, "Missing plan_name"
        print(f"Gym SaaS features: plan={data['plan_name']}, max_members={data['max_members']}")


class TestMySubscription:
    """Test Gym Admin subscription endpoint"""
    
    def test_get_my_subscription(self, gym_admin_token):
        """GET /api/saas/my-subscription returns gym's current subscription"""
        response = requests.get(
            f"{BASE_URL}/api/saas/my-subscription",
            headers={"Authorization": f"Bearer {gym_admin_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "gym_name" in data, "Missing gym_name"
        assert "member_count" in data, "Missing member_count"
        assert "max_members" in data, "Missing max_members"
        assert "plan" in data, "Missing plan"
        
        print(f"Subscription: gym={data['gym_name']}, members={data['member_count']}/{data['max_members']}")
        if data["plan"]:
            print(f"  Plan: {data['plan']['name']}, price={data['plan']['price_monthly']} {data['plan'].get('currency', 'EUR')}")
    
    def test_get_my_subscription_super_admin_no_gym(self, super_admin_token):
        """GET /api/saas/my-subscription - Super Admin without gym_id gets error"""
        response = requests.get(
            f"{BASE_URL}/api/saas/my-subscription",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        # Super admin has no gym_id, should return 400
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("Super Admin without gym_id correctly gets 400 error")


class TestAvailablePlans:
    """Test public available plans endpoint"""
    
    def test_get_available_plans_public(self):
        """GET /api/saas/available-plans returns available plans (public)"""
        response = requests.get(f"{BASE_URL}/api/saas/available-plans")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"Found {len(data)} available SaaS plans (public)")
        
        if len(data) > 0:
            plan = data[0]
            assert "name" in plan, "Missing name"
            assert "price_monthly" in plan, "Missing price_monthly"
            assert "max_members" in plan, "Missing max_members"


class TestSaaSSubscribe:
    """Test SaaS subscription endpoint"""
    
    def test_subscribe_without_stripe_key(self, gym_admin_token):
        """POST /api/saas/subscribe returns error when PLATFORM_STRIPE_KEY not set"""
        # Get an available plan
        plans_response = requests.get(f"{BASE_URL}/api/saas/available-plans")
        plans = plans_response.json()
        if len(plans) == 0:
            pytest.skip("No available plans")
        
        # Find a paid plan
        paid_plan = None
        for plan in plans:
            if plan.get("price_monthly", 0) > 0:
                paid_plan = plan
                break
        
        if not paid_plan:
            pytest.skip("No paid plans available")
        
        response = requests.post(
            f"{BASE_URL}/api/saas/subscribe",
            json={"plan_id": paid_plan["id"]},
            headers={"Authorization": f"Bearer {gym_admin_token}"}
        )
        
        # Expected: 500 error because PLATFORM_STRIPE_KEY is not set
        assert response.status_code == 500, f"Expected 500, got {response.status_code}"
        data = response.json()
        assert "detail" in data, "Missing error detail"
        assert "Stripe" in data["detail"] or "plataforma" in data["detail"], f"Unexpected error: {data['detail']}"
        print(f"Correctly got Stripe config error: {data['detail']}")
    
    def test_subscribe_free_plan(self, gym_admin_token):
        """POST /api/saas/subscribe with free plan should work"""
        # Get available plans
        plans_response = requests.get(f"{BASE_URL}/api/saas/available-plans")
        plans = plans_response.json()
        
        # Find a free plan (price_monthly = 0)
        free_plan = None
        for plan in plans:
            if plan.get("price_monthly", 0) == 0:
                free_plan = plan
                break
        
        if not free_plan:
            pytest.skip("No free plans available")
        
        response = requests.post(
            f"{BASE_URL}/api/saas/subscribe",
            json={"plan_id": free_plan["id"]},
            headers={"Authorization": f"Bearer {gym_admin_token}"}
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data.get("free") == True, "Should indicate free plan"
        print(f"Free plan subscription successful")


class TestCleanup:
    """Cleanup test data"""
    
    def test_cleanup_test_plans(self, super_admin_token):
        """Delete TEST_ prefixed plans"""
        response = requests.get(
            f"{BASE_URL}/api/saas/plans",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        if response.status_code != 200:
            return
        
        plans = response.json()
        deleted = 0
        for plan in plans:
            if plan["name"].startswith("TEST_"):
                del_response = requests.delete(
                    f"{BASE_URL}/api/saas/plans/{plan['id']}",
                    headers={"Authorization": f"Bearer {super_admin_token}"}
                )
                if del_response.status_code == 200:
                    deleted += 1
        
        print(f"Cleaned up {deleted} test plans")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
