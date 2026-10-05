"""Backend tests for iteration 34 - category/accounting/open_turnstile/member_me features."""
import os
import pytest
import requests
import uuid

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")
# Prefer local backend for speed/stability during this run
LOCAL = "http://localhost:8001"

SUPER_ADMIN = {"email": "admin@gymaccess.com", "password": "admin123"}
TEST_MEMBER_CODE = "RMB8S5"


@pytest.fixture(scope="session")
def super_token():
    r = requests.post(f"{LOCAL}/api/auth/admin/login", json=SUPER_ADMIN, timeout=30)
    assert r.status_code == 200, f"super admin login failed: {r.status_code} {r.text}"
    return r.json()["token"]


@pytest.fixture(scope="session")
def super_headers(super_token):
    return {"Authorization": f"Bearer {super_token}"}


@pytest.fixture(scope="session")
def test_gym(super_headers):
    """Pick any existing gym or create a new one for tests."""
    r = requests.get(f"{LOCAL}/api/gyms", headers=super_headers, timeout=30)
    assert r.status_code == 200, r.text
    gyms = r.json()
    if gyms:
        return gyms[0]
    # create
    payload = {"name": f"TEST_Gym_{uuid.uuid4().hex[:6]}", "address": "Test"}
    r = requests.post(f"{LOCAL}/api/gyms", json=payload, headers=super_headers, timeout=30)
    assert r.status_code in (200, 201), r.text
    return r.json()


