"""
Test suite for Stripe configuration and Access Statistics endpoints
Tests new features: Stripe config per gym, daily/hourly access stats, member attendance stats
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
SUPER_ADMIN_EMAIL = "admin@gymaccess.com"
SUPER_ADMIN_PASSWORD = "admin123"
GYM_ADMIN_EMAIL = "admin@fitzone.com"
GYM_ADMIN_PASSWORD = "admin123"
GYM_ID = "efe99507-15d5-4e54-9f07-30d2507894e0"
MEMBER_CODE = "LRF4HL"
MEMBER_ID = "6ff17746-c8c4-4d8f-b241-051a04fc0ba0"


@pytest.fixture(scope="module")
def super_admin_token():
    """Get super admin auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
        "email": SUPER_ADMIN_EMAIL,
        "password": SUPER_ADMIN_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip(f"Super admin login failed: {response.text}")
    return response.json().get("token")


@pytest.fixture(scope="module")
def gym_admin_token():
    """Get gym admin auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
        "email": GYM_ADMIN_EMAIL,
        "password": GYM_ADMIN_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip(f"Gym admin login failed: {response.text}")
    return response.json().get("token")


@pytest.fixture(scope="module")
def member_token():
    """Get member auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/member/login?code={MEMBER_CODE}")
    if response.status_code != 200:
        pytest.skip(f"Member login failed: {response.text}")
    return response.json().get("token")


class TestAdminLogin:
    """Test admin authentication"""
    
    def test_super_admin_login(self):
        """Test super admin login with admin@gymaccess.com"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "token" in data
        assert "admin" in data
        assert data["admin"]["role"] == "super_admin"
        # Super admin has no gym_id (key may be absent or None)
        assert data["admin"].get("gym_id") is None
    
    def test_gym_admin_login(self):
        """Test gym admin login with admin@fitzone.com"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": GYM_ADMIN_EMAIL,
            "password": GYM_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "token" in data
        assert "admin" in data
        assert data["admin"]["role"] == "gym_admin"
        assert data["admin"]["gym_id"] == GYM_ID


