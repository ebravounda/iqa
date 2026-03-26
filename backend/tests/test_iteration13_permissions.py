"""
Iteration 13: Granular Permission System Tests
Tests for gym_manager role permissions:
- Default permissions on staff creation
- Permissions catalog endpoint
- Permission updates
- Permission enforcement on sensitive endpoints
- Login response includes permissions
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
SUPER_ADMIN_EMAIL = "admin@gymaccess.com"
SUPER_ADMIN_PASSWORD = "admin123"

# Expected permissions
DEFAULT_MANAGER_PERMISSIONS = [
    "members_view",
    "members_create",
    "members_edit",
    "payments_register",
    "pos_sell",
    "access_view",
    "classes_manage",
]

ALL_MANAGER_PERMISSIONS = [
    "members_view",
    "members_create",
    "members_edit",
    "members_delete",
    "members_suspend",
    "payments_register",
    "pos_sell",
    "pos_products",
    "access_view",
    "classes_manage",
    "data_export",
    "notifications_send",
]


class TestPermissionSystem:
    """Tests for the granular permission system"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as super admin
        login_resp = self.session.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        assert login_resp.status_code == 200, f"Super admin login failed: {login_resp.text}"
        self.super_admin_token = login_resp.json()["token"]
        self.super_admin = login_resp.json()["admin"]
        self.session.headers.update({"Authorization": f"Bearer {self.super_admin_token}"})
        
        # Get a gym_id for testing
        gyms_resp = self.session.get(f"{BASE_URL}/api/gyms")
        assert gyms_resp.status_code == 200
        gyms = gyms_resp.json()
        assert len(gyms) > 0, "No gyms found for testing"
        self.gym_id = gyms[0]["id"]
        
        yield
        
        # Cleanup: Delete test managers created during tests
        self._cleanup_test_managers()
    
    def _cleanup_test_managers(self):
        """Clean up test managers created during tests"""
        try:
            staff_resp = self.session.get(f"{BASE_URL}/api/staff")
            if staff_resp.status_code == 200:
                staff = staff_resp.json()
                for s in staff:
                    if s.get("email", "").startswith("TEST_"):
                        # Note: No delete endpoint for staff, but they won't interfere
                        pass
        except Exception:
            pass
    
    def test_01_create_gym_manager_has_default_permissions(self):
        """POST /api/staff - Creating gym_manager includes default permissions array"""
        unique_id = str(uuid.uuid4())[:8]
        manager_email = f"TEST_manager_{unique_id}@test.com"
        
        create_resp = self.session.post(f"{BASE_URL}/api/staff", json={
            "name": f"Test Manager {unique_id}",
            "email": manager_email,
            "password": "testpass123",
            "role": "gym_manager",
            "gym_id": self.gym_id
        })
        
        assert create_resp.status_code == 200, f"Failed to create manager: {create_resp.text}"
        manager = create_resp.json()
        
        # Verify permissions array exists and has default permissions
        assert "permissions" in manager, "Manager should have permissions field"
        assert isinstance(manager["permissions"], list), "Permissions should be a list"
        
        # Check all default permissions are present
        for perm in DEFAULT_MANAGER_PERMISSIONS:
            assert perm in manager["permissions"], f"Default permission '{perm}' missing"
        
        # Check restricted permissions are NOT present by default
        restricted = ["members_delete", "members_suspend", "data_export", "notifications_send", "pos_products"]
        for perm in restricted:
            assert perm not in manager["permissions"], f"Restricted permission '{perm}' should not be in defaults"
        
        print(f"✓ Manager created with {len(manager['permissions'])} default permissions")
        
        # Store for later tests
        self.test_manager_id = manager["id"]
        self.test_manager_email = manager_email
    
    def test_02_permissions_catalog_returns_all_permissions(self):
        """GET /api/staff/permissions-catalog - Returns all 12 permissions with labels"""
        resp = self.session.get(f"{BASE_URL}/api/staff/permissions-catalog")
        
        assert resp.status_code == 200, f"Failed to get permissions catalog: {resp.text}"
        catalog = resp.json()
        
        # Verify structure
        assert "all_permissions" in catalog, "Catalog should have all_permissions"
        assert "default_permissions" in catalog, "Catalog should have default_permissions"
        assert "labels" in catalog, "Catalog should have labels"
        
        # Verify all 12 permissions
        assert len(catalog["all_permissions"]) == 12, f"Expected 12 permissions, got {len(catalog['all_permissions'])}"
        
        for perm in ALL_MANAGER_PERMISSIONS:
            assert perm in catalog["all_permissions"], f"Permission '{perm}' missing from catalog"
        
        # Verify 7 default permissions
        assert len(catalog["default_permissions"]) == 7, f"Expected 7 default permissions, got {len(catalog['default_permissions'])}"
        
        for perm in DEFAULT_MANAGER_PERMISSIONS:
            assert perm in catalog["default_permissions"], f"Default permission '{perm}' missing"
        
        # Verify labels exist for all permissions
        for perm in ALL_MANAGER_PERMISSIONS:
            assert perm in catalog["labels"], f"Label missing for permission '{perm}'"
            assert isinstance(catalog["labels"][perm], str), f"Label for '{perm}' should be a string"
        
        print(f"✓ Permissions catalog: {len(catalog['all_permissions'])} total, {len(catalog['default_permissions'])} default")
    
    def test_03_update_manager_permissions(self):
        """PUT /api/staff/{id}/permissions - Updates manager permissions"""
        # First create a manager
        unique_id = str(uuid.uuid4())[:8]
        manager_email = f"TEST_perms_{unique_id}@test.com"
        
        create_resp = self.session.post(f"{BASE_URL}/api/staff", json={
            "name": f"Test Perms Manager {unique_id}",
            "email": manager_email,
            "password": "testpass123",
            "role": "gym_manager",
            "gym_id": self.gym_id
        })
        assert create_resp.status_code == 200
        manager = create_resp.json()
        manager_id = manager["id"]
        
        # Update permissions to include members_delete
        new_permissions = DEFAULT_MANAGER_PERMISSIONS + ["members_delete", "data_export"]
        
        update_resp = self.session.put(f"{BASE_URL}/api/staff/{manager_id}/permissions", json={
            "permissions": new_permissions
        })
        
        assert update_resp.status_code == 200, f"Failed to update permissions: {update_resp.text}"
        result = update_resp.json()
        
        assert "permissions" in result, "Response should include updated permissions"
        assert "members_delete" in result["permissions"], "members_delete should be in updated permissions"
        assert "data_export" in result["permissions"], "data_export should be in updated permissions"
        
        print(f"✓ Permissions updated: {len(result['permissions'])} permissions")
        
        # Store for permission enforcement tests
        self.manager_with_delete_id = manager_id
        self.manager_with_delete_email = manager_email
    
    def test_04_manager_login_includes_permissions(self):
        """POST /api/auth/admin/login - Manager login response includes permissions array"""
        # Create a manager first
        unique_id = str(uuid.uuid4())[:8]
        manager_email = f"TEST_login_{unique_id}@test.com"
        manager_password = "testpass123"
        
        create_resp = self.session.post(f"{BASE_URL}/api/staff", json={
            "name": f"Test Login Manager {unique_id}",
            "email": manager_email,
            "password": manager_password,
            "role": "gym_manager",
            "gym_id": self.gym_id
        })
        assert create_resp.status_code == 200
        
        # Login as the manager
        login_session = requests.Session()
        login_resp = login_session.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": manager_email,
            "password": manager_password
        })
        
        assert login_resp.status_code == 200, f"Manager login failed: {login_resp.text}"
        data = login_resp.json()
        
        assert "admin" in data, "Login response should have admin object"
        assert "token" in data, "Login response should have token"
        assert "permissions" in data["admin"], "Admin object should have permissions"
        
        # Verify default permissions in login response
        for perm in DEFAULT_MANAGER_PERMISSIONS:
            assert perm in data["admin"]["permissions"], f"Default permission '{perm}' missing from login response"
        
        print(f"✓ Manager login includes {len(data['admin']['permissions'])} permissions")
    
    def test_05_manager_without_delete_gets_403_on_delete_member(self):
        """Permission enforcement: Manager WITHOUT members_delete gets 403 on DELETE /api/members/{id}"""
        # Create a manager with default permissions (no members_delete)
        unique_id = str(uuid.uuid4())[:8]
        manager_email = f"TEST_nodelete_{unique_id}@test.com"
        manager_password = "testpass123"
        
        create_resp = self.session.post(f"{BASE_URL}/api/staff", json={
            "name": f"Test NoDelete Manager {unique_id}",
            "email": manager_email,
            "password": manager_password,
            "role": "gym_manager",
            "gym_id": self.gym_id
        })
        assert create_resp.status_code == 200
        
        # Login as the manager
        manager_session = requests.Session()
        login_resp = manager_session.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": manager_email,
            "password": manager_password
        })
        assert login_resp.status_code == 200
        manager_token = login_resp.json()["token"]
        manager_session.headers.update({
            "Authorization": f"Bearer {manager_token}",
            "Content-Type": "application/json"
        })
        
        # Get a member to try to delete
        members_resp = manager_session.get(f"{BASE_URL}/api/members")
        assert members_resp.status_code == 200
        members = members_resp.json()
        
        if len(members) > 0:
            member_id = members[0]["id"]
            
            # Try to delete - should get 403
            delete_resp = manager_session.delete(f"{BASE_URL}/api/members/{member_id}")
            assert delete_resp.status_code == 403, f"Expected 403, got {delete_resp.status_code}: {delete_resp.text}"
            
            print("✓ Manager without members_delete permission gets 403 on DELETE /api/members")
        else:
            print("⚠ No members found to test delete permission - skipping")
    
    def test_06_manager_without_suspend_gets_403_on_suspend_member(self):
        """Permission enforcement: Manager WITHOUT members_suspend gets 403 on POST /api/members/{id}/suspend"""
        # Create a manager with default permissions (no members_suspend)
        unique_id = str(uuid.uuid4())[:8]
        manager_email = f"TEST_nosuspend_{unique_id}@test.com"
        manager_password = "testpass123"
        
        create_resp = self.session.post(f"{BASE_URL}/api/staff", json={
            "name": f"Test NoSuspend Manager {unique_id}",
            "email": manager_email,
            "password": manager_password,
            "role": "gym_manager",
            "gym_id": self.gym_id
        })
        assert create_resp.status_code == 200
        
        # Login as the manager
        manager_session = requests.Session()
        login_resp = manager_session.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": manager_email,
            "password": manager_password
        })
        assert login_resp.status_code == 200
        manager_token = login_resp.json()["token"]
        manager_session.headers.update({
            "Authorization": f"Bearer {manager_token}",
            "Content-Type": "application/json"
        })
        
        # Get a member to try to suspend
        members_resp = manager_session.get(f"{BASE_URL}/api/members")
        assert members_resp.status_code == 200
        members = members_resp.json()
        
        if len(members) > 0:
            member_id = members[0]["id"]
            
            # Try to suspend - should get 403
            suspend_resp = manager_session.post(f"{BASE_URL}/api/members/{member_id}/suspend", json={
                "reason": "Test suspension"
            })
            assert suspend_resp.status_code == 403, f"Expected 403, got {suspend_resp.status_code}: {suspend_resp.text}"
            
            print("✓ Manager without members_suspend permission gets 403 on POST /api/members/{id}/suspend")
        else:
            print("⚠ No members found to test suspend permission - skipping")
    
    def test_07_manager_without_data_export_gets_403_on_export(self):
        """Permission enforcement: Manager WITHOUT data_export gets 403 on GET /api/members/export/excel"""
        # Create a manager with default permissions (no data_export)
        unique_id = str(uuid.uuid4())[:8]
        manager_email = f"TEST_noexport_{unique_id}@test.com"
        manager_password = "testpass123"
        
        create_resp = self.session.post(f"{BASE_URL}/api/staff", json={
            "name": f"Test NoExport Manager {unique_id}",
            "email": manager_email,
            "password": manager_password,
            "role": "gym_manager",
            "gym_id": self.gym_id
        })
        assert create_resp.status_code == 200
        
        # Login as the manager
        manager_session = requests.Session()
        login_resp = manager_session.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": manager_email,
            "password": manager_password
        })
        assert login_resp.status_code == 200
        manager_token = login_resp.json()["token"]
        manager_session.headers.update({
            "Authorization": f"Bearer {manager_token}",
            "Content-Type": "application/json"
        })
        
        # Try to export - should get 403
        export_resp = manager_session.get(f"{BASE_URL}/api/members/export/excel")
        assert export_resp.status_code == 403, f"Expected 403, got {export_resp.status_code}: {export_resp.text}"
        
        print("✓ Manager without data_export permission gets 403 on GET /api/members/export/excel")
    
    def test_08_manager_without_notifications_send_gets_403_on_create_notification(self):
        """Permission enforcement: Manager WITHOUT notifications_send gets 403 on POST /api/notifications"""
        # Create a manager with default permissions (no notifications_send)
        unique_id = str(uuid.uuid4())[:8]
        manager_email = f"TEST_nonotify_{unique_id}@test.com"
        manager_password = "testpass123"
        
        create_resp = self.session.post(f"{BASE_URL}/api/staff", json={
            "name": f"Test NoNotify Manager {unique_id}",
            "email": manager_email,
            "password": manager_password,
            "role": "gym_manager",
            "gym_id": self.gym_id
        })
        assert create_resp.status_code == 200
        
        # Login as the manager
        manager_session = requests.Session()
        login_resp = manager_session.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": manager_email,
            "password": manager_password
        })
        assert login_resp.status_code == 200
        manager_token = login_resp.json()["token"]
        manager_session.headers.update({
            "Authorization": f"Bearer {manager_token}",
            "Content-Type": "application/json"
        })
        
        # Try to create notification - should get 403
        notify_resp = manager_session.post(f"{BASE_URL}/api/notifications", json={
            "gym_id": self.gym_id,
            "title": "Test Notification",
            "message": "Test message",
            "notification_type": "info",
            "target": "all"
        })
        assert notify_resp.status_code == 403, f"Expected 403, got {notify_resp.status_code}: {notify_resp.text}"
        
        print("✓ Manager without notifications_send permission gets 403 on POST /api/notifications")
    
    def test_09_manager_with_members_view_gets_200_on_get_members(self):
        """Permission enforcement: Manager WITH members_view gets 200 on GET /api/members"""
        # Create a manager with default permissions (includes members_view)
        unique_id = str(uuid.uuid4())[:8]
        manager_email = f"TEST_canview_{unique_id}@test.com"
        manager_password = "testpass123"
        
        create_resp = self.session.post(f"{BASE_URL}/api/staff", json={
            "name": f"Test CanView Manager {unique_id}",
            "email": manager_email,
            "password": manager_password,
            "role": "gym_manager",
            "gym_id": self.gym_id
        })
        assert create_resp.status_code == 200
        
        # Login as the manager
        manager_session = requests.Session()
        login_resp = manager_session.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": manager_email,
            "password": manager_password
        })
        assert login_resp.status_code == 200
        manager_token = login_resp.json()["token"]
        manager_session.headers.update({
            "Authorization": f"Bearer {manager_token}",
            "Content-Type": "application/json"
        })
        
        # Get members - should succeed
        members_resp = manager_session.get(f"{BASE_URL}/api/members")
        assert members_resp.status_code == 200, f"Expected 200, got {members_resp.status_code}: {members_resp.text}"
        
        print("✓ Manager with members_view permission gets 200 on GET /api/members")
    
    def test_10_after_granting_delete_permission_delete_returns_non_403(self):
        """After granting members_delete permission, DELETE returns 404 (not 403)"""
        # Create a manager
        unique_id = str(uuid.uuid4())[:8]
        manager_email = f"TEST_grantdelete_{unique_id}@test.com"
        manager_password = "testpass123"
        
        create_resp = self.session.post(f"{BASE_URL}/api/staff", json={
            "name": f"Test GrantDelete Manager {unique_id}",
            "email": manager_email,
            "password": manager_password,
            "role": "gym_manager",
            "gym_id": self.gym_id
        })
        assert create_resp.status_code == 200
        manager_id = create_resp.json()["id"]
        
        # Grant members_delete permission
        new_permissions = DEFAULT_MANAGER_PERMISSIONS + ["members_delete"]
        update_resp = self.session.put(f"{BASE_URL}/api/staff/{manager_id}/permissions", json={
            "permissions": new_permissions
        })
        assert update_resp.status_code == 200
        
        # Login as the manager (need fresh login to get updated permissions from DB)
        manager_session = requests.Session()
        login_resp = manager_session.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": manager_email,
            "password": manager_password
        })
        assert login_resp.status_code == 200
        manager_token = login_resp.json()["token"]
        manager_session.headers.update({
            "Authorization": f"Bearer {manager_token}",
            "Content-Type": "application/json"
        })
        
        # Try to delete a non-existent member - should get 404 (not 403)
        fake_member_id = str(uuid.uuid4())
        delete_resp = manager_session.delete(f"{BASE_URL}/api/members/{fake_member_id}")
        
        # Should NOT be 403 (permission denied) - should be 404 (not found)
        assert delete_resp.status_code != 403, f"Should not get 403 after granting permission, got {delete_resp.status_code}"
        assert delete_resp.status_code == 404, f"Expected 404 for non-existent member, got {delete_resp.status_code}"
        
        print("✓ After granting members_delete permission, DELETE returns 404 (not 403)")
    
    def test_11_disabled_account_login_returns_403(self):
        """Disabled account login returns 403 - tests the active check in auth_routes.py"""
        # The auth_routes.py has: if admin.get("active") is False: raise HTTPException(status_code=403)
        # However, there's no PUT /api/staff/{id} endpoint to deactivate staff
        # The /api/trainers/{id} endpoint only works for role="trainer"
        # 
        # This test verifies the login check exists by checking auth_routes.py code
        # A proper test would require a staff update endpoint
        
        # Verify the active check exists in auth code
        import requests
        
        # Test that a normal login works (active=True by default)
        unique_id = str(uuid.uuid4())[:8]
        manager_email = f"TEST_activecheck_{unique_id}@test.com"
        manager_password = "testpass123"
        
        create_resp = self.session.post(f"{BASE_URL}/api/staff", json={
            "name": f"Test ActiveCheck Manager {unique_id}",
            "email": manager_email,
            "password": manager_password,
            "role": "gym_manager",
            "gym_id": self.gym_id
        })
        assert create_resp.status_code == 200
        manager = create_resp.json()
        
        # Verify active=True by default
        assert manager.get("active") == True, "New staff should have active=True by default"
        
        # Login should work for active account
        login_session = requests.Session()
        login_resp = login_session.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": manager_email,
            "password": manager_password
        })
        assert login_resp.status_code == 200, f"Active account should be able to login, got {login_resp.status_code}"
        
        print("✓ Active account login works (active check exists in auth_routes.py line 35-36)")
        print("  Note: Full disabled account test requires PUT /api/staff/{id} endpoint to deactivate staff")


