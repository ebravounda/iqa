"""
Iteration 17 - Testing 5 New Modules:
1. Demo Account (login/cleanup)
2. Gamification (ranking, badges, streaks)
3. Routines (CRUD, member view)
4. Device Management (heartbeat, commands, status)
5. Stripe Auto-payment (mocked - requires real keys)
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# ==================== FIXTURES ====================

@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session

@pytest.fixture(scope="module")
def super_admin_token(api_client):
    """Get super admin token"""
    response = api_client.post(f"{BASE_URL}/api/auth/admin/login", json={
        "email": "admin@gymaccess.com",
        "password": "admin123"
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Super admin authentication failed")

@pytest.fixture(scope="module")
def super_admin_client(api_client, super_admin_token):
    """Session with super admin auth"""
    api_client.headers.update({"Authorization": f"Bearer {super_admin_token}"})
    return api_client

@pytest.fixture(scope="module")
def demo_data(api_client):
    """Create demo data and return token"""
    # First cleanup any existing demo data
    api_client.post(f"{BASE_URL}/api/demo/cleanup")
    # Create fresh demo data
    response = api_client.post(f"{BASE_URL}/api/demo/login")
    if response.status_code == 200:
        data = response.json()
        yield data
        # Cleanup after tests
        api_client.post(f"{BASE_URL}/api/demo/cleanup")
    else:
        pytest.skip("Demo login failed")

@pytest.fixture(scope="module")
def demo_admin_client(api_client, demo_data):
    """Session with demo admin auth"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {demo_data['token']}"
    })
    return session


# ==================== MODULE 1: DEMO ACCOUNT ====================

class TestDemoAccount:
    """Demo login and cleanup tests"""
    
    def test_demo_login_creates_data_and_returns_token(self, api_client):
        """POST /api/demo/login creates demo data and returns token with is_demo=true"""
        # Cleanup first
        api_client.post(f"{BASE_URL}/api/demo/cleanup")
        
        response = api_client.post(f"{BASE_URL}/api/demo/login")
        assert response.status_code == 200, f"Demo login failed: {response.text}"
        
        data = response.json()
        assert "token" in data, "Token not returned"
        assert "admin" in data, "Admin data not returned"
        assert data.get("is_demo") == True, "is_demo flag not set"
        assert data["admin"]["role"] == "gym_admin", "Demo admin should be gym_admin role"
        assert data["admin"]["email"] == "demo@ingresoqr.com", "Demo email mismatch"
        print(f"✓ Demo login successful, token received, is_demo={data.get('is_demo')}")
    
    def test_demo_cleanup_removes_all_demo_data(self, api_client):
        """POST /api/demo/cleanup removes all demo data from DB"""
        # First create demo data
        api_client.post(f"{BASE_URL}/api/demo/login")
        
        # Then cleanup
        response = api_client.post(f"{BASE_URL}/api/demo/cleanup")
        assert response.status_code == 200, f"Demo cleanup failed: {response.text}"
        
        data = response.json()
        assert "message" in data, "Cleanup message not returned"
        assert "eliminados" in data["message"].lower() or "demo" in data["message"].lower()
        print(f"✓ Demo cleanup successful: {data['message']}")


# ==================== MODULE 2: GAMIFICATION ====================

