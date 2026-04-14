"""
Iteration 27 - Membership Expiration Edit Feature Tests
Tests for PUT /api/members/{member_id}/membership endpoint
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://stripe-gym-payments.preview.emergentagent.com')

class TestMembershipExpirationEdit:
    """Tests for the membership expiration edit feature"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Get auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/admin/login",
            json={"email": "admin@gymaccess.com", "password": "admin123"}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json()["token"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        # Find a member with membership
        members_response = requests.get(
            f"{BASE_URL}/api/members",
            headers=self.headers
        )
        assert members_response.status_code == 200
        members = members_response.json()
        
        self.member_with_membership = None
        self.member_without_membership = None
        
        for member in members:
            if member.get("membership") and not self.member_with_membership:
                self.member_with_membership = member
            if not member.get("membership") and not self.member_without_membership:
                self.member_without_membership = member
            if self.member_with_membership and self.member_without_membership:
                break
    
    def test_update_membership_expiration_success(self):
        """Test: Successfully update membership expiration date with comment"""
        if not self.member_with_membership:
            pytest.skip("No member with membership found")
        
        member_id = self.member_with_membership["id"]
        new_date = "2026-08-15"
        
        response = requests.put(
            f"{BASE_URL}/api/members/{member_id}/membership",
            headers=self.headers,
            json={"end_date": new_date, "comment": "Extended for testing"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["success"] == True
        assert "Vencimiento actualizado" in data["message"]
        assert new_date in data["message"]
    
    def test_update_membership_without_comment(self):
        """Test: Update membership expiration without comment (should work)"""
        if not self.member_with_membership:
            pytest.skip("No member with membership found")
        
        member_id = self.member_with_membership["id"]
        new_date = "2026-09-01"
        
        response = requests.put(
            f"{BASE_URL}/api/members/{member_id}/membership",
            headers=self.headers,
            json={"end_date": new_date}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["success"] == True
    
    def test_update_membership_missing_end_date(self):
        """Test: Update without end_date should return 400"""
        if not self.member_with_membership:
            pytest.skip("No member with membership found")
        
        member_id = self.member_with_membership["id"]
        
        response = requests.put(
            f"{BASE_URL}/api/members/{member_id}/membership",
            headers=self.headers,
            json={"comment": "No date provided"}
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        data = response.json()
        assert "Fecha de vencimiento requerida" in data["detail"]
    
    def test_update_membership_nonexistent_member(self):
        """Test: Update for non-existent member should return 404"""
        response = requests.put(
            f"{BASE_URL}/api/members/non-existent-member-id/membership",
            headers=self.headers,
            json={"end_date": "2026-07-15"}
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
        data = response.json()
        assert "Socio no encontrado" in data["detail"]
    
    def test_update_membership_member_without_membership(self):
        """Test: Update for member without membership should return 404"""
        if not self.member_without_membership:
            pytest.skip("No member without membership found")
        
        member_id = self.member_without_membership["id"]
        
        response = requests.put(
            f"{BASE_URL}/api/members/{member_id}/membership",
            headers=self.headers,
            json={"end_date": "2026-07-15"}
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
        data = response.json()
        assert "No se encontro membresia activa" in data["detail"]
    
    def test_update_membership_sets_status_based_on_date(self):
        """Test: Updating to future date sets status to active, past date sets to expired"""
        if not self.member_with_membership:
            pytest.skip("No member with membership found")
        
        member_id = self.member_with_membership["id"]
        
        # Set to future date - should be active
        future_date = "2027-12-31"
        response = requests.put(
            f"{BASE_URL}/api/members/{member_id}/membership",
            headers=self.headers,
            json={"end_date": future_date, "comment": "Set to future date"}
        )
        assert response.status_code == 200
        
        # Verify member's membership status
        member_response = requests.get(
            f"{BASE_URL}/api/members",
            headers=self.headers
        )
        members = member_response.json()
        updated_member = next((m for m in members if m["id"] == member_id), None)
        assert updated_member is not None
        assert updated_member["membership"]["end_date"] == future_date
        # Status should be active for future date
        assert updated_member["membership"]["status"] == "active"


class TestMembershipModalIntegration:
    """Tests for the Assign Membership modal (existing functionality)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Get auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/admin/login",
            json={"email": "admin@gymaccess.com", "password": "admin123"}
        )
        assert response.status_code == 200
        self.token = response.json()["token"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_get_members_returns_membership_data(self):
        """Test: GET /api/members returns membership data for enrichment"""
        response = requests.get(
            f"{BASE_URL}/api/members",
            headers=self.headers
        )
        
        assert response.status_code == 200
        members = response.json()
        assert isinstance(members, list)
        
        # Check that members with memberships have the expected structure
        members_with_membership = [m for m in members if m.get("membership")]
        if members_with_membership:
            member = members_with_membership[0]
            assert "membership" in member
            membership = member["membership"]
            assert "plan_name" in membership
            assert "end_date" in membership
            assert "status" in membership
    
    def test_get_plans_for_membership_assignment(self):
        """Test: GET /api/plans returns plans for membership assignment modal"""
        response = requests.get(
            f"{BASE_URL}/api/plans",
            headers=self.headers
        )
        
        assert response.status_code == 200
        plans = response.json()
        assert isinstance(plans, list)
        
        if plans:
            plan = plans[0]
            assert "id" in plan
            assert "name" in plan
            assert "price" in plan
            assert "duration_days" in plan


class TestPermissions:
    """Tests for permission checks on membership edit"""
    
    def test_unauthenticated_request_fails(self):
        """Test: Request without auth token should fail"""
        response = requests.put(
            f"{BASE_URL}/api/members/some-id/membership",
            headers={"Content-Type": "application/json"},
            json={"end_date": "2026-07-15"}
        )
        
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