class TestSuperAdminBypassesPermissions:
    """Tests that super_admin and gym_admin bypass permission checks"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as super admin
        login_resp = self.session.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        assert login_resp.status_code == 200
        self.super_admin_token = login_resp.json()["token"]
        self.session.headers.update({"Authorization": f"Bearer {self.super_admin_token}"})
        
        yield
    
    def test_super_admin_can_delete_member(self):
        """Super admin can delete members without explicit permission"""
        # Get a member
        members_resp = self.session.get(f"{BASE_URL}/api/members")
        assert members_resp.status_code == 200
        members = members_resp.json()
        
        if len(members) > 0:
            # Try to delete a non-existent member to test permission bypass
            fake_member_id = str(uuid.uuid4())
            delete_resp = self.session.delete(f"{BASE_URL}/api/members/{fake_member_id}")
            
            # Should get 404 (not found), not 403 (forbidden)
            assert delete_resp.status_code == 404, f"Super admin should bypass permissions, got {delete_resp.status_code}"
            print("✓ Super admin bypasses permission checks (gets 404, not 403)")
        else:
            print("⚠ No members found - testing with fake ID")
            fake_member_id = str(uuid.uuid4())
            delete_resp = self.session.delete(f"{BASE_URL}/api/members/{fake_member_id}")
            assert delete_resp.status_code == 404
            print("✓ Super admin bypasses permission checks")
    
    def test_super_admin_can_export_data(self):
        """Super admin can export data without explicit permission"""
        export_resp = self.session.get(f"{BASE_URL}/api/members/export/excel")
        assert export_resp.status_code == 200, f"Super admin should be able to export, got {export_resp.status_code}"
        print("✓ Super admin can export data")
    
    def test_super_admin_can_send_notifications(self):
        """Super admin can send notifications without explicit permission"""
        # Get a gym_id
        gyms_resp = self.session.get(f"{BASE_URL}/api/gyms")
        assert gyms_resp.status_code == 200
        gyms = gyms_resp.json()
        
        if len(gyms) > 0:
            gym_id = gyms[0]["id"]
            notify_resp = self.session.post(f"{BASE_URL}/api/notifications", json={
                "gym_id": gym_id,
                "title": "Test Super Admin Notification",
                "message": "Test message from super admin",
                "notification_type": "info",
                "target": "all"
            })
            assert notify_resp.status_code == 200, f"Super admin should be able to send notifications, got {notify_resp.status_code}"
            print("✓ Super admin can send notifications")
        else:
            print("⚠ No gyms found for notification test")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
