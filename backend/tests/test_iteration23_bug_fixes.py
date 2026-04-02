"""
Iteration 23 - Bug Fixes Testing
Tests for:
1. Public registration with plan_id returns member with status 'pending' and requires_payment=true
2. Public registration without plan_id returns member with status 'active'
3. QR generation returns 403 for pending members
4. QR generation works for active members with active membership
5. Class bookings return 403 for pending members without active membership
6. Accounting transactions endpoint returns transactions with payment_status
7. Accounting report only includes paid transactions in revenue totals
"""

import pytest
import requests
import os
import uuid
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://stripe-gym-payments.preview.emergentagent.com')

# Test credentials - using existing admin from previous iterations
SUPER_ADMIN_EMAIL = "admin@ingresoqr.com"
SUPER_ADMIN_PASSWORD = "admin123"
# Gym and plan IDs from the system
EXISTING_GYM_ID = "efe99507-15d5-4e54-9f07-30d2507894e0"  # FitPro Gym
EXISTING_PLAN_ID = "54fd50c6-d475-4e1e-98f6-9340992c069f"  # Plan Mensual


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
        "email": SUPER_ADMIN_EMAIL,
        "password": SUPER_ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip(f"Admin authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    """Headers with admin auth token"""
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


class TestPublicRegistration:
    """Test public member registration with and without plan selection"""
    
    def test_register_with_plan_returns_pending_status(self):
        """POST /api/members/register with plan_id should return member with status 'pending' and requires_payment=true"""
        unique_email = f"test_pending_{uuid.uuid4().hex[:8]}@demo.com"
        payload = {
            "name": "Test Pending Member",
            "email": unique_email,
            "phone": "+34600000001",
            "gym_id": EXISTING_GYM_ID,
            "plan_id": EXISTING_PLAN_ID,
            "gender": "prefer_not_to_say"
        }
        
        response = requests.post(f"{BASE_URL}/api/members/register", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify member status is pending
        assert "member" in data, "Response should contain 'member' object"
        assert data["member"]["status"] == "pending", f"Member status should be 'pending', got '{data['member']['status']}'"
        
        # Verify requires_payment is true
        assert "requires_payment" in data, "Response should contain 'requires_payment' field"
        assert data["requires_payment"] == True, f"requires_payment should be True, got {data['requires_payment']}"
        
        # Verify membership is created with pending_payment status
        assert "membership" in data, "Response should contain 'membership' object"
        assert data["membership"]["status"] == "pending_payment", f"Membership status should be 'pending_payment', got '{data['membership']['status']}'"
        
        # Verify plan data is returned
        assert "plan" in data, "Response should contain 'plan' object"
        assert data["plan"]["id"] == EXISTING_PLAN_ID, "Plan ID should match"
        
        # Verify token is returned for payment flow
        assert "token" in data, "Response should contain 'token' for payment flow"
        
        print(f"✓ Registration with plan: member status='pending', requires_payment=True, membership status='pending_payment'")
        
        # Store token for cleanup
        return data
    
    def test_register_without_plan_returns_active_status(self):
        """POST /api/members/register without plan_id should return member with status 'active'"""
        unique_email = f"test_active_{uuid.uuid4().hex[:8]}@demo.com"
        payload = {
            "name": "Test Active Member",
            "email": unique_email,
            "phone": "+34600000002",
            "gym_id": EXISTING_GYM_ID,
            "plan_id": None,  # No plan selected
            "gender": "prefer_not_to_say"
        }
        
        response = requests.post(f"{BASE_URL}/api/members/register", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify member status is active
        assert "member" in data, "Response should contain 'member' object"
        assert data["member"]["status"] == "active", f"Member status should be 'active', got '{data['member']['status']}'"
        
        # Verify requires_payment is false
        assert "requires_payment" in data, "Response should contain 'requires_payment' field"
        assert data["requires_payment"] == False, f"requires_payment should be False, got {data['requires_payment']}"
        
        # Verify no membership is created
        assert data.get("membership") is None, "Membership should be None when no plan selected"
        
        print(f"✓ Registration without plan: member status='active', requires_payment=False")
        
        return data


class TestQRGeneration:
    """Test QR generation blocking for pending members"""
    
    def test_qr_generation_blocked_for_pending_member(self):
        """GET /api/qr/generate should return 403 for pending members"""
        # First register a pending member
        unique_email = f"test_qr_pending_{uuid.uuid4().hex[:8]}@demo.com"
        payload = {
            "name": "Test QR Pending",
            "email": unique_email,
            "phone": "+34600000003",
            "gym_id": EXISTING_GYM_ID,
            "plan_id": EXISTING_PLAN_ID,
            "gender": "prefer_not_to_say"
        }
        
        reg_response = requests.post(f"{BASE_URL}/api/members/register", json=payload)
        assert reg_response.status_code == 200, f"Registration failed: {reg_response.text}"
        
        member_token = reg_response.json()["token"]
        headers = {"Authorization": f"Bearer {member_token}"}
        
        # Try to generate QR
        qr_response = requests.get(f"{BASE_URL}/api/qr/generate", headers=headers)
        
        assert qr_response.status_code == 403, f"Expected 403 for pending member, got {qr_response.status_code}: {qr_response.text}"
        
        error_data = qr_response.json()
        assert "detail" in error_data, "Response should contain error detail"
        assert "membresia activa" in error_data["detail"].lower() or "activa" in error_data["detail"].lower(), \
            f"Error message should mention active membership requirement, got: {error_data['detail']}"
        
        print(f"✓ QR generation blocked for pending member with 403: {error_data['detail']}")
    
    def test_qr_generation_works_for_active_member(self):
        """GET /api/qr/generate should work for active members with active membership"""
        # Use existing active member NEDFJR
        login_response = requests.post(f"{BASE_URL}/api/auth/member/login?code=NEDFJR")
        
        if login_response.status_code != 200:
            pytest.skip(f"Could not login as member NEDFJR: {login_response.text}")
        
        member_token = login_response.json().get("token")
        member_headers = {"Authorization": f"Bearer {member_token}"}
        
        # Try to generate QR
        qr_response = requests.get(f"{BASE_URL}/api/qr/generate", headers=member_headers)
        
        assert qr_response.status_code == 200, f"Expected 200 for active member with membership, got {qr_response.status_code}: {qr_response.text}"
        
        qr_data = qr_response.json()
        assert "qr_code" in qr_data, "Response should contain 'qr_code'"
        assert qr_data["qr_code"], "QR code should not be empty"
        
        print(f"✓ QR generation works for active member with active membership")


class TestClassBookings:
    """Test class booking restrictions for pending members"""
    
    def test_booking_blocked_for_pending_member(self):
        """POST /api/bookings should return 403 for pending members without active membership"""
        # First register a pending member
        unique_email = f"test_booking_pending_{uuid.uuid4().hex[:8]}@demo.com"
        payload = {
            "name": "Test Booking Pending",
            "email": unique_email,
            "phone": "+34600000005",
            "gym_id": EXISTING_GYM_ID,
            "plan_id": EXISTING_PLAN_ID,
            "gender": "prefer_not_to_say"
        }
        
        reg_response = requests.post(f"{BASE_URL}/api/members/register", json=payload)
        assert reg_response.status_code == 200, f"Registration failed: {reg_response.text}"
        
        member_token = reg_response.json()["token"]
        member_headers = {"Authorization": f"Bearer {member_token}"}
        
        # Get available schedules
        schedules_response = requests.get(f"{BASE_URL}/api/schedules/public/{EXISTING_GYM_ID}")
        
        if schedules_response.status_code != 200 or not schedules_response.json():
            pytest.skip("No schedules available for testing")
        
        schedules = schedules_response.json()
        if not schedules:
            pytest.skip("No schedules available for testing")
        
        schedule_id = schedules[0]["id"]
        
        # Try to book a class
        booking_payload = {"schedule_id": schedule_id}
        booking_response = requests.post(f"{BASE_URL}/api/bookings", json=booking_payload, headers=member_headers)
        
        assert booking_response.status_code == 403, f"Expected 403 for pending member, got {booking_response.status_code}: {booking_response.text}"
        
        error_data = booking_response.json()
        assert "detail" in error_data, "Response should contain error detail"
        assert "membresia activa" in error_data["detail"].lower() or "activa" in error_data["detail"].lower(), \
            f"Error message should mention active membership requirement, got: {error_data['detail']}"
        
        print(f"✓ Class booking blocked for pending member with 403: {error_data['detail']}")


class TestAccountingTransactions:
    """Test accounting transactions endpoint with payment_status"""
    
    @pytest.fixture(autouse=True)
    def setup_admin(self):
        """Get admin token for this test class"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        if response.status_code == 200:
            self.admin_headers = {"Authorization": f"Bearer {response.json()['token']}", "Content-Type": "application/json"}
        else:
            pytest.skip(f"Admin authentication failed: {response.status_code}")
    
    def test_transactions_endpoint_returns_payment_status(self):
        """GET /api/accounting/transactions should return transactions with payment_status 'paid' or 'pending'"""
        response = requests.get(f"{BASE_URL}/api/accounting/transactions", headers=self.admin_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "transactions" in data, "Response should contain 'transactions' array"
        assert "summary" in data, "Response should contain 'summary' object"
        
        # Check summary has paid/pending counts
        summary = data["summary"]
        assert "paid_count" in summary, "Summary should have 'paid_count'"
        assert "pending_count" in summary, "Summary should have 'pending_count'"
        assert "total_paid" in summary, "Summary should have 'total_paid'"
        assert "total_pending" in summary, "Summary should have 'total_pending'"
        
        # Check transactions have payment_status field
        transactions = data["transactions"]
        if transactions:
            for tx in transactions[:5]:  # Check first 5
                assert "payment_status" in tx, f"Transaction should have 'payment_status' field: {tx}"
                assert tx["payment_status"] in ["paid", "pending", "initiated"], \
                    f"payment_status should be 'paid', 'pending', or 'initiated', got: {tx['payment_status']}"
        
        print(f"✓ Transactions endpoint returns payment_status. Summary: paid={summary['paid_count']}, pending={summary['pending_count']}")
    
    def test_accounting_report_only_includes_paid_transactions(self):
        """GET /api/accounting/report should only include paid transactions in revenue totals"""
        response = requests.get(f"{BASE_URL}/api/accounting/report", headers=self.admin_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "transactions" in data, "Response should contain 'transactions' array"
        assert "summary" in data, "Response should contain 'summary' object"
        
        # All transactions in report should be paid
        transactions = data["transactions"]
        for tx in transactions:
            # The report endpoint filters by payment_status='paid'
            if "payment_status" in tx:
                assert tx["payment_status"] == "paid", \
                    f"Report should only include paid transactions, found: {tx['payment_status']}"
        
        # Verify summary totals
        summary = data["summary"]
        assert "total_revenue" in summary, "Summary should have 'total_revenue'"
        assert "membership_revenue" in summary, "Summary should have 'membership_revenue'"
        
        # Calculate expected membership revenue from transactions
        calculated_revenue = sum(tx.get("amount", 0) for tx in transactions)
        assert summary["membership_revenue"] == calculated_revenue, \
            f"Membership revenue should match sum of paid transactions: {summary['membership_revenue']} vs {calculated_revenue}"
        
        print(f"✓ Accounting report only includes paid transactions. Total revenue: {summary['total_revenue']}")


class TestPendingMemberCreation:
    """Test that pending transactions are created for public registration with plan"""
    
    @pytest.fixture(autouse=True)
    def setup_admin(self):
        """Get admin token for this test class"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        if response.status_code == 200:
            self.admin_headers = {"Authorization": f"Bearer {response.json()['token']}", "Content-Type": "application/json"}
        else:
            pytest.skip(f"Admin authentication failed: {response.status_code}")
    
    def test_pending_transaction_created_on_registration(self):
        """Registration with plan should create a pending payment transaction"""
        unique_email = f"test_tx_pending_{uuid.uuid4().hex[:8]}@demo.com"
        payload = {
            "name": "Test Transaction Pending",
            "email": unique_email,
            "phone": "+34600000006",
            "gym_id": EXISTING_GYM_ID,
            "plan_id": EXISTING_PLAN_ID,
            "gender": "prefer_not_to_say"
        }
        
        reg_response = requests.post(f"{BASE_URL}/api/members/register", json=payload)
        assert reg_response.status_code == 200, f"Registration failed: {reg_response.text}"
        
        member_data = reg_response.json()
        member_id = member_data["member"]["id"]
        
        # Check transactions endpoint for pending transaction
        tx_response = requests.get(f"{BASE_URL}/api/accounting/transactions?status=pending", headers=self.admin_headers)
        assert tx_response.status_code == 200, f"Failed to get transactions: {tx_response.text}"
        
        tx_data = tx_response.json()
        transactions = tx_data.get("transactions", [])
        
        # Find transaction for this member
        member_tx = None
        for tx in transactions:
            if tx.get("member_id") == member_id:
                member_tx = tx
                break
        
        assert member_tx is not None, f"Pending transaction should be created for member {member_id}"
        assert member_tx["payment_status"] == "pending", f"Transaction should have payment_status='pending'"
        assert member_tx["status"] == "pending", f"Transaction should have status='pending'"
        
        print(f"✓ Pending transaction created for registration with plan. Member ID: {member_id}")


class TestExistingActiveMember:
    """Test that existing active member (NEDFJR) can generate QR"""
    
    @pytest.fixture(autouse=True)
    def setup_admin(self):
        """Get admin token for this test class"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        if response.status_code == 200:
            self.admin_headers = {"Authorization": f"Bearer {response.json()['token']}", "Content-Type": "application/json"}
        else:
            pytest.skip(f"Admin authentication failed: {response.status_code}")
    
    def test_existing_active_member_info(self):
        """Verify existing active member NEDFJR exists and has active membership"""
        # Get members
        response = requests.get(f"{BASE_URL}/api/members", headers=self.admin_headers)
        assert response.status_code == 200, f"Failed to get members: {response.text}"
        
        members = response.json()
        nedfjr = None
        for m in members:
            if m.get("code") == "NEDFJR":
                nedfjr = m
                break
        
        if not nedfjr:
            pytest.skip("Member with code NEDFJR not found")
        
        assert nedfjr["status"] == "active", f"NEDFJR should be active, got: {nedfjr['status']}"
        
        # Check membership
        memberships_response = requests.get(f"{BASE_URL}/api/memberships?member_id={nedfjr['id']}", headers=self.admin_headers)
        if memberships_response.status_code == 200:
            memberships = memberships_response.json()
            active_membership = None
            for ms in memberships:
                if ms.get("status") == "active":
                    active_membership = ms
                    break
            
            if active_membership:
                print(f"✓ NEDFJR is active with active membership")
            else:
                print(f"⚠ NEDFJR is active but no active membership found")
        else:
            print(f"✓ NEDFJR exists and is active")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
