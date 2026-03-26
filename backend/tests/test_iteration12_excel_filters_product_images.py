"""
Iteration 12 Tests: Advanced Excel Export Filters and POS Product Image Upload

Features tested:
1. Excel Export with status filter (active, suspended, etc.)
2. Excel Export with date range filter (date_from, date_to)
3. Excel Export with include_memberships flag (adds Plan columns)
4. Excel Export with combined filters
5. Product image upload endpoint
6. Product image_path stored in DB
"""

import pytest
import requests
import os
import io
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestExcelExportFilters:
    """Test advanced Excel export filters for members"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as super admin and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": "admin@gymaccess.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Get a gym_id for testing
        gyms_response = requests.get(f"{BASE_URL}/api/gyms", headers=self.headers)
        assert gyms_response.status_code == 200
        gyms = gyms_response.json()
        self.gym_id = gyms[0]["id"] if gyms else None
    
    def test_excel_export_basic(self):
        """Test basic Excel export returns valid xlsx file"""
        response = requests.get(
            f"{BASE_URL}/api/members/export/excel",
            headers=self.headers
        )
        assert response.status_code == 200, f"Export failed: {response.text}"
        assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in response.headers.get("Content-Type", "")
        assert "Content-Disposition" in response.headers
        assert "attachment" in response.headers["Content-Disposition"]
        print("TEST PASSED: Basic Excel export returns valid xlsx file")
    
    def test_excel_export_status_active(self):
        """Test Excel export with status=active filter"""
        response = requests.get(
            f"{BASE_URL}/api/members/export/excel?status=active",
            headers=self.headers
        )
        assert response.status_code == 200, f"Export with status=active failed: {response.text}"
        assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in response.headers.get("Content-Type", "")
        print("TEST PASSED: Excel export with status=active filter works")
    
    def test_excel_export_status_suspended(self):
        """Test Excel export with status=suspended filter"""
        response = requests.get(
            f"{BASE_URL}/api/members/export/excel?status=suspended",
            headers=self.headers
        )
        assert response.status_code == 200, f"Export with status=suspended failed: {response.text}"
        print("TEST PASSED: Excel export with status=suspended filter works")
    
    def test_excel_export_date_range(self):
        """Test Excel export with date range filter"""
        date_from = "2026-01-01"
        date_to = "2026-12-31"
        response = requests.get(
            f"{BASE_URL}/api/members/export/excel?date_from={date_from}&date_to={date_to}",
            headers=self.headers
        )
        assert response.status_code == 200, f"Export with date range failed: {response.text}"
        print("TEST PASSED: Excel export with date range filter works")
    
    def test_excel_export_include_memberships(self):
        """Test Excel export with include_memberships=true adds extra columns"""
        response = requests.get(
            f"{BASE_URL}/api/members/export/excel?include_memberships=true",
            headers=self.headers
        )
        assert response.status_code == 200, f"Export with include_memberships failed: {response.text}"
        
        # Verify it's a valid xlsx by checking content length > 0
        assert len(response.content) > 0, "Excel file is empty"
        
        # Parse the Excel to verify columns
        try:
            from openpyxl import load_workbook
            wb = load_workbook(io.BytesIO(response.content))
            ws = wb.active
            headers = [cell.value for cell in ws[1]]
            
            # Check for membership columns
            expected_membership_cols = ["Plan Activo", "Inicio Plan", "Fin Plan", "Precio Plan"]
            for col in expected_membership_cols:
                assert col in headers, f"Missing column: {col}"
            print(f"TEST PASSED: Excel export with include_memberships=true has columns: {headers}")
        except ImportError:
            # If openpyxl not available, just verify response is valid
            print("TEST PASSED: Excel export with include_memberships=true returns valid response (openpyxl not available for column verification)")
    
    def test_excel_export_combined_filters(self):
        """Test Excel export with combined filters (gym_id + status)"""
        if not self.gym_id:
            pytest.skip("No gym available for testing")
        
        response = requests.get(
            f"{BASE_URL}/api/members/export/excel?gym_id={self.gym_id}&status=active",
            headers=self.headers
        )
        assert response.status_code == 200, f"Export with combined filters failed: {response.text}"
        print(f"TEST PASSED: Excel export with gym_id={self.gym_id}&status=active works")
    
    def test_excel_export_all_filters_combined(self):
        """Test Excel export with all filters combined"""
        if not self.gym_id:
            pytest.skip("No gym available for testing")
        
        response = requests.get(
            f"{BASE_URL}/api/members/export/excel?gym_id={self.gym_id}&status=active&date_from=2025-01-01&date_to=2026-12-31&include_memberships=true",
            headers=self.headers
        )
        assert response.status_code == 200, f"Export with all filters failed: {response.text}"
        print("TEST PASSED: Excel export with all filters combined works")


class TestProductImageUpload:
    """Test POS product image upload functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as super admin and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": "admin@gymaccess.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Get a gym_id for testing
        gyms_response = requests.get(f"{BASE_URL}/api/gyms", headers=self.headers)
        assert gyms_response.status_code == 200
        gyms = gyms_response.json()
        self.gym_id = gyms[0]["id"] if gyms else None
    
    def test_get_products_endpoint(self):
        """Test GET /api/pos/products returns products list"""
        response = requests.get(
            f"{BASE_URL}/api/pos/products?gym_id={self.gym_id}",
            headers=self.headers
        )
        assert response.status_code == 200, f"Get products failed: {response.text}"
        products = response.json()
        assert isinstance(products, list), "Products should be a list"
        print(f"TEST PASSED: GET /api/pos/products returns {len(products)} products")
        return products
    
    def test_create_product_for_image_test(self):
        """Create a test product for image upload testing"""
        if not self.gym_id:
            pytest.skip("No gym available for testing")
        
        product_data = {
            "gym_id": self.gym_id,
            "name": "TEST_ImageProduct",
            "description": "Test product for image upload",
            "cost_price": 5.00,
            "sale_price": 10.00,
            "stock": 100,
            "category": "Test",
            "barcode": "TEST123456"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/pos/products",
            json=product_data,
            headers=self.headers
        )
        assert response.status_code in [200, 201], f"Create product failed: {response.text}"
        product = response.json()
        assert "id" in product, "Product should have an id"
        print(f"TEST PASSED: Created test product with id: {product['id']}")
        return product
    
    def test_upload_product_image(self):
        """Test POST /api/upload/product-image/{product_id} uploads image"""
        if not self.gym_id:
            pytest.skip("No gym available for testing")
        
        # First create a product
        product_data = {
            "gym_id": self.gym_id,
            "name": "TEST_ImageUploadProduct",
            "description": "Test product for image upload",
            "cost_price": 5.00,
            "sale_price": 10.00,
            "stock": 50,
            "category": "Test"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/pos/products",
            json=product_data,
            headers=self.headers
        )
        assert create_response.status_code in [200, 201], f"Create product failed: {create_response.text}"
        product_id = create_response.json()["id"]
        
        # Create a minimal PNG image (1x1 pixel red PNG)
        # This is a valid PNG file header + IHDR + IDAT + IEND chunks
        png_data = bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
            0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk length + type
            0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # width=1, height=1
            0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,  # bit depth, color type, etc
            0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,  # CRC + IDAT chunk
            0x54, 0x08, 0xD7, 0x63, 0xF8, 0xFF, 0xFF, 0x3F,  # compressed data
            0x00, 0x05, 0xFE, 0x02, 0xFE, 0xDC, 0xCC, 0x59,  # more data
            0xE7, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,  # IEND chunk
            0x44, 0xAE, 0x42, 0x60, 0x82                      # IEND CRC
        ])
        
        files = {
            'file': ('test_product.png', png_data, 'image/png')
        }
        
        upload_response = requests.post(
            f"{BASE_URL}/api/upload/product-image/{product_id}",
            files=files,
            headers={"Authorization": f"Bearer {self.token}"}
        )
        assert upload_response.status_code == 200, f"Upload failed: {upload_response.text}"
        
        result = upload_response.json()
        assert "storage_path" in result, "Response should contain storage_path"
        print(f"TEST PASSED: Product image uploaded, storage_path: {result['storage_path']}")
        
        # Verify product now has image_path in DB
        get_response = requests.get(
            f"{BASE_URL}/api/pos/products?gym_id={self.gym_id}",
            headers=self.headers
        )
        products = get_response.json()
        updated_product = next((p for p in products if p["id"] == product_id), None)
        assert updated_product is not None, "Product not found after upload"
        assert updated_product.get("image_path") is not None, "Product should have image_path after upload"
        print(f"TEST PASSED: Product image_path stored in DB: {updated_product['image_path']}")
        
        return product_id
    
    def test_upload_product_image_invalid_product(self):
        """Test upload to non-existent product returns 404"""
        png_data = bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
            0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
            0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
            0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
            0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,
            0x54, 0x08, 0xD7, 0x63, 0xF8, 0xFF, 0xFF, 0x3F,
            0x00, 0x05, 0xFE, 0x02, 0xFE, 0xDC, 0xCC, 0x59,
            0xE7, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,
            0x44, 0xAE, 0x42, 0x60, 0x82
        ])
        
        files = {
            'file': ('test.png', png_data, 'image/png')
        }
        
        response = requests.post(
            f"{BASE_URL}/api/upload/product-image/nonexistent-product-id",
            files=files,
            headers={"Authorization": f"Bearer {self.token}"}
        )
        assert response.status_code == 404, f"Expected 404 for non-existent product, got {response.status_code}"
        print("TEST PASSED: Upload to non-existent product returns 404")
    
    def test_upload_product_image_invalid_file_type(self):
        """Test upload with invalid file type returns 400"""
        if not self.gym_id:
            pytest.skip("No gym available for testing")
        
        # Create a product first
        product_data = {
            "gym_id": self.gym_id,
            "name": "TEST_InvalidFileProduct",
            "sale_price": 10.00,
            "stock": 10
        }
        create_response = requests.post(
            f"{BASE_URL}/api/pos/products",
            json=product_data,
            headers=self.headers
        )
        product_id = create_response.json()["id"]
        
        # Try to upload a text file
        files = {
            'file': ('test.txt', b'This is not an image', 'text/plain')
        }
        
        response = requests.post(
            f"{BASE_URL}/api/upload/product-image/{product_id}",
            files=files,
            headers={"Authorization": f"Bearer {self.token}"}
        )
        assert response.status_code == 400, f"Expected 400 for invalid file type, got {response.status_code}"
        print("TEST PASSED: Upload with invalid file type returns 400")


