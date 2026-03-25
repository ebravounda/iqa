"""
Iteration 9 Feature Tests
Tests for 4 new major features:
1. Kiosk Module - In-gym registration
2. Email Templates - Per-gym email templates
3. Accounting Module - Charts and PDF export
4. Manual Payments - Cash/card at reception
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://stripe-gym-payments.preview.emergentagent.com')
GYM_ID = "efe99507-15d5-4e54-9f07-30d2507894e0"  # FitZone Gym

# Test credentials
SUPER_ADMIN_EMAIL = "admin@gymaccess.com"
SUPER_ADMIN_PASSWORD = "admin123"
GYM_ADMIN_EMAIL = "admin@fitzone.com"
GYM_ADMIN_PASSWORD = "admin123"


@pytest.fixture(scope="module")
def super_admin_token():
    """Get super admin auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
        "email": SUPER_ADMIN_EMAIL,
        "password": SUPER_ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Super admin login failed")


@pytest.fixture(scope="module")
def gym_admin_token():
    """Get gym admin auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
        "email": GYM_ADMIN_EMAIL,
        "password": GYM_ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Gym admin login failed")


@pytest.fixture(scope="module")
def auth_headers(gym_admin_token):
    """Auth headers for gym admin"""
    return {"Authorization": f"Bearer {gym_admin_token}"}


@pytest.fixture(scope="module")
def super_auth_headers(super_admin_token):
    """Auth headers for super admin"""
    return {"Authorization": f"Bearer {super_admin_token}"}


class TestKioskModule:
    """Feature 1: Kiosk - In-gym registration"""
    
    def test_kiosk_register_new_member(self):
        """POST /api/kiosk/register registers member with status 'pending' and registered_via 'kiosk'"""
        unique_email = f"kiosk_test_{int(time.time())}@test.com"
        
        response = requests.post(f"{BASE_URL}/api/kiosk/register", json={
            "name": "Kiosk Test User",
            "email": unique_email,
            "phone": "+34 600 123 456",
            "gym_id": GYM_ID,
            "plan_id": None
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "member" in data
        assert "token" in data
        assert "message" in data
        
        # Verify member data
        member = data["member"]
        assert member["email"] == unique_email
        assert member["name"] == "Kiosk Test User"
        assert member["status"] == "pending", f"Expected status 'pending', got '{member['status']}'"
        assert member.get("registered_via") == "kiosk", f"Expected registered_via 'kiosk', got '{member.get('registered_via')}'"
        assert "code" in member
        assert len(member["code"]) == 6
        
        print(f"✓ Kiosk registration successful: {member['code']}")
    
    def test_kiosk_register_duplicate_email(self):
        """POST /api/kiosk/register rejects duplicate email"""
        # First registration
        unique_email = f"kiosk_dup_{int(time.time())}@test.com"
        response1 = requests.post(f"{BASE_URL}/api/kiosk/register", json={
            "name": "First User",
            "email": unique_email,
            "gym_id": GYM_ID
        })
        assert response1.status_code == 200
        
        # Second registration with same email
        response2 = requests.post(f"{BASE_URL}/api/kiosk/register", json={
            "name": "Second User",
            "email": unique_email,
            "gym_id": GYM_ID
        })
        assert response2.status_code == 400
        assert "ya está registrado" in response2.json().get("detail", "").lower()
        
        print("✓ Duplicate email rejected correctly")
    
    def test_gym_public_info_endpoint(self):
        """GET /api/gyms/{gym_id}/public-info returns gym info for kiosk"""
        response = requests.get(f"{BASE_URL}/api/gyms/{GYM_ID}/public-info")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert "name" in data
        assert data["id"] == GYM_ID
        
        print(f"✓ Public gym info: {data['name']}")


class TestEmailTemplates:
    """Feature 2: Email Templates - Per-gym email templates"""
    
    def test_get_gym_with_templates(self, auth_headers):
        """GET /api/gyms/{gym_id} returns email_templates array"""
        response = requests.get(f"{BASE_URL}/api/gyms/{GYM_ID}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "email_templates" in data, "email_templates field missing"
        templates = data["email_templates"]
        assert isinstance(templates, list)
        
        # Check for expected template types
        template_types = [t["type"] for t in templates]
        expected_types = ["welcome", "expiring_10", "expiring_5", "expiring_3", "expired", "payment_success"]
        
        for expected in expected_types:
            assert expected in template_types, f"Missing template type: {expected}"
        
        print(f"✓ Found {len(templates)} email templates")
    
    def test_update_welcome_template(self, auth_headers):
        """PUT /api/gyms/{gym_id}/templates/welcome updates the welcome template"""
        new_subject = f"Bienvenido a FitZone - Test {int(time.time())}"
        new_body = "Hola {member_name},\n\nBienvenido a {gym_name}. Tu código es: {member_code}\n\nTest update."
        
        response = requests.put(
            f"{BASE_URL}/api/gyms/{GYM_ID}/templates/welcome",
            headers=auth_headers,
            json={"subject": new_subject, "body": new_body}
        )
        
        assert response.status_code == 200
        assert "message" in response.json()
        
        # Verify update
        verify_response = requests.get(f"{BASE_URL}/api/gyms/{GYM_ID}", headers=auth_headers)
        templates = verify_response.json().get("email_templates", [])
        welcome_template = next((t for t in templates if t["type"] == "welcome"), None)
        
        assert welcome_template is not None
        assert welcome_template["subject"] == new_subject
        
        print("✓ Welcome template updated successfully")
    
    def test_update_payment_success_template(self, auth_headers):
        """PUT /api/gyms/{gym_id}/templates/payment_success updates payment template"""
        response = requests.put(
            f"{BASE_URL}/api/gyms/{GYM_ID}/templates/payment_success",
            headers=auth_headers,
            json={
                "subject": "Pago Confirmado - {gym_name}",
                "body": "Hola {member_name},\n\nTu pago de {amount} ha sido procesado.\n\nGracias!"
            }
        )
        
        assert response.status_code == 200
        print("✓ Payment success template updated")


class TestAccountingModule:
    """Feature 3: Accounting - Charts and PDF export"""
    
    def test_accounting_report_endpoint(self, auth_headers):
        """GET /api/accounting/report returns summary with totals and transactions"""
        response = requests.get(f"{BASE_URL}/api/accounting/report", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "summary" in data
        assert "transactions" in data
        assert "daily_chart" in data
        
        summary = data["summary"]
        assert "total_revenue" in summary
        assert "total_transactions" in summary
        assert "cash_total" in summary
        assert "card_total" in summary
        assert "stripe_total" in summary
        
        print(f"✓ Accounting report: ${summary['total_revenue']:.2f} total, {summary['total_transactions']} transactions")
    
    def test_accounting_report_with_date_filter(self, auth_headers):
        """GET /api/accounting/report with date filters"""
        response = requests.get(
            f"{BASE_URL}/api/accounting/report",
            headers=auth_headers,
            params={"date_from": "2024-01-01", "date_to": "2026-12-31"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        
        print("✓ Accounting report with date filter works")
    
    def test_accounting_pdf_endpoint(self, auth_headers):
        """GET /api/accounting/pdf returns a PDF stream"""
        response = requests.get(
            f"{BASE_URL}/api/accounting/pdf",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Check content type is PDF
        content_type = response.headers.get("content-type", "")
        assert "pdf" in content_type.lower() or "octet-stream" in content_type.lower(), \
            f"Expected PDF content type, got: {content_type}"
        
        # Check we got actual content
        assert len(response.content) > 100, "PDF content too small"
        
        # Check PDF magic bytes
        assert response.content[:4] == b'%PDF', "Response is not a valid PDF"
        
        print(f"✓ PDF generated: {len(response.content)} bytes")


class TestManualPayments:
    """Feature 4: Manual Payments - Cash/card at reception"""
    
    @pytest.fixture
    def test_member(self, auth_headers):
        """Create a test member for payment tests"""
        unique_email = f"payment_test_{int(time.time())}@test.com"
        
        response = requests.post(
            f"{BASE_URL}/api/members",
            headers=auth_headers,
            json={
                "name": "Payment Test Member",
                "email": unique_email,
                "gym_id": GYM_ID
            }
        )
        
        if response.status_code == 200:
            return response.json()
        pytest.skip("Could not create test member")
    
    @pytest.fixture
    def test_plan(self, auth_headers):
        """Get first available plan"""
        response = requests.get(f"{BASE_URL}/api/plans", headers=auth_headers)
        if response.status_code == 200 and len(response.json()) > 0:
            return response.json()[0]
        pytest.skip("No plans available")
    
    def test_manual_payment_cash(self, auth_headers, test_member, test_plan):
        """POST /api/payments/manual with cash payment creates transaction and activates membership"""
        response = requests.post(
            f"{BASE_URL}/api/payments/manual",
            headers=auth_headers,
            json={
                "member_id": test_member["id"],
                "plan_id": test_plan["id"],
                "payment_method": "cash",
                "amount": test_plan["price"],
                "notes": "Test cash payment"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response
        assert "transaction" in data
        assert "membership" in data
        assert "message" in data
        
        transaction = data["transaction"]
        assert transaction["payment_method"] == "cash"
        assert transaction["status"] == "completed"
        assert transaction["payment_status"] == "paid"
        assert transaction["amount"] == test_plan["price"]
        
        membership = data["membership"]
        assert membership["status"] == "active"
        assert membership["plan_id"] == test_plan["id"]
        
        print(f"✓ Cash payment registered: ${transaction['amount']}")
    
    def test_manual_payment_card_reception(self, auth_headers):
        """POST /api/payments/manual with card_reception payment"""
        # Create a new member for this test
        unique_email = f"card_test_{int(time.time())}@test.com"
        member_response = requests.post(
            f"{BASE_URL}/api/members",
            headers=auth_headers,
            json={"name": "Card Test Member", "email": unique_email, "gym_id": GYM_ID}
        )
        assert member_response.status_code == 200
        member = member_response.json()
        
        # Get a plan
        plans_response = requests.get(f"{BASE_URL}/api/plans", headers=auth_headers)
        plan = plans_response.json()[0]
        
        # Make card payment
        response = requests.post(
            f"{BASE_URL}/api/payments/manual",
            headers=auth_headers,
            json={
                "member_id": member["id"],
                "plan_id": plan["id"],
                "payment_method": "card_reception",
                "amount": plan["price"],
                "notes": "Test card at reception"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["transaction"]["payment_method"] == "card_reception"
        assert data["transaction"]["status"] == "completed"
        
        print("✓ Card at reception payment registered")
    
    def test_manual_payment_reactivates_suspended_member(self, auth_headers):
        """Manual payment reactivates a suspended member"""
        # Create and suspend a member
        unique_email = f"suspend_test_{int(time.time())}@test.com"
        member_response = requests.post(
            f"{BASE_URL}/api/members",
            headers=auth_headers,
            json={"name": "Suspended Test", "email": unique_email, "gym_id": GYM_ID}
        )
        member = member_response.json()
        
        # Suspend the member
        requests.post(
            f"{BASE_URL}/api/members/{member['id']}/suspend",
            headers=auth_headers,
            json={"reason": "Test suspension"}
        )
        
        # Verify suspended
        verify_response = requests.get(f"{BASE_URL}/api/members/{member['id']}", headers=auth_headers)
        assert verify_response.json()["status"] == "suspended"
        
        # Get a plan and make payment
        plans_response = requests.get(f"{BASE_URL}/api/plans", headers=auth_headers)
        plan = plans_response.json()[0]
        
        payment_response = requests.post(
            f"{BASE_URL}/api/payments/manual",
            headers=auth_headers,
            json={
                "member_id": member["id"],
                "plan_id": plan["id"],
                "payment_method": "cash",
                "amount": plan["price"]
            }
        )
        
        assert payment_response.status_code == 200
        
        # Verify member is now active
        final_response = requests.get(f"{BASE_URL}/api/members/{member['id']}", headers=auth_headers)
        assert final_response.json()["status"] == "active", "Member should be reactivated after payment"
        
        print("✓ Suspended member reactivated after payment")


class TestSidebarNavigation:
    """Test sidebar navigation items"""
    
    def test_gym_admin_login(self):
        """Verify gym admin can login"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": GYM_ADMIN_EMAIL,
            "password": GYM_ADMIN_PASSWORD
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["admin"]["role"] == "gym_admin"
        
        print("✓ Gym admin login successful")