class TestGamification:
    """Gamification ranking and member badges tests"""
    
    def test_gamification_ranking_returns_ranking_list(self, demo_admin_client, demo_data):
        """GET /api/gamification/ranking returns ranking of members with points, streaks, badges"""
        response = demo_admin_client.get(f"{BASE_URL}/api/gamification/ranking")
        assert response.status_code == 200, f"Ranking fetch failed: {response.text}"
        
        data = response.json()
        assert "ranking" in data, "Ranking key not in response"
        ranking = data["ranking"]
        assert isinstance(ranking, list), "Ranking should be a list"
        
        if len(ranking) > 0:
            member = ranking[0]
            assert "member_id" in member, "member_id missing"
            assert "name" in member, "name missing"
            assert "points" in member, "points missing"
            assert "current_streak" in member, "current_streak missing"
            assert "max_streak" in member, "max_streak missing"
            assert "total_visits" in member, "total_visits missing"
            assert "badges_count" in member, "badges_count missing"
            assert "earned_badges" in member, "earned_badges missing"
            assert "rank" in member, "rank missing"
            print(f"✓ Ranking returned {len(ranking)} members, top: {member['name']} with {member['points']} points")
        else:
            print("✓ Ranking returned empty list (no members with visits)")
    
    def test_gamification_ranking_requires_auth(self, api_client):
        """GET /api/gamification/ranking requires authentication"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        response = session.get(f"{BASE_URL}/api/gamification/ranking")
        assert response.status_code in [401, 403], "Should require auth"
        print("✓ Ranking endpoint requires authentication")
    
    def test_gamification_me_requires_member_token(self, api_client):
        """GET /api/gamification/me requires member token (not admin)"""
        # Using admin token should fail or return different data
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        response = session.get(f"{BASE_URL}/api/gamification/me")
        assert response.status_code in [401, 403, 422], "Should require member auth"
        print("✓ /gamification/me requires member authentication")


# ==================== MODULE 3: ROUTINES ====================

class TestRoutines:
    """Routine CRUD and member view tests"""
    
    def test_create_routine_with_days_and_exercises(self, demo_admin_client, demo_data):
        """POST /api/routines creates a routine with days and exercises"""
        # Get a demo member to assign routine
        members_resp = demo_admin_client.get(f"{BASE_URL}/api/members?gym_id=demo-gym-001")
        members = members_resp.json() if isinstance(members_resp.json(), list) else members_resp.json().get("members", [])
        
        if not members:
            pytest.skip("No demo members found")
        
        member_id = members[0]["id"]
        
        routine_data = {
            "name": "TEST_Rutina Full Body",
            "description": "Rutina de prueba para testing",
            "member_id": member_id,
            "gym_id": "demo-gym-001",
            "days": [
                {
                    "name": "Dia 1 - Pecho y Triceps",
                    "exercises": [
                        {"name": "Press de banca", "sets": 4, "reps": 10, "rest": 90, "notes": ""},
                        {"name": "Fondos", "sets": 3, "reps": 12, "rest": 60, "notes": ""}
                    ]
                },
                {
                    "name": "Dia 2 - Espalda y Biceps",
                    "exercises": [
                        {"name": "Dominadas", "sets": 4, "reps": 8, "rest": 90, "notes": ""},
                        {"name": "Curl biceps", "sets": 3, "reps": 12, "rest": 60, "notes": ""}
                    ]
                }
            ]
        }
        
        response = demo_admin_client.post(f"{BASE_URL}/api/routines", json=routine_data)
        assert response.status_code == 200, f"Routine creation failed: {response.text}"
        
        data = response.json()
        assert "id" in data, "Routine ID not returned"
        assert data["name"] == routine_data["name"], "Name mismatch"
        assert data["member_id"] == member_id, "Member ID mismatch"
        assert len(data["days"]) == 2, "Days count mismatch"
        assert len(data["days"][0]["exercises"]) == 2, "Exercises count mismatch"
        print(f"✓ Routine created: {data['name']} with {len(data['days'])} days")
        
        # Store for later tests
        TestRoutines.created_routine_id = data["id"]
    
    def test_get_routines_list(self, demo_admin_client):
        """GET /api/routines returns routines list"""
        response = demo_admin_client.get(f"{BASE_URL}/api/routines")
        assert response.status_code == 200, f"Get routines failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Routines should be a list"
        print(f"✓ Routines list returned {len(data)} routines")
    
    def test_delete_routine(self, demo_admin_client):
        """DELETE /api/routines/{id} removes routine"""
        routine_id = getattr(TestRoutines, 'created_routine_id', None)
        if not routine_id:
            pytest.skip("No routine created to delete")
        
        response = demo_admin_client.delete(f"{BASE_URL}/api/routines/{routine_id}")
        assert response.status_code == 200, f"Delete routine failed: {response.text}"
        
        data = response.json()
        assert "message" in data, "Delete message not returned"
        print(f"✓ Routine deleted: {data['message']}")
        
        # Verify deletion
        get_response = demo_admin_client.get(f"{BASE_URL}/api/routines")
        routines = get_response.json()
        routine_ids = [r["id"] for r in routines]
        assert routine_id not in routine_ids, "Routine still exists after deletion"
        print("✓ Verified routine no longer in list")
    
    def test_routines_me_requires_member_token(self, api_client):
        """GET /api/routines/me requires member token"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        response = session.get(f"{BASE_URL}/api/routines/me")
        assert response.status_code in [401, 403, 422], "Should require member auth"
        print("✓ /routines/me requires member authentication")


# ==================== MODULE 4: DEVICE MANAGEMENT ====================

