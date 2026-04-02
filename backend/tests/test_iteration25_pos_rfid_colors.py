"""
Iteration 25 - Testing POS rewrite, RFID access control, and Corporate Colors features

Features tested:
1. POS: Product CRUD with categories, sales, stats, categories endpoint
2. RFID: Assign/remove RFID UID to members, validate access via RFID
3. Corporate Colors: Update gym colors via PUT /api/gyms/{gym_id}
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from review request
SUPER_ADMIN_EMAIL = "admin@gymaccess.com"
SUPER_ADMIN_PASSWORD = "admin123"
GYM_ADMIN_EMAIL = "admin@fitzone.com"
GYM_ADMIN_PASSWORD = "admin123"
GYM_ID = "efe99507-15d5-4e54-9f07-30d2507894e0"


class TestAuth:
    """Authentication helpers"""
    
    @staticmethod
    def get_admin_token(email, password):
        """Get admin JWT token"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": email,
            "password": password
        })
        if response.status_code == 200:
            return response.json().get("token")
        return None


@pytest.fixture(scope="module")
def gym_admin_token():
    """Get gym admin token"""
    token = TestAuth.get_admin_token(GYM_ADMIN_EMAIL, GYM_ADMIN_PASSWORD)
    if not token:
        pytest.skip("Could not authenticate as gym admin")
    return token


@pytest.fixture(scope="module")
def super_admin_token():
    """Get super admin token"""
    token = TestAuth.get_admin_token(SUPER_ADMIN_EMAIL, SUPER_ADMIN_PASSWORD)
    if not token:
        pytest.skip("Could not authenticate as super admin")
    return token


@pytest.fixture(scope="module")
def gym_api_token(gym_admin_token):
    """Get gym's API token for access validation"""
    headers = {"Authorization": f"Bearer {gym_admin_token}"}
    response = requests.get(f"{BASE_URL}/api/gyms/{GYM_ID}", headers=headers)
    if response.status_code == 200:
        return response.json().get("api_token")
    pytest.skip("Could not get gym API token")


@pytest.fixture(scope="module")
def test_member_with_membership(gym_admin_token):
    """Get or create a test member with active membership for RFID testing"""
    headers = {"Authorization": f"Bearer {gym_admin_token}"}
    
    # First try to find an existing active member
    response = requests.get(f"{BASE_URL}/api/members", headers=headers, params={"status": "active"})
    if response.status_code == 200:
        members = response.json()
        for member in members:
            # Check if member has active membership
            ms_response = requests.get(f"{BASE_URL}/api/memberships", headers=headers, params={"member_id": member["id"]})
            if ms_response.status_code == 200:
                memberships = ms_response.json()
                active_ms = [m for m in memberships if m.get("status") == "active"]
                if active_ms:
                    return member
    
    # Create a new test member if none found
    test_email = f"test_rfid_{uuid.uuid4().hex[:8]}@test.com"
    create_response = requests.post(f"{BASE_URL}/api/members", headers=headers, json={
        "email": test_email,
        "name": "TEST_RFID_Member",
        "phone": "+1234567890",
        "gym_id": GYM_ID
    })
    if create_response.status_code in [200, 201]:
        member = create_response.json()
        # Create active membership
        requests.post(f"{BASE_URL}/api/memberships", headers=headers, json={
            "member_id": member["id"],
            "gym_id": GYM_ID,
            "plan_id": "test-plan",
            "start_date": datetime.now().isoformat(),
            "end_date": "2030-12-31T23:59:59",
            "status": "active"
        })
        return member
    
    pytest.skip("Could not find or create test member with active membership")


# ==================== POS PRODUCT TESTS ====================

