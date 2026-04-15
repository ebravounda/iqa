"""
Iteration 29 - Redsys TPV Virtual Integration Tests
Tests for:
- GET /api/gyms/{gym_id}/redsys-config - Get Redsys config status with masked credentials
- PUT /api/gyms/{gym_id}/redsys-config - Update Redsys credentials and enabled status
- POST /api/redsys/initiate - Generate Redsys payment form data
- GET /api/redsys/status/{order_number} - Get payment status by order number
"""
import pytest
import requests
import os
import base64
import json

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test gym ID with Redsys configured (from agent context)
TEST_GYM_ID = "efe99507-15d5-4e54-9f07-30d2507894e0"

# Test credentials
ADMIN_EMAIL = "admin@gymaccess.com"
ADMIN_PASSWORD = "admin123"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip(f"Admin authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def auth_headers(admin_token):
    """Headers with admin auth token"""
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


class TestRedsysConfigEndpoints:
    """Tests for Redsys configuration endpoints"""

    def test_get_redsys_config_success(self, auth_headers):
        """GET /api/gyms/{gym_id}/redsys-config returns config status with masked credentials"""
        response = requests.get(f"{BASE_URL}/api/gyms/{TEST_GYM_ID}/redsys-config", headers=auth_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify response structure
        assert "enabled" in data, "Response should have 'enabled' field"
        assert "has_credentials" in data, "Response should have 'has_credentials' field"
        assert "masked_merchant_code" in data, "Response should have 'masked_merchant_code' field"
        assert "terminal" in data, "Response should have 'terminal' field"
        assert "environment" in data, "Response should have 'environment' field"
        
        # Verify types
        assert isinstance(data["enabled"], bool), "enabled should be boolean"
        assert isinstance(data["has_credentials"], bool), "has_credentials should be boolean"
        assert data["environment"] in ["sandbox", "production"], "environment should be sandbox or production"
        
        print(f"Redsys config: enabled={data['enabled']}, has_credentials={data['has_credentials']}, env={data['environment']}")

    def test_get_redsys_config_masked_credentials(self, auth_headers):
        """GET /api/gyms/{gym_id}/redsys-config returns masked merchant code (not full credentials)"""
        response = requests.get(f"{BASE_URL}/api/gyms/{TEST_GYM_ID}/redsys-config", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # If credentials exist, merchant code should be masked
        if data["has_credentials"]:
            masked = data["masked_merchant_code"]
            assert "****" in masked, "Merchant code should be masked with ****"
            # Should not return full merchant code (9 digits)
            assert len(masked) < 9 or "****" in masked, "Merchant code should be partially masked"
            print(f"Masked merchant code: {masked}")

    def test_get_redsys_config_nonexistent_gym(self, auth_headers):
        """GET /api/gyms/{gym_id}/redsys-config returns 404 for non-existent gym"""
        response = requests.get(f"{BASE_URL}/api/gyms/nonexistent-gym-id/redsys-config", headers=auth_headers)
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"

    def test_get_redsys_config_unauthenticated(self):
        """GET /api/gyms/{gym_id}/redsys-config requires authentication"""
        response = requests.get(f"{BASE_URL}/api/gyms/{TEST_GYM_ID}/redsys-config")
        
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"

    def test_update_redsys_config_enable(self, auth_headers):
        """PUT /api/gyms/{gym_id}/redsys-config can enable Redsys"""
        # First get current state
        get_response = requests.get(f"{BASE_URL}/api/gyms/{TEST_GYM_ID}/redsys-config", headers=auth_headers)
        original_state = get_response.json()
        
        # Update to enable
        update_data = {
            "redsys_enabled": True,
            "redsys_environment": "sandbox"
        }
        response = requests.put(f"{BASE_URL}/api/gyms/{TEST_GYM_ID}/redsys-config", 
                               json=update_data, headers=auth_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True, "Response should indicate success"
        
        # Verify the change
        verify_response = requests.get(f"{BASE_URL}/api/gyms/{TEST_GYM_ID}/redsys-config", headers=auth_headers)
        verify_data = verify_response.json()
        assert verify_data["enabled"] == True, "Redsys should be enabled"
        assert verify_data["environment"] == "sandbox", "Environment should be sandbox"
        
        print(f"Redsys enabled successfully: {verify_data}")

    def test_update_redsys_config_credentials(self, auth_headers):
        """PUT /api/gyms/{gym_id}/redsys-config can update credentials"""
        # Update with test credentials
        update_data = {
            "redsys_merchant_code": "999008881",
            "redsys_terminal": "001",
            "redsys_secret_key": "sq7HjrUOBfKmC576ILgskD5srU870gJ7",
            "redsys_environment": "sandbox",
            "redsys_enabled": True
        }
        response = requests.put(f"{BASE_URL}/api/gyms/{TEST_GYM_ID}/redsys-config", 
                               json=update_data, headers=auth_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Verify credentials were saved (masked)
        verify_response = requests.get(f"{BASE_URL}/api/gyms/{TEST_GYM_ID}/redsys-config", headers=auth_headers)
        verify_data = verify_response.json()
        assert verify_data["has_credentials"] == True, "Should have credentials after update"
        assert verify_data["terminal"] == "001", "Terminal should be 001"
        
        print(f"Credentials updated: {verify_data}")

    def test_update_redsys_config_disable(self, auth_headers):
        """PUT /api/gyms/{gym_id}/redsys-config can disable Redsys"""
        update_data = {"redsys_enabled": False}
        response = requests.put(f"{BASE_URL}/api/gyms/{TEST_GYM_ID}/redsys-config", 
                               json=update_data, headers=auth_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        # Verify disabled
        verify_response = requests.get(f"{BASE_URL}/api/gyms/{TEST_GYM_ID}/redsys-config", headers=auth_headers)
        verify_data = verify_response.json()
        assert verify_data["enabled"] == False, "Redsys should be disabled"
        
        # Re-enable for other tests
        requests.put(f"{BASE_URL}/api/gyms/{TEST_GYM_ID}/redsys-config", 
                    json={"redsys_enabled": True}, headers=auth_headers)
        
        print("Redsys disabled and re-enabled successfully")

    def test_update_redsys_config_unauthenticated(self):
        """PUT /api/gyms/{gym_id}/redsys-config requires authentication"""
        response = requests.put(f"{BASE_URL}/api/gyms/{TEST_GYM_ID}/redsys-config", 
                               json={"redsys_enabled": True})
        
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"


class TestRedsysPaymentInitiation:
    """Tests for Redsys payment initiation endpoint"""

    @pytest.fixture(scope="class")
    def test_member_and_plan(self, auth_headers):
        """Get a test member and plan from the gym"""
        # Get members
        members_response = requests.get(f"{BASE_URL}/api/members?gym_id={TEST_GYM_ID}", headers=auth_headers)
        members = members_response.json() if members_response.status_code == 200 else []
        
        # Get plans
        plans_response = requests.get(f"{BASE_URL}/api/plans?gym_id={TEST_GYM_ID}", headers=auth_headers)
        plans = plans_response.json() if plans_response.status_code == 200 else []
        
        if not members or not plans:
            pytest.skip("No members or plans available for testing")
        
        return {"member_id": members[0]["id"], "plan_id": plans[0]["id"]}

    def test_initiate_redsys_payment_success(self, auth_headers, test_member_and_plan):
        """POST /api/redsys/initiate generates Redsys payment form data"""
        # Ensure Redsys is enabled
        requests.put(f"{BASE_URL}/api/gyms/{TEST_GYM_ID}/redsys-config", 
                    json={"redsys_enabled": True}, headers=auth_headers)
        
        payload = {
            "member_id": test_member_and_plan["member_id"],
            "plan_id": test_member_and_plan["plan_id"],
            "gym_id": TEST_GYM_ID
        }
        
        response = requests.post(f"{BASE_URL}/api/redsys/initiate", json=payload, headers=auth_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify required fields for Redsys form submission
        assert "redsys_url" in data, "Response should have 'redsys_url'"
        assert "Ds_SignatureVersion" in data, "Response should have 'Ds_SignatureVersion'"
        assert "Ds_MerchantParameters" in data, "Response should have 'Ds_MerchantParameters'"
        assert "Ds_Signature" in data, "Response should have 'Ds_Signature'"
        assert "order_number" in data, "Response should have 'order_number'"
        
        # Verify values
        assert data["Ds_SignatureVersion"] == "HMAC_SHA256_V1", "Signature version should be HMAC_SHA256_V1"
        assert data["redsys_url"].startswith("https://sis"), "Redsys URL should be HTTPS"
        assert len(data["order_number"]) == 12, "Order number should be 12 characters"
        
        # Verify Ds_MerchantParameters is valid base64
        try:
            decoded = base64.b64decode(data["Ds_MerchantParameters"])
            params = json.loads(decoded)
            assert "DS_MERCHANT_ORDER" in params, "Merchant params should have order"
            assert "DS_MERCHANT_AMOUNT" in params, "Merchant params should have amount"
            assert "DS_MERCHANT_MERCHANTCODE" in params, "Merchant params should have merchant code"
            print(f"Decoded merchant params: {params}")
        except Exception as e:
            pytest.fail(f"Failed to decode Ds_MerchantParameters: {e}")
        
        print(f"Redsys payment initiated: order={data['order_number']}, url={data['redsys_url']}")

    def test_initiate_redsys_payment_redsys_disabled(self, auth_headers, test_member_and_plan):
        """POST /api/redsys/initiate returns 400 if Redsys not enabled for gym"""
        # Disable Redsys
        requests.put(f"{BASE_URL}/api/gyms/{TEST_GYM_ID}/redsys-config", 
                    json={"redsys_enabled": False}, headers=auth_headers)
        
        payload = {
            "member_id": test_member_and_plan["member_id"],
            "plan_id": test_member_and_plan["plan_id"],
            "gym_id": TEST_GYM_ID
        }
        
        response = requests.post(f"{BASE_URL}/api/redsys/initiate", json=payload, headers=auth_headers)
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "detail" in data, "Response should have error detail"
        assert "habilitado" in data["detail"].lower() or "enabled" in data["detail"].lower(), \
            "Error should mention Redsys not enabled"
        
        # Re-enable for other tests
        requests.put(f"{BASE_URL}/api/gyms/{TEST_GYM_ID}/redsys-config", 
                    json={"redsys_enabled": True}, headers=auth_headers)
        
        print(f"Correctly returned 400 when Redsys disabled: {data['detail']}")

    def test_initiate_redsys_payment_missing_params(self, auth_headers):
        """POST /api/redsys/initiate returns 400 if required params missing"""
        # Missing member_id
        response = requests.post(f"{BASE_URL}/api/redsys/initiate", 
                                json={"plan_id": "test", "gym_id": TEST_GYM_ID}, 
                                headers=auth_headers)
        assert response.status_code == 400, f"Expected 400 for missing member_id, got {response.status_code}"
        
        # Missing plan_id
        response = requests.post(f"{BASE_URL}/api/redsys/initiate", 
                                json={"member_id": "test", "gym_id": TEST_GYM_ID}, 
                                headers=auth_headers)
        assert response.status_code == 400, f"Expected 400 for missing plan_id, got {response.status_code}"
        
        # Missing gym_id
        response = requests.post(f"{BASE_URL}/api/redsys/initiate", 
                                json={"member_id": "test", "plan_id": "test"}, 
                                headers=auth_headers)
        assert response.status_code == 400, f"Expected 400 for missing gym_id, got {response.status_code}"
        
        print("Correctly validates required parameters")

    def test_initiate_redsys_payment_nonexistent_member(self, auth_headers, test_member_and_plan):
        """POST /api/redsys/initiate returns 404 for non-existent member"""
        # Ensure Redsys is enabled
        requests.put(f"{BASE_URL}/api/gyms/{TEST_GYM_ID}/redsys-config", 
                    json={"redsys_enabled": True}, headers=auth_headers)
        
        payload = {
            "member_id": "nonexistent-member-id",
            "plan_id": test_member_and_plan["plan_id"],
            "gym_id": TEST_GYM_ID
        }
        
        response = requests.post(f"{BASE_URL}/api/redsys/initiate", json=payload, headers=auth_headers)
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"

    def test_initiate_redsys_payment_nonexistent_plan(self, auth_headers, test_member_and_plan):
        """POST /api/redsys/initiate returns 404 for non-existent plan"""
        payload = {
            "member_id": test_member_and_plan["member_id"],
            "plan_id": "nonexistent-plan-id",
            "gym_id": TEST_GYM_ID
        }
        
        response = requests.post(f"{BASE_URL}/api/redsys/initiate", json=payload, headers=auth_headers)
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"


class TestRedsysPaymentStatus:
    """Tests for Redsys payment status endpoint"""

    def test_get_payment_status_nonexistent(self):
        """GET /api/redsys/status/{order_number} returns 404 for non-existent order"""
        response = requests.get(f"{BASE_URL}/api/redsys/status/NONEXISTENT123")
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"

    def test_get_payment_status_after_initiation(self, auth_headers):
        """GET /api/redsys/status/{order_number} returns pending status after initiation"""
        # First, get a member and plan
        members_response = requests.get(f"{BASE_URL}/api/members?gym_id={TEST_GYM_ID}", headers=auth_headers)
        plans_response = requests.get(f"{BASE_URL}/api/plans?gym_id={TEST_GYM_ID}", headers=auth_headers)
        
        if members_response.status_code != 200 or plans_response.status_code != 200:
            pytest.skip("Could not get members or plans")
        
        members = members_response.json()
        plans = plans_response.json()
        
        if not members or not plans:
            pytest.skip("No members or plans available")
        
        # Ensure Redsys is enabled
        requests.put(f"{BASE_URL}/api/gyms/{TEST_GYM_ID}/redsys-config", 
                    json={"redsys_enabled": True}, headers=auth_headers)
        
        # Initiate payment
        payload = {
            "member_id": members[0]["id"],
            "plan_id": plans[0]["id"],
            "gym_id": TEST_GYM_ID
        }
        
        init_response = requests.post(f"{BASE_URL}/api/redsys/initiate", json=payload, headers=auth_headers)
        
        if init_response.status_code != 200:
            pytest.skip(f"Could not initiate payment: {init_response.text}")
        
        order_number = init_response.json()["order_number"]
        
        # Check status
        status_response = requests.get(f"{BASE_URL}/api/redsys/status/{order_number}")
        
        assert status_response.status_code == 200, f"Expected 200, got {status_response.status_code}"
        
        data = status_response.json()
        assert data["order_number"] == order_number, "Order number should match"
        assert data["status"] == "pending", "Status should be pending"
        assert data["payment_status"] == "pending", "Payment status should be pending"
        assert "amount" in data, "Response should have amount"
        assert "plan_name" in data, "Response should have plan_name"
        
        print(f"Payment status: {data}")


class TestRedsysUtilityFunctions:
    """Tests for Redsys utility functions (signature generation, etc.)"""

    def test_order_number_format(self, auth_headers):
        """Order numbers should be 12 characters (4 numeric + 8 alphanumeric)"""
        # Ensure Redsys is enabled
        requests.put(f"{BASE_URL}/api/gyms/{TEST_GYM_ID}/redsys-config", 
                    json={"redsys_enabled": True}, headers=auth_headers)
        
        # Get a member and plan
        members_response = requests.get(f"{BASE_URL}/api/members?gym_id={TEST_GYM_ID}", headers=auth_headers)
        plans_response = requests.get(f"{BASE_URL}/api/plans?gym_id={TEST_GYM_ID}", headers=auth_headers)
        
        if members_response.status_code != 200 or plans_response.status_code != 200:
            pytest.skip("Could not get members or plans")
        
        members = members_response.json()
        plans = plans_response.json()
        
        if not members or not plans:
            pytest.skip("No members or plans available")
        
        # Initiate multiple payments to check order number uniqueness
        order_numbers = []
        for _ in range(3):
            payload = {
                "member_id": members[0]["id"],
                "plan_id": plans[0]["id"],
                "gym_id": TEST_GYM_ID
            }
            response = requests.post(f"{BASE_URL}/api/redsys/initiate", json=payload, headers=auth_headers)
            if response.status_code == 200:
                order_numbers.append(response.json()["order_number"])
        
        # Verify format and uniqueness
        for order in order_numbers:
            assert len(order) == 12, f"Order number should be 12 chars: {order}"
            assert order[:4].isdigit(), f"First 4 chars should be numeric: {order}"
        
        # Check uniqueness
        assert len(set(order_numbers)) == len(order_numbers), "Order numbers should be unique"
        
        print(f"Generated order numbers: {order_numbers}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