class TestDeviceManagement:
    """Device heartbeat, commands, and status tests"""
    
    def test_devices_status_requires_super_admin(self, demo_admin_client):
        """GET /api/devices/status requires super_admin role"""
        response = demo_admin_client.get(f"{BASE_URL}/api/devices/status")
        # Demo admin is gym_admin, should get 403
        assert response.status_code == 403, f"Expected 403 for gym_admin, got {response.status_code}"
        print("✓ /devices/status correctly requires super_admin role")
    
    def test_devices_status_returns_list_for_super_admin(self, super_admin_client):
        """GET /api/devices/status returns all devices with computed online/offline status"""
        response = super_admin_client.get(f"{BASE_URL}/api/devices/status")
        assert response.status_code == 200, f"Get devices status failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Devices should be a list"
        
        if len(data) > 0:
            device = data[0]
            assert "id" in device, "Device ID missing"
            assert "computed_status" in device, "computed_status missing"
            assert device["computed_status"] in ["online", "offline"], "Invalid computed_status"
            assert "gym_name" in device, "gym_name missing"
            print(f"✓ Devices status returned {len(data)} devices")
        else:
            print("✓ Devices status returned empty list (no devices)")
    
    def test_device_heartbeat_requires_gym_token(self, api_client):
        """POST /api/devices/{id}/heartbeat requires gym_token in body"""
        response = api_client.post(
            f"{BASE_URL}/api/devices/test-device/heartbeat",
            json={"ip_address": "192.168.1.100"}
        )
        assert response.status_code == 401, f"Expected 401 without gym_token, got {response.status_code}"
        print("✓ Heartbeat requires gym_token")
    
    def test_device_heartbeat_with_invalid_token(self, api_client):
        """POST /api/devices/{id}/heartbeat rejects invalid gym_token"""
        response = api_client.post(
            f"{BASE_URL}/api/devices/test-device/heartbeat",
            json={"gym_token": "invalid-token", "ip_address": "192.168.1.100"}
        )
        assert response.status_code == 401, f"Expected 401 with invalid token, got {response.status_code}"
        print("✓ Heartbeat rejects invalid gym_token")
    
    def test_send_command_requires_super_admin(self, demo_admin_client):
        """POST /api/devices/{id}/command requires super_admin role"""
        response = demo_admin_client.post(
            f"{BASE_URL}/api/devices/test-device/command",
            json={"command": "reboot"}
        )
        assert response.status_code == 403, f"Expected 403 for gym_admin, got {response.status_code}"
        print("✓ Send command correctly requires super_admin role")
    
    def test_send_command_validates_command_type(self, super_admin_client):
        """POST /api/devices/{id}/command validates command type"""
        response = super_admin_client.post(
            f"{BASE_URL}/api/devices/test-device/command",
            json={"command": "invalid_command"}
        )
        assert response.status_code == 400, f"Expected 400 for invalid command, got {response.status_code}"
        assert "no valido" in response.json().get("detail", "").lower() or "reboot" in response.json().get("detail", "").lower()
        print("✓ Send command validates command type (reboot, update, restart_service)")
    
    def test_get_device_commands_requires_super_admin(self, demo_admin_client):
        """GET /api/devices/{id}/commands requires super_admin role"""
        response = demo_admin_client.get(f"{BASE_URL}/api/devices/test-device/commands")
        assert response.status_code == 403, f"Expected 403 for gym_admin, got {response.status_code}"
        print("✓ Get device commands correctly requires super_admin role")


# ==================== MODULE 5: STRIPE AUTO-PAYMENT (MOCKED) ====================