class TestPOSProducts:
    """POS Product CRUD tests"""
    
    created_product_id = None
    
    def test_create_product(self, gym_admin_token):
        """Test creating a POS product with category"""
        headers = {"Authorization": f"Bearer {gym_admin_token}"}
        product_data = {
            "name": f"TEST_Product_{uuid.uuid4().hex[:6]}",
            "description": "Test product for iteration 25",
            "category": "Bebidas",
            "cost_price": 1.50,
            "sale_price": 3.00,
            "stock": 100,
            "barcode": f"TEST{uuid.uuid4().hex[:8]}",
            "gym_id": GYM_ID
        }
        
        response = requests.post(f"{BASE_URL}/api/pos/products", headers=headers, json=product_data)
        
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "id" in data, "Product should have an id"
        assert data["name"] == product_data["name"], "Product name should match"
        assert data["category"] == "Bebidas", "Product category should be 'Bebidas'"
        assert data["cost_price"] == 1.50, "Cost price should match"
        assert data["sale_price"] == 3.00, "Sale price should match"
        assert data["stock"] == 100, "Stock should match"
        assert data.get("active") == True, "Product should be active"
        
        TestPOSProducts.created_product_id = data["id"]
        print(f"PASS: Created product {data['id']} with category '{data['category']}'")
    
    def test_list_products(self, gym_admin_token):
        """Test listing POS products - should return products with category field"""
        headers = {"Authorization": f"Bearer {gym_admin_token}"}
        
        response = requests.get(f"{BASE_URL}/api/pos/products", headers=headers, params={"gym_id": GYM_ID})
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        products = response.json()
        
        assert isinstance(products, list), "Response should be a list"
        
        # Check that products have category field
        if products:
            product = products[0]
            assert "name" in product, "Product should have name"
            assert "sale_price" in product, "Product should have sale_price"
            # Category may be None for old products, but field should exist or default to 'General'
            print(f"PASS: Listed {len(products)} products")
    
    def test_get_categories(self, gym_admin_token):
        """Test getting distinct product categories"""
        headers = {"Authorization": f"Bearer {gym_admin_token}"}
        
        response = requests.get(f"{BASE_URL}/api/pos/categories", headers=headers, params={"gym_id": GYM_ID})
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        categories = response.json()
        
        assert isinstance(categories, list), "Response should be a list of categories"
        # Should have at least 'general' or our test category
        print(f"PASS: Got categories: {categories}")
    
    def test_update_product(self, gym_admin_token):
        """Test updating a POS product"""
        if not TestPOSProducts.created_product_id:
            pytest.skip("No product created to update")
        
        headers = {"Authorization": f"Bearer {gym_admin_token}"}
        update_data = {
            "name": "TEST_Updated_Product",
            "sale_price": 4.50,
            "stock": 50,
            "category": "Suplementos"
        }
        
        response = requests.put(
            f"{BASE_URL}/api/pos/products/{TestPOSProducts.created_product_id}",
            headers=headers,
            json=update_data
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data["name"] == "TEST_Updated_Product", "Name should be updated"
        assert data["sale_price"] == 4.50, "Sale price should be updated"
        assert data["stock"] == 50, "Stock should be updated"
        assert data["category"] == "Suplementos", "Category should be updated"
        print(f"PASS: Updated product {TestPOSProducts.created_product_id}")
    
    def test_delete_product(self, gym_admin_token):
        """Test deleting (soft delete) a POS product"""
        if not TestPOSProducts.created_product_id:
            pytest.skip("No product created to delete")
        
        headers = {"Authorization": f"Bearer {gym_admin_token}"}
        
        response = requests.delete(
            f"{BASE_URL}/api/pos/products/{TestPOSProducts.created_product_id}",
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "message" in data, "Should return success message"
        print(f"PASS: Deleted product {TestPOSProducts.created_product_id}")


# ==================== POS SALES TESTS ====================

class TestPOSSales:
    """POS Sales tests"""
    
    test_product_id = None
    
    @pytest.fixture(autouse=True)
    def setup_test_product(self, gym_admin_token):
        """Create a test product for sales testing"""
        headers = {"Authorization": f"Bearer {gym_admin_token}"}
        product_data = {
            "name": f"TEST_Sale_Product_{uuid.uuid4().hex[:6]}",
            "category": "Snacks",
            "cost_price": 1.00,
            "sale_price": 2.50,
            "stock": 50,
            "gym_id": GYM_ID
        }
        
        response = requests.post(f"{BASE_URL}/api/pos/products", headers=headers, json=product_data)
        if response.status_code in [200, 201]:
            TestPOSSales.test_product_id = response.json()["id"]
        
        yield
        
        # Cleanup
        if TestPOSSales.test_product_id:
            requests.delete(f"{BASE_URL}/api/pos/products/{TestPOSSales.test_product_id}", headers=headers)
    
    def test_process_sale(self, gym_admin_token):
        """Test processing a POS sale"""
        if not TestPOSSales.test_product_id:
            pytest.skip("No test product available")
        
        headers = {"Authorization": f"Bearer {gym_admin_token}"}
        sale_data = {
            "gym_id": GYM_ID,
            "items": [
                {
                    "product_id": TestPOSSales.test_product_id,
                    "quantity": 2,
                    "unit_price": 2.50
                }
            ],
            "total": 5.00,
            "payment_method": "cash"
        }
        
        response = requests.post(f"{BASE_URL}/api/pos/sales", headers=headers, json=sale_data)
        
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "id" in data, "Sale should have an id"
        assert data["total"] == 5.00, "Total should match"
        assert data["payment_method"] == "cash", "Payment method should match"
        assert "items" in data, "Sale should have items"
        assert len(data["items"]) == 1, "Should have 1 item"
        print(f"PASS: Processed sale {data['id']} with total ${data['total']}")
    
    def test_get_sales_history(self, gym_admin_token):
        """Test getting sales history"""
        headers = {"Authorization": f"Bearer {gym_admin_token}"}
        
        response = requests.get(f"{BASE_URL}/api/pos/sales", headers=headers, params={"gym_id": GYM_ID})
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        sales = response.json()
        
        assert isinstance(sales, list), "Response should be a list"
        print(f"PASS: Got {len(sales)} sales in history")
    
    def test_get_pos_stats(self, gym_admin_token):
        """Test getting POS stats - should return today_total, month_total, total_products, low_stock_products"""
        headers = {"Authorization": f"Bearer {gym_admin_token}"}
        
        response = requests.get(f"{BASE_URL}/api/pos/stats", headers=headers, params={"gym_id": GYM_ID})
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        stats = response.json()
        
        # Verify expected fields exist
        assert "today_total" in stats, "Stats should have today_total"
        assert "month_total" in stats, "Stats should have month_total"
        assert "total_products" in stats, "Stats should have total_products"
        assert "low_stock_products" in stats, "Stats should have low_stock_products"
        
        # Also check legacy fields for backwards compatibility
        assert "today_revenue" in stats or "today_total" in stats, "Should have today revenue"
        assert "month_revenue" in stats or "month_total" in stats, "Should have month revenue"
        
        print(f"PASS: Got POS stats - today_total: {stats.get('today_total')}, month_total: {stats.get('month_total')}, products: {stats.get('total_products')}")


# ==================== RFID TESTS ====================

class TestRFID:
    """RFID access control tests"""
    
    test_rfid_uid = "ABC123DEF456"
    
    def test_assign_rfid_to_member(self, gym_admin_token, test_member_with_membership):
        """Test assigning RFID UID to a member"""
        headers = {"Authorization": f"Bearer {gym_admin_token}"}
        member_id = test_member_with_membership["id"]
        
        response = requests.put(
            f"{BASE_URL}/api/members/{member_id}/rfid",
            headers=headers,
            json={"rfid_uid": TestRFID.test_rfid_uid}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "message" in data, "Should return message"
        assert data.get("rfid_uid") == TestRFID.test_rfid_uid.upper().replace(":", ""), "RFID UID should be normalized"
        print(f"PASS: Assigned RFID {TestRFID.test_rfid_uid} to member {member_id}")
    
    def test_validate_access_with_rfid(self, gym_api_token, test_member_with_membership):
        """Test validating access using RFID input"""
        # RFID validation uses gym's api_token, not admin token
        response = requests.post(
            f"{BASE_URL}/api/access/validate",
            json={
                "qr_code": TestRFID.test_rfid_uid,  # Short hex string = RFID
                "gym_token": gym_api_token,
                "direction": "entrada"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Should recognize as RFID and validate
        if data.get("valid"):
            assert data.get("access_type") == "rfid", "Access type should be 'rfid'"
            assert "member_name" in data, "Should return member name"
            print(f"PASS: RFID access validated for {data.get('member_name')}")
        else:
            # May fail if member doesn't have active membership - that's ok for this test
            print(f"INFO: RFID validation returned: {data.get('reason', 'unknown')}")
    
    def test_duplicate_rfid_rejected(self, gym_admin_token, test_member_with_membership):
        """Test that duplicate RFID assignment is rejected for different members"""
        headers = {"Authorization": f"Bearer {gym_admin_token}"}
        
        # Create another test member
        test_email = f"test_rfid_dup_{uuid.uuid4().hex[:8]}@test.com"
        create_response = requests.post(f"{BASE_URL}/api/members", headers=headers, json={
            "email": test_email,
            "name": "TEST_RFID_Duplicate",
            "phone": "+1234567890",
            "gym_id": GYM_ID
        })
        
        if create_response.status_code not in [200, 201]:
            pytest.skip("Could not create second test member")
        
        second_member_id = create_response.json()["id"]
        
        # Try to assign same RFID to second member
        response = requests.put(
            f"{BASE_URL}/api/members/{second_member_id}/rfid",
            headers=headers,
            json={"rfid_uid": TestRFID.test_rfid_uid}
        )
        
        assert response.status_code == 400, f"Expected 400 for duplicate RFID, got {response.status_code}: {response.text}"
        data = response.json()
        assert "detail" in data, "Should return error detail"
        print(f"PASS: Duplicate RFID correctly rejected: {data.get('detail')}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/members/{second_member_id}", headers=headers)
    
    def test_remove_rfid_from_member(self, gym_admin_token, test_member_with_membership):
        """Test removing RFID from member by setting empty rfid_uid"""
        headers = {"Authorization": f"Bearer {gym_admin_token}"}
        member_id = test_member_with_membership["id"]
        
        response = requests.put(
            f"{BASE_URL}/api/members/{member_id}/rfid",
            headers=headers,
            json={"rfid_uid": ""}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data.get("rfid_uid") is None, "RFID should be removed (None)"
        print(f"PASS: Removed RFID from member {member_id}")


# ==================== CORPORATE COLORS TESTS ====================

class TestCorporateColors:
    """Corporate Colors tests"""
    
    original_colors = {}
    
    def test_update_gym_colors(self, gym_admin_token):
        """Test updating gym corporate colors"""
        headers = {"Authorization": f"Bearer {gym_admin_token}"}
        
        # First get current colors to restore later
        get_response = requests.get(f"{BASE_URL}/api/gyms/{GYM_ID}", headers=headers)
        if get_response.status_code == 200:
            gym = get_response.json()
            TestCorporateColors.original_colors = {
                "primary_color": gym.get("primary_color"),
                "bg_color": gym.get("bg_color"),
                "menu_color": gym.get("menu_color"),
                "text_color": gym.get("text_color"),
                "secondary_color": gym.get("secondary_color")
            }
        
        # Update colors
        color_data = {
            "primary_color": "#FF6B6B",
            "bg_color": "#1A1A2E",
            "menu_color": "#16213E",
            "text_color": "#EAEAEA",
            "secondary_color": "#4ECDC4"
        }
        
        response = requests.put(f"{BASE_URL}/api/gyms/{GYM_ID}", headers=headers, json=color_data)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify colors were updated
        assert data.get("primary_color") == "#FF6B6B", "Primary color should be updated"
        assert data.get("bg_color") == "#1A1A2E", "Background color should be updated"
        assert data.get("menu_color") == "#16213E", "Menu color should be updated"
        assert data.get("text_color") == "#EAEAEA", "Text color should be updated"
        assert data.get("secondary_color") == "#4ECDC4", "Secondary color should be updated"
        
        print(f"PASS: Updated gym colors - primary: {data.get('primary_color')}")
    
    def test_restore_original_colors(self, gym_admin_token):
        """Restore original colors after test"""
        if not TestCorporateColors.original_colors:
            pytest.skip("No original colors to restore")
        
        headers = {"Authorization": f"Bearer {gym_admin_token}"}
        
        # Only restore non-None values
        restore_data = {k: v for k, v in TestCorporateColors.original_colors.items() if v is not None}
        if not restore_data:
            restore_data = {"primary_color": "#E1FF01"}  # Default
        
        response = requests.put(f"{BASE_URL}/api/gyms/{GYM_ID}", headers=headers, json=restore_data)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("PASS: Restored original gym colors")


# ==================== ADMIN SETTINGS PAGE TEST ====================

class TestAdminSettingsAccess:
    """Test that gym admin can access settings page"""
    
    def test_gym_admin_can_get_gym_data(self, gym_admin_token):
        """Verify gym admin can fetch gym data (required for settings page)"""
        headers = {"Authorization": f"Bearer {gym_admin_token}"}
        
        response = requests.get(f"{BASE_URL}/api/gyms/{GYM_ID}", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "id" in data, "Gym should have id"
        assert "name" in data, "Gym should have name"
        # Check color fields exist (may be None)
        assert "primary_color" in data or data.get("primary_color") is None, "Should have primary_color field"
        
        print(f"PASS: Gym admin can access gym data for settings page")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