class TestDailyAccessStats:
    """Test GET /api/access/stats/daily endpoint"""
    
    def test_daily_stats_returns_7_days(self, gym_admin_token):
        """Test daily access stats returns 7 days of data"""
        response = requests.get(
            f"{BASE_URL}/api/access/stats/daily?days=7",
            headers={"Authorization": f"Bearer {gym_admin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 7, f"Expected 7 days, got {len(data)}"
        
        # Verify structure of each day
        for day in data:
            assert "date" in day
            assert "day_name" in day
            assert "accesos" in day
            assert "entradas" in day
    
    def test_daily_stats_custom_days(self, gym_admin_token):
        """Test daily access stats with custom days parameter"""
        response = requests.get(
            f"{BASE_URL}/api/access/stats/daily?days=14",
            headers={"Authorization": f"Bearer {gym_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 14, f"Expected 14 days, got {len(data)}"
    
    def test_daily_stats_requires_auth(self):
        """Test daily stats requires authentication"""
        response = requests.get(f"{BASE_URL}/api/access/stats/daily?days=7")
        assert response.status_code in [401, 403]


class TestHourlyAccessStats:
    """Test GET /api/access/stats/hourly endpoint"""
    
    def test_hourly_stats_returns_24_hours(self, gym_admin_token):
        """Test hourly access stats returns 24 hourly entries"""
        response = requests.get(
            f"{BASE_URL}/api/access/stats/hourly",
            headers={"Authorization": f"Bearer {gym_admin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 24, f"Expected 24 hours, got {len(data)}"
        
        # Verify structure
        for hour in data:
            assert "hour" in hour
            assert "accesos" in hour
    
    def test_hourly_stats_requires_auth(self):
        """Test hourly stats requires authentication"""
        response = requests.get(f"{BASE_URL}/api/access/stats/hourly")
        assert response.status_code in [401, 403]


class TestMemberAccessStats:
    """Test GET /api/access/stats/member/{member_id} endpoint"""
    
    def test_member_stats_returns_data(self, gym_admin_token):
        """Test member access stats returns attendance data"""
        response = requests.get(
            f"{BASE_URL}/api/access/stats/member/{MEMBER_ID}?days=30",
            headers={"Authorization": f"Bearer {gym_admin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify structure
        assert "member" in data
        assert "total_entries" in data
        assert "days_attended" in data
        assert "period_days" in data
        assert "attendance_rate" in data
        assert "daily_breakdown" in data
        assert "recent_logs" in data
        
        # Verify member info
        assert data["member"]["id"] == MEMBER_ID
        assert "name" in data["member"]
        assert "code" in data["member"]
    
    def test_member_stats_invalid_member(self, gym_admin_token):
        """Test member stats with invalid member ID returns 404"""
        response = requests.get(
            f"{BASE_URL}/api/access/stats/member/invalid-member-id?days=30",
            headers={"Authorization": f"Bearer {gym_admin_token}"}
        )
        assert response.status_code == 404


class TestStripeConfig:
    """Test Stripe configuration endpoints"""
    
    def test_get_stripe_config(self, gym_admin_token):
        """Test GET /api/gyms/{gym_id}/stripe-config returns masked key and currency"""
        response = requests.get(
            f"{BASE_URL}/api/gyms/{GYM_ID}/stripe-config",
            headers={"Authorization": f"Bearer {gym_admin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify structure
        assert "has_stripe_key" in data
        assert "masked_key" in data
        assert "currency" in data
        assert isinstance(data["has_stripe_key"], bool)
    
    def test_update_stripe_config(self, gym_admin_token):
        """Test PUT /api/gyms/{gym_id}/stripe-config saves configuration"""
        response = requests.put(
            f"{BASE_URL}/api/gyms/{GYM_ID}/stripe-config",
            headers={"Authorization": f"Bearer {gym_admin_token}"},
            json={
                "stripe_secret_key": "sk_test_emergent_test_key",
                "stripe_currency": "mxn"
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Verify the config was saved
        get_response = requests.get(
            f"{BASE_URL}/api/gyms/{GYM_ID}/stripe-config",
            headers={"Authorization": f"Bearer {gym_admin_token}"}
        )
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["has_stripe_key"] == True
        assert data["currency"] == "mxn"
        assert "sk_test" in data["masked_key"]  # Masked key should show prefix
    
    def test_stripe_config_access_denied_wrong_gym(self, gym_admin_token):
        """Test gym admin cannot access other gym's stripe config"""
        other_gym_id = "66bf9bb2-8a67-4bbd-bbdb-1a762af61429"  # Test Gym
        response = requests.get(
            f"{BASE_URL}/api/gyms/{other_gym_id}/stripe-config",
            headers={"Authorization": f"Bearer {gym_admin_token}"}
        )
        assert response.status_code == 403


class TestGymHasPayments:
    """Test GET /api/gyms/{gym_id}/has-payments endpoint"""
    
    def test_gym_has_payments_public(self):
        """Test has-payments is a public endpoint"""
        response = requests.get(f"{BASE_URL}/api/gyms/{GYM_ID}/has-payments")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "has_payments" in data
        assert "currency" in data
        assert isinstance(data["has_payments"], bool)
    
    def test_gym_has_payments_invalid_gym(self):
        """Test has-payments with invalid gym returns has_payments: false"""
        response = requests.get(f"{BASE_URL}/api/gyms/invalid-gym-id/has-payments")
        assert response.status_code == 200
        data = response.json()
        assert data["has_payments"] == False


class TestPaymentHistory:
    """Test GET /api/payments/history endpoint"""
    
    def test_payment_history_returns_list(self, gym_admin_token):
        """Test payment history returns transaction list"""
        response = requests.get(
            f"{BASE_URL}/api/payments/history",
            headers={"Authorization": f"Bearer {gym_admin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list)
    
    def test_payment_history_requires_auth(self):
        """Test payment history requires authentication"""
        response = requests.get(f"{BASE_URL}/api/payments/history")
        assert response.status_code in [401, 403]


class TestDashboardStats:
    """Test dashboard stats endpoint"""
    
    def test_dashboard_stats(self, gym_admin_token):
        """Test dashboard stats returns comprehensive data"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers={"Authorization": f"Bearer {gym_admin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify key stats are present
        assert "total_members" in data
        assert "active_members" in data
        assert "today_accesses" in data
        assert "week_accesses" in data
        assert "month_accesses" in data
        assert "active_memberships" in data


class TestAccessStats:
    """Test general access stats endpoint"""
    
    def test_access_stats(self, gym_admin_token):
        """Test access stats returns summary data"""
        response = requests.get(
            f"{BASE_URL}/api/access/stats",
            headers={"Authorization": f"Bearer {gym_admin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "today_accesses" in data
        assert "week_accesses" in data
        assert "month_accesses" in data
        assert "active_members" in data
        assert "active_memberships" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
