import requests
import sys
import json
from datetime import datetime

class GymAccessAPITester:
    def __init__(self, base_url="https://stripe-gym-payments.preview.emergentagent.com"):
        self.base_url = base_url
        self.admin_token = None
        self.member_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_resources = {
            'gym_id': None,
            'member_id': None,
            'plan_id': None,
            'membership_id': None
        }

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {method} {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return True, response.json()
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test basic health endpoints"""
        print("\n=== HEALTH CHECK TESTS ===")
        self.run_test("API Root", "GET", "", 200)
        self.run_test("Health Check", "GET", "health", 200)

    def test_admin_auth(self):
        """Test admin authentication"""
        print("\n=== ADMIN AUTHENTICATION TESTS ===")
        
        # Test admin login with default credentials
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/admin/login",
            200,
            data={"email": "admin@gymaccess.com", "password": "admin123"}
        )
        
        if success and 'token' in response:
            self.admin_token = response['token']
            print(f"   Admin token obtained: {self.admin_token[:20]}...")
            return True
        return False

    def test_gym_management(self):
        """Test gym CRUD operations"""
        print("\n=== GYM MANAGEMENT TESTS ===")
        
        if not self.admin_token:
            print("❌ No admin token available")
            return False

        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Create gym
        gym_data = {
            "name": "Test Gym",
            "address": "123 Test Street",
            "phone": "+1234567890",
            "email": "test@gym.com",
            "primary_color": "#E1FF01",
            "qr_refresh_seconds": 10
        }
        
        success, response = self.run_test(
            "Create Gym",
            "POST",
            "gyms",
            200,
            data=gym_data,
            headers=headers
        )
        
        if success and 'id' in response:
            self.created_resources['gym_id'] = response['id']
            print(f"   Created gym ID: {response['id']}")
        
        # Get gyms
        self.run_test("Get Gyms", "GET", "gyms", 200, headers=headers)
        
        return success

    def test_member_management(self):
        """Test member CRUD operations"""
        print("\n=== MEMBER MANAGEMENT TESTS ===")
        
        if not self.admin_token or not self.created_resources['gym_id']:
            print("❌ Missing admin token or gym ID")
            return False

        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Create member
        member_data = {
            "email": "testmember@gym.com",
            "name": "Test Member",
            "phone": "+1234567890",
            "gym_id": self.created_resources['gym_id']
        }
        
        success, response = self.run_test(
            "Create Member",
            "POST",
            "members",
            200,
            data=member_data,
            headers=headers
        )
        
        if success and 'id' in response:
            self.created_resources['member_id'] = response['id']
            print(f"   Created member ID: {response['id']}")
            print(f"   Member code: {response.get('code', 'N/A')}")
        
        # Get members
        self.run_test("Get Members", "GET", "members", 200, headers=headers)
        
        return success

    def test_plan_management(self):
        """Test plan CRUD operations"""
        print("\n=== PLAN MANAGEMENT TESTS ===")
        
        if not self.admin_token or not self.created_resources['gym_id']:
            print("❌ Missing admin token or gym ID")
            return False

        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Create plan
        plan_data = {
            "gym_id": self.created_resources['gym_id'],
            "name": "Monthly Plan",
            "description": "Basic monthly membership",
            "price": 50.0,
            "duration_days": 30,
            "access_type": "unlimited"
        }
        
        success, response = self.run_test(
            "Create Plan",
            "POST",
            "plans",
            200,
            data=plan_data,
            headers=headers
        )
        
        if success and 'id' in response:
            self.created_resources['plan_id'] = response['id']
            print(f"   Created plan ID: {response['id']}")
        
        # Get plans
        self.run_test("Get Plans", "GET", "plans", 200, headers=headers)
        
        return success

    def test_membership_management(self):
        """Test membership operations"""
        print("\n=== MEMBERSHIP MANAGEMENT TESTS ===")
        
        if not self.admin_token or not self.created_resources['member_id'] or not self.created_resources['plan_id']:
            print("❌ Missing required resources")
            return False

        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Create membership
        membership_data = {
            "member_id": self.created_resources['member_id'],
            "plan_id": self.created_resources['plan_id']
        }
        
        success, response = self.run_test(
            "Create Membership",
            "POST",
            "memberships",
            200,
            data=membership_data,
            headers=headers
        )
        
        if success and 'id' in response:
            self.created_resources['membership_id'] = response['id']
            print(f"   Created membership ID: {response['id']}")
        
        # Get memberships
        self.run_test("Get Memberships", "GET", "memberships", 200, headers=headers)
        
        return success

    def test_member_login(self):
        """Test member login with test code"""
        print("\n=== MEMBER LOGIN TESTS ===")
        
        # Test with the provided test member code
        success, response = self.run_test(
            "Member Login (LRF4HL)",
            "POST",
            "auth/member/login?code=LRF4HL",
            200
        )
        
        if success and 'token' in response:
            self.member_token = response['token']
            print(f"   Member token obtained: {self.member_token[:20]}...")
            return True
        
        return False

    def test_qr_generation(self):
        """Test QR code generation"""
        print("\n=== QR CODE TESTS ===")
        
        if not self.member_token:
            print("❌ No member token available")
            return False

        headers = {'Authorization': f'Bearer {self.member_token}'}
        
        success, response = self.run_test(
            "Generate QR Code",
            "GET",
            "qr/generate",
            200,
            headers=headers
        )
        
        if success and 'qr_code' in response:
            print(f"   QR Code generated: {response['qr_code'][:20]}...")
            print(f"   Expires at: {response.get('expires_at')}")
            print(f"   Refresh seconds: {response.get('refresh_seconds')}")
        
        return success

    def test_access_validation(self):
        """Test access validation endpoint (for Raspberry Pi)"""
        print("\n=== ACCESS VALIDATION TESTS ===")
        
        # This would normally require a valid gym token and QR code
        # For now, we'll test with invalid data to check the endpoint exists
        validation_data = {
            "qr_code": "invalid_qr_code",
            "gym_token": "invalid_token",
            "direction": "entrada"
        }
        
        # Expecting 200 with valid: false for invalid data
        success, response = self.run_test(
            "Access Validation (Invalid)",
            "POST",
            "access/validate",
            200,
            data=validation_data
        )
        
        if success and 'valid' in response:
            print(f"   Validation result: {response['valid']}")
            print(f"   Reason: {response.get('reason', 'N/A')}")
        
        return success

    def test_dashboard_stats(self):
        """Test dashboard statistics"""
        print("\n=== DASHBOARD TESTS ===")
        
        if not self.admin_token:
            print("❌ No admin token available")
            return False

        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        success, response = self.run_test(
            "Dashboard Stats",
            "GET",
            "dashboard/stats",
            200,
            headers=headers
        )
        
        if success:
            print(f"   Total members: {response.get('total_members', 0)}")
            print(f"   Active members: {response.get('active_members', 0)}")
            print(f"   Today accesses: {response.get('today_accesses', 0)}")
        
        return success

    def test_access_logs(self):
        """Test access logs endpoint"""
        print("\n=== ACCESS LOGS TESTS ===")
        
        if not self.admin_token:
            print("❌ No admin token available")
            return False

        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        success, response = self.run_test(
            "Get Access Logs",
            "GET",
            "access/logs",
            200,
            headers=headers
        )
        
        if success:
            print(f"   Access logs count: {len(response) if isinstance(response, list) else 0}")
        
        return success

def main():
    print("🚀 Starting Gym Access Control System API Tests")
    print("=" * 60)
    
    tester = GymAccessAPITester()
    
    # Run all tests
    test_results = []
    
    # Basic health tests
    tester.test_health_check()
    
    # Authentication tests
    auth_success = tester.test_admin_auth()
    test_results.append(("Admin Auth", auth_success))
    
    if auth_success:
        # Management tests
        gym_success = tester.test_gym_management()
        test_results.append(("Gym Management", gym_success))
        
        member_success = tester.test_member_management()
        test_results.append(("Member Management", member_success))
        
        plan_success = tester.test_plan_management()
        test_results.append(("Plan Management", plan_success))
        
        membership_success = tester.test_membership_management()
        test_results.append(("Membership Management", membership_success))
        
        # Dashboard tests
        dashboard_success = tester.test_dashboard_stats()
        test_results.append(("Dashboard Stats", dashboard_success))
        
        logs_success = tester.test_access_logs()
        test_results.append(("Access Logs", logs_success))
    
    # Member tests
    member_login_success = tester.test_member_login()
    test_results.append(("Member Login", member_login_success))
    
    if member_login_success:
        qr_success = tester.test_qr_generation()
        test_results.append(("QR Generation", qr_success))
    
    # Access validation test
    validation_success = tester.test_access_validation()
    test_results.append(("Access Validation", validation_success))
    
    # Print final results
    print("\n" + "=" * 60)
    print("📊 FINAL TEST RESULTS")
    print("=" * 60)
    
    for test_name, success in test_results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:<25} {status}")
    
    print(f"\n📈 Overall: {tester.tests_passed}/{tester.tests_run} tests passed")
    success_rate = (tester.tests_passed / tester.tests_run * 100) if tester.tests_run > 0 else 0
    print(f"📊 Success Rate: {success_rate:.1f}%")
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())