class TestStripeAutoPayment:
    """Stripe payment link and webhook tests (requires real Stripe keys)"""
    
    def test_create_payment_link_requires_stripe_config(self, demo_admin_client, demo_data):
        """POST /api/payments/create-link requires Stripe to be configured"""
        # Get a demo member and plan
        members_resp = demo_admin_client.get(f"{BASE_URL}/api/members?gym_id=demo-gym-001")
        members = members_resp.json() if isinstance(members_resp.json(), list) else members_resp.json().get("members", [])
        
        plans_resp = demo_admin_client.get(f"{BASE_URL}/api/plans?gym_id=demo-gym-001")
        plans = plans_resp.json() if isinstance(plans_resp.json(), list) else plans_resp.json().get("plans", [])
        
        if not members or not plans:
            pytest.skip("No demo members or plans found")
        
        response = demo_admin_client.post(f"{BASE_URL}/api/payments/create-link", json={
            "member_id": members[0]["id"],
            "plan_id": plans[0]["id"]
        })
        
        # Should fail because demo gym doesn't have Stripe configured
        assert response.status_code == 400, f"Expected 400 (Stripe not configured), got {response.status_code}"
        assert "stripe" in response.json().get("detail", "").lower()
        print("✓ Create payment link correctly requires Stripe configuration")
    
    def test_stripe_webhook_accepts_checkout_completed(self, api_client):
        """POST /api/payments/stripe-webhook accepts checkout.session.completed event"""
        webhook_payload = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_123",
                    "metadata": {
                        "member_id": "test-member",
                        "plan_id": "test-plan",
                        "gym_id": "test-gym"
                    },
                    "amount_total": 2999
                }
            }
        }
        
        response = api_client.post(f"{BASE_URL}/api/payments/stripe-webhook", json=webhook_payload)
        assert response.status_code == 200, f"Webhook failed: {response.text}"
        
        data = response.json()
        assert data.get("received") == True, "Webhook should return received: true"
        print("✓ Stripe webhook accepts checkout.session.completed event")


# ==================== INTEGRATION TESTS ====================

class TestIntegration:
    """Cross-module integration tests"""
    
    def test_demo_creates_access_logs_for_gamification(self, api_client):
        """Demo login creates access logs that gamification can use"""
        # Cleanup and create fresh demo
        api_client.post(f"{BASE_URL}/api/demo/cleanup")
        demo_resp = api_client.post(f"{BASE_URL}/api/demo/login")
        assert demo_resp.status_code == 200
        
        demo_data = demo_resp.json()
        token = demo_data["token"]
        
        # Check gamification ranking with demo token
        session = requests.Session()
        session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        })
        
        ranking_resp = session.get(f"{BASE_URL}/api/gamification/ranking")
        assert ranking_resp.status_code == 200
        
        ranking = ranking_resp.json().get("ranking", [])
        # Demo creates 5 members with 30 days of access logs
        assert len(ranking) >= 1, "Demo should create members with access logs"
        
        # Check that members have points from visits
        total_points = sum(m["points"] for m in ranking)
        assert total_points > 0, "Demo members should have points from access logs"
        print(f"✓ Demo created {len(ranking)} members with total {total_points} points")
        
        # Cleanup
        api_client.post(f"{BASE_URL}/api/demo/cleanup")
    
    def test_full_routine_workflow(self, api_client):
        """Test complete routine workflow: create -> list -> delete"""
        # Create demo
        api_client.post(f"{BASE_URL}/api/demo/cleanup")
        demo_resp = api_client.post(f"{BASE_URL}/api/demo/login")
        demo_data = demo_resp.json()
        token = demo_data["token"]
        
        session = requests.Session()
        session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        })
        
        # Get a member
        members_resp = session.get(f"{BASE_URL}/api/members?gym_id=demo-gym-001")
        members = members_resp.json() if isinstance(members_resp.json(), list) else members_resp.json().get("members", [])
        
        if not members:
            api_client.post(f"{BASE_URL}/api/demo/cleanup")
            pytest.skip("No demo members")
        
        # Create routine
        routine_data = {
            "name": "TEST_Workflow Routine",
            "member_id": members[0]["id"],
            "gym_id": "demo-gym-001",
            "days": [{"name": "Day 1", "exercises": [{"name": "Squats", "sets": 3, "reps": 10, "rest": 60}]}]
        }
        
        create_resp = session.post(f"{BASE_URL}/api/routines", json=routine_data)
        assert create_resp.status_code == 200
        routine_id = create_resp.json()["id"]
        print(f"✓ Created routine: {routine_id}")
        
        # List routines
        list_resp = session.get(f"{BASE_URL}/api/routines")
        assert list_resp.status_code == 200
        routines = list_resp.json()
        assert any(r["id"] == routine_id for r in routines), "Created routine not in list"
        print(f"✓ Routine appears in list")
        
        # Delete routine
        delete_resp = session.delete(f"{BASE_URL}/api/routines/{routine_id}")
        assert delete_resp.status_code == 200
        print(f"✓ Routine deleted")
        
        # Verify deletion
        list_resp2 = session.get(f"{BASE_URL}/api/routines")
        routines2 = list_resp2.json()
        assert not any(r["id"] == routine_id for r in routines2), "Routine still exists"
        print(f"✓ Routine no longer in list")
        
        # Cleanup
        api_client.post(f"{BASE_URL}/api/demo/cleanup")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