# ------------------ PLAN CATEGORY ------------------
class TestPlanCategory:
    def test_create_plan_with_category(self, super_headers, test_gym):
        payload = {
            "gym_id": test_gym["id"],
            "name": f"TEST_Plan_{uuid.uuid4().hex[:6]}",
            "price": 50.0,
            "duration_days": 30,
            "access_type": "unlimited",
            "category": "Kickboxing",
        }
        r = requests.post(f"{LOCAL}/api/plans", json=payload, headers=super_headers, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["category"] == "Kickboxing"
        assert "id" in data
        pytest.plan_id = data["id"]
        pytest.plan_gym_id = test_gym["id"]

    def test_get_plans_returns_category(self, super_headers):
        r = requests.get(f"{LOCAL}/api/plans?gym_id={pytest.plan_gym_id}", headers=super_headers, timeout=30)
        assert r.status_code == 200
        plans = r.json()
        found = next((p for p in plans if p["id"] == pytest.plan_id), None)
        assert found is not None
        assert found.get("category") == "Kickboxing"

    def test_update_plan_category(self, super_headers):
        r = requests.put(
            f"{LOCAL}/api/plans/{pytest.plan_id}",
            json={"category": "Boxeo"},
            headers=super_headers, timeout=30,
        )
        assert r.status_code == 200, r.text
        assert r.json().get("category") == "Boxeo"


# ------------------ ACCOUNTING REPORT ------------------
class TestAccountingReport:
    def test_report_has_category_fields(self, super_headers, test_gym):
        r = requests.get(
            f"{LOCAL}/api/accounting/report?gym_id={test_gym['id']}",
            headers=super_headers, timeout=60,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert "category_breakdown" in data
        assert "available_categories" in data
        assert isinstance(data["category_breakdown"], list)
        assert isinstance(data["available_categories"], list)
        # each breakdown row has correct keys
        for row in data["category_breakdown"]:
            assert set(row.keys()) >= {"category", "count", "amount"}

    def test_report_with_category_filter(self, super_headers, test_gym):
        r = requests.get(
            f"{LOCAL}/api/accounting/report?gym_id={test_gym['id']}&category=Boxeo",
            headers=super_headers, timeout=60,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        # Every transaction returned should have category Boxeo (if any)
        for tx in data.get("transactions", []):
            assert tx.get("category") == "Boxeo", f"tx category mismatch: {tx.get('category')}"


# ------------------ ACCOUNTING EXCEL ------------------
class TestAccountingExcel:
    def test_excel_export(self, super_headers, test_gym):
        r = requests.get(
            f"{LOCAL}/api/accounting/excel?gym_id={test_gym['id']}",
            headers=super_headers, timeout=60,
        )
        assert r.status_code == 200, r.text[:500]
        ct = r.headers.get("content-type", "")
        assert "openxml" in ct or "spreadsheet" in ct, f"unexpected content-type: {ct}"
        # xlsx is a zip -> starts with PK
        assert r.content[:2] == b"PK", "not a valid xlsx (missing PK header)"
        assert len(r.content) > 500

    def test_excel_with_category_filter(self, super_headers, test_gym):
        r = requests.get(
            f"{LOCAL}/api/accounting/excel?gym_id={test_gym['id']}&category=Kickboxing",
            headers=super_headers, timeout=60,
        )
        assert r.status_code == 200, r.text[:500]
        assert r.content[:2] == b"PK"


# ------------------ OPEN TURNSTILE (gym_admin) ------------------
class TestOpenTurnstile:
    @pytest.fixture(scope="class")
    def gym_admin(self, super_headers, test_gym):
        email = f"TEST_gymadmin_{uuid.uuid4().hex[:6]}@example.com"
        payload = {
            "email": email,
            "password": "testpass123",
            "name": "Test Gym Admin",
            "role": "gym_admin",
            "gym_id": test_gym["id"],
        }
        r = requests.post(f"{LOCAL}/api/auth/admin/register", json=payload, headers=super_headers, timeout=30)
        assert r.status_code in (200, 201), r.text
        # login
        r2 = requests.post(f"{LOCAL}/api/auth/admin/login", json={"email": email, "password": "testpass123"}, timeout=30)
        assert r2.status_code == 200, r2.text
        return {"token": r2.json()["token"], "email": email, "gym_id": test_gym["id"]}

    @pytest.fixture(scope="class")
    def test_device(self, super_headers, test_gym):
        # try to find an existing device for this gym
        r = requests.get(f"{LOCAL}/api/devices/status", headers=super_headers, timeout=30)
        if r.status_code == 200:
            for d in r.json():
                if d.get("gym_id") == test_gym["id"]:
                    return d["id"]
        # Otherwise create one via direct insert through a devices endpoint if available
        # Try POST /api/devices
        payload = {"name": f"TEST_Device_{uuid.uuid4().hex[:6]}", "gym_id": test_gym["id"]}
        r = requests.post(f"{LOCAL}/api/devices", json=payload, headers=super_headers, timeout=30)
        if r.status_code in (200, 201):
            return r.json().get("id")
        pytest.skip("No device available and cannot create one")

    def test_gym_admin_can_open_turnstile(self, gym_admin, test_device):
        headers = {"Authorization": f"Bearer {gym_admin['token']}"}
        r = requests.post(
            f"{LOCAL}/api/devices/{test_device}/command",
            json={"command": "open_turnstile"},
            headers=headers, timeout=30,
        )
        assert r.status_code == 200, f"open_turnstile failed as gym_admin: {r.status_code} {r.text}"
        body = r.json()
        assert body.get("command", {}).get("command") == "open_turnstile"

    def test_gym_admin_cannot_reboot(self, gym_admin, test_device):
        headers = {"Authorization": f"Bearer {gym_admin['token']}"}
        r = requests.post(
            f"{LOCAL}/api/devices/{test_device}/command",
            json={"command": "reboot"},
            headers=headers, timeout=30,
        )
        assert r.status_code == 403, f"gym_admin should NOT reboot. got {r.status_code}: {r.text}"

    def test_super_admin_can_reboot(self, super_headers, test_device):
        r = requests.post(
            f"{LOCAL}/api/devices/{test_device}/command",
            json={"command": "reboot"},
            headers=super_headers, timeout=30,
        )
        assert r.status_code == 200, r.text


# ------------------ MEMBER /me TOKEN REFRESH ------------------
class TestMemberMeRefresh:
    def test_member_login_and_me_returns_fresh_token(self):
        # member login via code
        r = requests.post(f"{LOCAL}/api/auth/member/login?code={TEST_MEMBER_CODE}", timeout=30)
        assert r.status_code == 200, r.text
        token = r.json().get("token")
        assert token
        # call /me
        r2 = requests.get(
            f"{LOCAL}/api/auth/member/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        assert r2.status_code == 200, r2.text
        data = r2.json()
        assert "token" in data, "member /me must return token field for silent refresh"
        assert isinstance(data["token"], str) and len(data["token"]) > 20