class TestRegressionTests:
    """Regression tests for existing functionality"""
    
    def test_super_admin_login(self):
        """Super admin login still works"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        
        assert response.status_code == 200
        assert response.json()["admin"]["role"] == "super_admin"
        print("✓ Super admin login works")
    
    def test_impersonation(self, super_auth_headers):
        """Super admin impersonation still works"""
        response = requests.post(
            f"{BASE_URL}/api/auth/admin/impersonate/{GYM_ID}",
            headers=super_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["admin"]["impersonating"] == True
        assert data["admin"]["gym_id"] == GYM_ID
        
        print("✓ Impersonation works")
    
    def test_devices_endpoint(self, auth_headers):
        """Devices endpoint still works"""
        response = requests.get(f"{BASE_URL}/api/devices", headers=auth_headers)
        assert response.status_code == 200
        print("✓ Devices endpoint works")
    
    def test_access_logs_endpoint(self, auth_headers):
        """Access logs endpoint still works"""
        response = requests.get(f"{BASE_URL}/api/access/logs", headers=auth_headers)
        assert response.status_code == 200
        print("✓ Access logs endpoint works")
    
    def test_public_registration_endpoint(self):
        """Public registration endpoint still works"""
        response = requests.get(f"{BASE_URL}/api/gyms/{GYM_ID}/public-info")
        assert response.status_code == 200
        print("✓ Public registration endpoint works")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
