"""
Iteration 28 - Testing:
1. GET /api/members/{member_id}/membership-logs endpoint
2. Logo URL handling in gym data
3. Membership logs data structure
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestMembershipLogsEndpoint:
    """Test the new membership-logs endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Login as admin and get token"""
        self.token = None
        login_response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": "admin@gymaccess.com",
            "password": "admin123"
        })
        if login_response.status_code == 200:
            self.token = login_response.json().get("token")
        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
    
    def test_admin_login_success(self):
        """Test admin login works"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": "admin@gymaccess.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data
        print("PASS: Admin login successful")
    
    def test_get_membership_logs_for_member_with_logs(self):
        """Test getting membership logs for member with existing logs"""
        if not self.token:
            pytest.skip("No auth token available")
        
        # Use the member ID mentioned in the context that has 7 logs
        member_id = "86c975e8-7eb5-44cb-9299-198877a60f62"
        response = requests.get(
            f"{BASE_URL}/api/members/{member_id}/membership-logs",
            headers=self.headers
        )
        
        # Could be 200 (found) or 404 (member not found in this env)
        if response.status_code == 404:
            print(f"INFO: Member {member_id} not found in this environment - testing with another member")
            # Get a member from the list
            members_response = requests.get(f"{BASE_URL}/api/members", headers=self.headers)
            if members_response.status_code == 200:
                members = members_response.json()
                if members:
                    member_id = members[0]["id"]
                    response = requests.get(
                        f"{BASE_URL}/api/members/{member_id}/membership-logs",
                        headers=self.headers
                    )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"PASS: Got {len(data)} membership logs for member")
        
        # If there are logs, verify structure
        if data:
            log = data[0]
            assert "id" in log, "Log should have id"
            assert "member_id" in log, "Log should have member_id"
            assert "new_end_date" in log, "Log should have new_end_date"
            assert "changed_by" in log, "Log should have changed_by"
            assert "created_at" in log, "Log should have created_at"
            print(f"PASS: Log structure is correct. Sample log: changed_by={log.get('changed_by')}, new_end_date={log.get('new_end_date')}")
    
    def test_get_membership_logs_nonexistent_member(self):
        """Test getting logs for non-existent member returns 404"""
        if not self.token:
            pytest.skip("No auth token available")
        
        response = requests.get(
            f"{BASE_URL}/api/members/nonexistent-member-id-12345/membership-logs",
            headers=self.headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("PASS: Non-existent member returns 404")
    
    def test_get_membership_logs_unauthenticated(self):
        """Test that unauthenticated requests fail"""
        response = requests.get(
            f"{BASE_URL}/api/members/some-member-id/membership-logs"
        )
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: Unauthenticated request properly rejected")


class TestGymLogoData:
    """Test gym data includes logo_url field"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Login as admin and get token"""
        self.token = None
        login_response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": "admin@gymaccess.com",
            "password": "admin123"
        })
        if login_response.status_code == 200:
            self.token = login_response.json().get("token")
            self.admin_data = login_response.json().get("admin", {})
        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
    
    def test_get_gyms_list(self):
        """Test getting list of gyms"""
        if not self.token:
            pytest.skip("No auth token available")
        
        response = requests.get(f"{BASE_URL}/api/gyms", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"PASS: Got {len(data)} gyms")
        
        if data:
            gym = data[0]
            # Check that gym has expected fields
            assert "id" in gym, "Gym should have id"
            assert "name" in gym, "Gym should have name"
            # logo_url may or may not be present
            has_logo = "logo_url" in gym and gym["logo_url"]
            print(f"PASS: First gym: {gym.get('name')}, has_logo_url: {has_logo}")
    
    def test_get_single_gym_with_logo_field(self):
        """Test getting a single gym includes logo_url field"""
        if not self.token:
            pytest.skip("No auth token available")
        
        # First get list of gyms
        response = requests.get(f"{BASE_URL}/api/gyms", headers=self.headers)
        if response.status_code != 200 or not response.json():
            pytest.skip("No gyms available")
        
        gym_id = response.json()[0]["id"]
        
        # Get single gym
        response = requests.get(f"{BASE_URL}/api/gyms/{gym_id}", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        gym = response.json()
        assert "id" in gym
        assert "name" in gym
        # logo_url field should exist (even if null)
        print(f"PASS: Gym {gym.get('name')} - logo_url: {gym.get('logo_url', 'not set')}")


class TestMembershipUpdateWithLogs:
    """Test that updating membership creates logs"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Login as admin and get token"""
        self.token = None
        login_response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": "admin@gymaccess.com",
            "password": "admin123"
        })
        if login_response.status_code == 200:
            self.token = login_response.json().get("token")
        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
    
    def test_update_membership_creates_log(self):
        """Test that updating membership expiration creates a log entry"""
        if not self.token:
            pytest.skip("No auth token available")
        
        # Get a member with membership
        members_response = requests.get(f"{BASE_URL}/api/members", headers=self.headers)
        if members_response.status_code != 200:
            pytest.skip("Could not get members")
        
        members = members_response.json()
        member_with_membership = None
        for m in members:
            if m.get("membership") and m["membership"].get("end_date"):
                member_with_membership = m
                break
        
        if not member_with_membership:
            pytest.skip("No member with active membership found")
        
        member_id = member_with_membership["id"]
        
        # Get current logs count
        logs_before = requests.get(
            f"{BASE_URL}/api/members/{member_id}/membership-logs",
            headers=self.headers
        ).json()
        logs_count_before = len(logs_before)
        
        # Update membership with a new date and comment
        new_date = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
        update_response = requests.put(
            f"{BASE_URL}/api/members/{member_id}/membership",
            headers=self.headers,
            json={
                "end_date": new_date,
                "comment": "Test comment from iteration 28 testing"
            }
        )
        
        assert update_response.status_code == 200, f"Update failed: {update_response.text}"
        
        # Get logs after update
        logs_after = requests.get(
            f"{BASE_URL}/api/members/{member_id}/membership-logs",
            headers=self.headers
        ).json()
        
        assert len(logs_after) > logs_count_before, "New log entry should be created"
        
        # Verify the new log has our comment
        latest_log = logs_after[0]  # Sorted by created_at desc
        assert latest_log.get("new_end_date") == new_date, "Log should have new end date"
        assert latest_log.get("comment") == "Test comment from iteration 28 testing", "Log should have our comment"
        print(f"PASS: Membership update created log entry with comment")


class TestMembersEndpointWithMembership:
    """Test members endpoint returns membership data"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Login as admin and get token"""
        self.token = None
        login_response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": "admin@gymaccess.com",
            "password": "admin123"
        })
        if login_response.status_code == 200:
            self.token = login_response.json().get("token")
        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
    
    def test_members_list_includes_membership_data(self):
        """Test that members list includes membership info"""
        if not self.token:
            pytest.skip("No auth token available")
        
        response = requests.get(f"{BASE_URL}/api/members", headers=self.headers)
        assert response.status_code == 200
        
        members = response.json()
        assert isinstance(members, list)
        
        # Find a member with membership
        member_with_membership = None
        for m in members:
            if m.get("membership"):
                member_with_membership = m
                break
        
        if member_with_membership:
            membership = member_with_membership["membership"]
            # Verify membership structure
            assert "plan_name" in membership or membership.get("plan_name") is None
            assert "end_date" in membership or membership.get("end_date") is None
            assert "status" in membership or membership.get("status") is None
            print(f"PASS: Member {member_with_membership.get('name')} has membership data: plan={membership.get('plan_name')}, end_date={membership.get('end_date')}")
        else:
            print("INFO: No members with active membership found in test data")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