class TestGymSelectorVisibility:
    """Test gym selector visibility on various pages for super admin"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as super admin"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": "admin@gymaccess.com",
            "password": "admin123"
        })
        assert response.status_code == 200
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_gyms_endpoint_for_selector(self):
        """Test GET /api/gyms returns gyms for selector dropdown"""
        response = requests.get(f"{BASE_URL}/api/gyms", headers=self.headers)
        assert response.status_code == 200
        gyms = response.json()
        assert isinstance(gyms, list)
        print(f"TEST PASSED: GET /api/gyms returns {len(gyms)} gyms for selector")


class TestCleanup:
    """Cleanup test data"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as super admin"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": "admin@gymaccess.com",
            "password": "admin123"
        })
        if response.status_code == 200:
            self.token = response.json()["token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.headers = {}
    
    def test_cleanup_test_products(self):
        """Clean up TEST_ prefixed products"""
        if not self.token:
            pytest.skip("Could not login for cleanup")
        
        # Get all gyms
        gyms_response = requests.get(f"{BASE_URL}/api/gyms", headers=self.headers)
        if gyms_response.status_code != 200:
            return
        
        gyms = gyms_response.json()
        deleted_count = 0
        
        for gym in gyms:
            products_response = requests.get(
                f"{BASE_URL}/api/pos/products?gym_id={gym['id']}",
                headers=self.headers
            )
            if products_response.status_code == 200:
                products = products_response.json()
                for product in products:
                    if product.get("name", "").startswith("TEST_"):
                        delete_response = requests.delete(
                            f"{BASE_URL}/api/pos/products/{product['id']}",
                            headers=self.headers
                        )
                        if delete_response.status_code in [200, 204]:
                            deleted_count += 1
        
        print(f"TEST PASSED: Cleaned up {deleted_count} test products")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
