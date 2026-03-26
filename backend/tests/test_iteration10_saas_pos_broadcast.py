"""
Iteration 10 Tests: SaaS Plans, POS/TPV, Accounting, Broadcast, MercadoPago
Tests for the refactored backend with modular routes.
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://stripe-gym-payments.preview.emergentagent.com')

# Test credentials
SUPER_ADMIN_EMAIL = "admin@gymaccess.com"
SUPER_ADMIN_PASSWORD = "admin123"

class TestAuthAndHealth:
    """Basic health and authentication tests"""
    
    def test_health_endpoint(self):
        """Test /api/health returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✓ Health endpoint working")
    
    def test_super_admin_login(self):
        """Test super admin login"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["admin"]["role"] == "super_admin"
        print(f"✓ Super admin login successful, role: {data['admin']['role']}")
        return data["token"]


class TestSaaSPlans:
    """Tests for SaaS Plans CRUD operations"""
    
    @pytest.fixture
    def auth_token(self):
        """Get super admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_get_saas_plans_empty_or_existing(self, auth_token):
        """GET /api/saas/plans - returns array (empty or with plans)"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/saas/plans", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/saas/plans returned {len(data)} plans")
    
    def test_create_saas_plan(self, auth_token):
        """POST /api/saas/plans - create a SaaS plan with has_pos=true"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        plan_data = {
            "name": f"TEST_Plan_Pro_{uuid.uuid4().hex[:6]}",
            "max_members": 1000,
            "has_pos": True,
            "has_mercadopago": True,
            "has_iframes": True,
            "has_advanced_accounting": True,
            "price_monthly": 99.99,
            "currency": "EUR",
            "description": "Plan profesional con todas las funciones"
        }
        response = requests.post(f"{BASE_URL}/api/saas/plans", json=plan_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == plan_data["name"]
        assert data["has_pos"] == True
        assert data["max_members"] == 1000
        assert "id" in data
        print(f"✓ Created SaaS plan: {data['name']} (id: {data['id']})")
        return data
    
    def test_get_saas_plans_after_create(self, auth_token):
        """GET /api/saas/plans - returns the created plan"""
        # First create a plan
        headers = {"Authorization": f"Bearer {auth_token}"}
        plan_data = {
            "name": f"TEST_Plan_Basic_{uuid.uuid4().hex[:6]}",
            "max_members": 500,
            "has_pos": False,
            "price_monthly": 49.99,
            "currency": "CLP"
        }
        create_response = requests.post(f"{BASE_URL}/api/saas/plans", json=plan_data, headers=headers)
        assert create_response.status_code == 200
        created_plan = create_response.json()
        
        # Now get all plans
        response = requests.get(f"{BASE_URL}/api/saas/plans", headers=headers)
        assert response.status_code == 200
        plans = response.json()
        assert any(p["id"] == created_plan["id"] for p in plans)
        print(f"✓ GET /api/saas/plans contains created plan")


class TestGymSaaSAssignment:
    """Tests for assigning SaaS plans to gyms"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    @pytest.fixture
    def gym_id(self, auth_token):
        """Get first available gym ID"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/gyms", headers=headers)
        gyms = response.json()
        if gyms:
            return gyms[0]["id"]
        return None
    
    @pytest.fixture
    def saas_plan_id(self, auth_token):
        """Create a SaaS plan and return its ID"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        plan_data = {
            "name": f"TEST_Plan_Assign_{uuid.uuid4().hex[:6]}",
            "max_members": 1000,
            "has_pos": True,
            "has_mercadopago": True,
            "price_monthly": 79.99,
            "currency": "EUR"
        }
        response = requests.post(f"{BASE_URL}/api/saas/plans", json=plan_data, headers=headers)
        return response.json()["id"]
    
    def test_assign_saas_plan_to_gym(self, auth_token, gym_id, saas_plan_id):
        """PUT /api/gyms/{gym_id}/saas-plan - assign SaaS plan to a gym"""
        if not gym_id:
            pytest.skip("No gym available for testing")
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.put(
            f"{BASE_URL}/api/gyms/{gym_id}/saas-plan",
            json={"saas_plan_id": saas_plan_id},
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"✓ Assigned SaaS plan to gym: {data['message']}")
    
    def test_get_gym_saas_features(self, auth_token, gym_id, saas_plan_id):
        """GET /api/gyms/{gym_id}/saas-features - returns features based on plan"""
        if not gym_id:
            pytest.skip("No gym available for testing")
        
        # First assign the plan
        headers = {"Authorization": f"Bearer {auth_token}"}
        requests.put(
            f"{BASE_URL}/api/gyms/{gym_id}/saas-plan",
            json={"saas_plan_id": saas_plan_id},
            headers=headers
        )
        
        # Now get features
        response = requests.get(f"{BASE_URL}/api/gyms/{gym_id}/saas-features", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "has_pos" in data
        assert "has_mercadopago" in data
        assert "max_members" in data
        assert "plan_name" in data
        print(f"✓ GET /api/gyms/{gym_id}/saas-features: has_pos={data['has_pos']}, plan={data['plan_name']}")


class TestPOSProducts:
    """Tests for POS/TPV Products CRUD"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    @pytest.fixture
    def gym_with_pos(self, auth_token):
        """Get or create a gym with POS enabled"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get gyms
        response = requests.get(f"{BASE_URL}/api/gyms", headers=headers)
        gyms = response.json()
        if not gyms:
            pytest.skip("No gyms available")
        
        gym_id = gyms[0]["id"]
        
        # Create a SaaS plan with POS enabled
        plan_data = {
            "name": f"TEST_POS_Plan_{uuid.uuid4().hex[:6]}",
            "max_members": 1000,
            "has_pos": True,
            "price_monthly": 99.99
        }
        plan_response = requests.post(f"{BASE_URL}/api/saas/plans", json=plan_data, headers=headers)
        plan_id = plan_response.json()["id"]
        
        # Assign plan to gym
        requests.put(
            f"{BASE_URL}/api/gyms/{gym_id}/saas-plan",
            json={"saas_plan_id": plan_id},
            headers=headers
        )
        
        return gym_id
    
    def test_create_pos_product(self, auth_token, gym_with_pos):
        """POST /api/pos/products - create a product"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        product_data = {
            "gym_id": gym_with_pos,
            "name": f"TEST_Protein_Bar_{uuid.uuid4().hex[:6]}",
            "description": "Barra de proteina 50g",
            "cost_price": 1.50,
            "sale_price": 3.00,
            "stock": 100,
            "category": "Suplementos",
            "barcode": f"TEST{uuid.uuid4().hex[:8]}"
        }
        response = requests.post(f"{BASE_URL}/api/pos/products", json=product_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == product_data["name"]
        assert data["sale_price"] == 3.00
        assert data["stock"] == 100
        assert "id" in data
        print(f"✓ Created POS product: {data['name']} (id: {data['id']})")
        return data
    
    def test_get_pos_products(self, auth_token, gym_with_pos):
        """GET /api/pos/products - returns products"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # First create a product
        product_data = {
            "gym_id": gym_with_pos,
            "name": f"TEST_Water_{uuid.uuid4().hex[:6]}",
            "sale_price": 1.50,
            "stock": 50
        }
        requests.post(f"{BASE_URL}/api/pos/products", json=product_data, headers=headers)
        
        # Get products
        response = requests.get(f"{BASE_URL}/api/pos/products?gym_id={gym_with_pos}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/pos/products returned {len(data)} products")


class TestPOSSales:
    """Tests for POS/TPV Sales"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    @pytest.fixture
    def gym_with_product(self, auth_token):
        """Get gym with POS and create a product"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get gyms
        response = requests.get(f"{BASE_URL}/api/gyms", headers=headers)
        gyms = response.json()
        if not gyms:
            pytest.skip("No gyms available")
        
        gym_id = gyms[0]["id"]
        
        # Create SaaS plan with POS
        plan_data = {
            "name": f"TEST_Sales_Plan_{uuid.uuid4().hex[:6]}",
            "max_members": 1000,
            "has_pos": True
        }
        plan_response = requests.post(f"{BASE_URL}/api/saas/plans", json=plan_data, headers=headers)
        plan_id = plan_response.json()["id"]
        
        # Assign plan
        requests.put(
            f"{BASE_URL}/api/gyms/{gym_id}/saas-plan",
            json={"saas_plan_id": plan_id},
            headers=headers
        )
        
        # Create product
        product_data = {
            "gym_id": gym_id,
            "name": f"TEST_Sale_Product_{uuid.uuid4().hex[:6]}",
            "sale_price": 5.00,
            "stock": 50
        }
        product_response = requests.post(f"{BASE_URL}/api/pos/products", json=product_data, headers=headers)
        product = product_response.json()
        
        return {"gym_id": gym_id, "product": product}
    
    def test_create_pos_sale(self, auth_token, gym_with_product):
        """POST /api/pos/sales - create a sale with items"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        sale_data = {
            "gym_id": gym_with_product["gym_id"],
            "items": [
                {
                    "product_id": gym_with_product["product"]["id"],
                    "quantity": 2,
                    "unit_price": gym_with_product["product"]["sale_price"]
                }
            ],
            "payment_method": "cash",
            "notes": "Test sale"
        }
        response = requests.post(f"{BASE_URL}/api/pos/sales", json=sale_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 10.00  # 2 * 5.00
        assert data["payment_method"] == "cash"
        assert len(data["items"]) == 1
        print(f"✓ Created POS sale: total={data['total']}, items={len(data['items'])}")
        return data
    
    def test_get_pos_sales(self, auth_token, gym_with_product):
        """GET /api/pos/sales - returns sales history"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create a sale first
        sale_data = {
            "gym_id": gym_with_product["gym_id"],
            "items": [
                {
                    "product_id": gym_with_product["product"]["id"],
                    "quantity": 1,
                    "unit_price": gym_with_product["product"]["sale_price"]
                }
            ],
            "payment_method": "card"
        }
        requests.post(f"{BASE_URL}/api/pos/sales", json=sale_data, headers=headers)
        
        # Get sales
        response = requests.get(f"{BASE_URL}/api/pos/sales?gym_id={gym_with_product['gym_id']}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/pos/sales returned {len(data)} sales")
    
    def test_get_pos_stats(self, auth_token, gym_with_product):
        """GET /api/pos/stats - returns stats"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/pos/stats?gym_id={gym_with_product['gym_id']}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "today_sales" in data
        assert "today_revenue" in data
        assert "month_sales" in data
        assert "month_revenue" in data
        print(f"✓ GET /api/pos/stats: today_sales={data['today_sales']}, today_revenue={data['today_revenue']}")


class TestAccounting:
    """Tests for Accounting and Cash Withdrawals"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    @pytest.fixture
    def gym_id(self, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/gyms", headers=headers)
        gyms = response.json()
        return gyms[0]["id"] if gyms else None
    
    def test_create_cash_withdrawal(self, auth_token, gym_id):
        """POST /api/accounting/withdrawal - create a cash withdrawal"""
        if not gym_id:
            pytest.skip("No gym available")
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        withdrawal_data = {
            "gym_id": gym_id,
            "amount": 100.00,
            "reason": "Compra de suministros",
            "notes": "Test withdrawal"
        }
        response = requests.post(f"{BASE_URL}/api/accounting/withdrawal", json=withdrawal_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == 100.00
        assert data["reason"] == "Compra de suministros"
        assert "id" in data
        print(f"✓ Created cash withdrawal: amount={data['amount']}, reason={data['reason']}")
    
    def test_get_accounting_report(self, auth_token, gym_id):
        """GET /api/accounting/report - returns combined report"""
        if not gym_id:
            pytest.skip("No gym available")
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/accounting/report?gym_id={gym_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "transactions" in data
        assert "pos_sales" in data
        assert "withdrawals" in data
        assert "summary" in data
        assert "daily_chart" in data
        
        summary = data["summary"]
        assert "total_revenue" in summary
        assert "cash_total" in summary
        assert "net_cash" in summary
        print(f"✓ GET /api/accounting/report: total_revenue={summary['total_revenue']}, net_cash={summary['net_cash']}")


class TestBroadcast:
    """Tests for Broadcast messaging (Super Admin only)"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_create_broadcast(self, auth_token):
        """POST /api/broadcast - create a broadcast (super admin only)"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        broadcast_data = {
            "title": f"TEST_Broadcast_{uuid.uuid4().hex[:6]}",
            "message": "Este es un mensaje de prueba para todos los gimnasios",
            "priority": "normal"
        }
        response = requests.post(f"{BASE_URL}/api/broadcast", json=broadcast_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == broadcast_data["title"]
        assert data["message"] == broadcast_data["message"]
        assert data["priority"] == "normal"
        assert data["active"] == True
        assert "id" in data
        print(f"✓ Created broadcast: {data['title']} (id: {data['id']})")
        return data
    
    def test_get_active_broadcasts(self, auth_token):
        """GET /api/broadcast/active - returns broadcasts"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create a broadcast first
        broadcast_data = {
            "title": f"TEST_Active_Broadcast_{uuid.uuid4().hex[:6]}",
            "message": "Mensaje activo",
            "priority": "urgent"
        }
        requests.post(f"{BASE_URL}/api/broadcast", json=broadcast_data, headers=headers)
        
        # Get active broadcasts
        response = requests.get(f"{BASE_URL}/api/broadcast/active", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/broadcast/active returned {len(data)} broadcasts")


class TestMercadoPago:
    """Tests for MercadoPago integration"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    @pytest.fixture
    def gym_id(self, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/gyms", headers=headers)
        gyms = response.json()
        return gyms[0]["id"] if gyms else None
    
    def test_get_mercadopago_config(self, auth_token, gym_id):
        """GET /api/gyms/{gym_id}/mercadopago-config - get MP config"""
        if not gym_id:
            pytest.skip("No gym available")
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/gyms/{gym_id}/mercadopago-config", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "has_mercadopago" in data
        assert "masked_token" in data
        print(f"✓ GET /api/gyms/{gym_id}/mercadopago-config: has_mercadopago={data['has_mercadopago']}")


class TestDashboardAndAccess:
    """Tests for Dashboard and Access endpoints (regression)"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_dashboard_stats(self, auth_token):
        """GET /api/dashboard/stats - dashboard still works after refactor"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_gyms" in data or "total_members" in data or "active_members" in data
        print(f"✓ GET /api/dashboard/stats working")
    
    def test_access_self_test(self, auth_token):
        """GET /api/access/self-test - QR self test still works"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/access/self-test", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "dynamic_qr_test" in data
        assert "static_qr_test" in data
        assert data["dynamic_qr_test"]["valid"] == True
        assert data["static_qr_test"]["valid"] == True
        print(f"✓ GET /api/access/self-test: all_passed={data.get('all_passed', True)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
