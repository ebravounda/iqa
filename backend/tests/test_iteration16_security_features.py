"""
Iteration 16: Security Features Tests
- Rate limiting on admin/member login (5 failed attempts = 15 min block)
- IP blocking with HTTP 429 response
- Login attempt recording (success/failure)
- Security endpoints (stats, blocked-ips, login-attempts) - super_admin only
- Unblock IP endpoints
- Security headers in responses
"""
import pytest
import requests
import os
import time
import random
import string

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

def random_ip():
    """Generate a random IP for testing to avoid cross-contamination"""
    return f"192.168.{random.randint(1,254)}.{random.randint(1,254)}"

def random_email():
    """Generate random email for failed login tests"""
    suffix = ''.join(random.choices(string.ascii_lowercase, k=6))
    return f"fake_{suffix}@test.com"

class TestSecurityHeaders:
    """Test security headers are present in responses"""
    
    def test_security_headers_present(self):
        """Verify X-Content-Type-Options, X-Frame-Options, X-XSS-Protection headers"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        
        # Check security headers
        assert response.headers.get("X-Content-Type-Options") == "nosniff", "Missing X-Content-Type-Options header"
        assert response.headers.get("X-Frame-Options") == "DENY", "Missing X-Frame-Options header"
        assert response.headers.get("X-XSS-Protection") == "1; mode=block", "Missing X-XSS-Protection header"
        print("✓ All security headers present")


class TestAdminLogin:
    """Test admin login with rate limiting"""
    
    @pytest.fixture
    def admin_token(self):
        """Get super admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": "admin@gymaccess.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        return response.json()["token"]
    
    def test_admin_login_success(self):
        """Test successful admin login records attempt"""
        test_ip = random_ip()
        response = requests.post(
            f"{BASE_URL}/api/auth/admin/login",
            json={"email": "admin@gymaccess.com", "password": "admin123"},
            headers={"X-Forwarded-For": test_ip}
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "admin" in data
        assert data["admin"]["email"] == "admin@gymaccess.com"
        print(f"✓ Admin login successful from IP {test_ip}")
    
    def test_admin_login_invalid_credentials(self):
        """Test failed admin login records attempt"""
        test_ip = random_ip()
        response = requests.post(
            f"{BASE_URL}/api/auth/admin/login",
            json={"email": "wrong@test.com", "password": "wrongpass"},
            headers={"X-Forwarded-For": test_ip}
        )
        assert response.status_code == 401
        assert "Credenciales invalidas" in response.json().get("detail", "")
        print(f"✓ Failed admin login recorded from IP {test_ip}")


class TestRateLimiting:
    """Test rate limiting - 5 failed attempts block IP for 15 minutes"""
    
    @pytest.fixture
    def admin_token(self):
        """Get super admin token for cleanup"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": "admin@gymaccess.com",
            "password": "admin123"
        })
        return response.json()["token"]
    
    def test_rate_limiting_admin_login(self, admin_token):
        """Test that 5 failed admin login attempts block the IP"""
        test_ip = random_ip()
        fake_email = random_email()
        
        # Make 5 failed attempts
        for i in range(5):
            response = requests.post(
                f"{BASE_URL}/api/auth/admin/login",
                json={"email": fake_email, "password": "wrongpass"},
                headers={"X-Forwarded-For": test_ip}
            )
            if i < 4:
                assert response.status_code == 401, f"Attempt {i+1} should return 401"
            else:
                # 5th attempt should trigger block
                assert response.status_code in [401, 429], f"Attempt 5 should return 401 or 429"
        
        # 6th attempt should be blocked with 429
        response = requests.post(
            f"{BASE_URL}/api/auth/admin/login",
            json={"email": fake_email, "password": "wrongpass"},
            headers={"X-Forwarded-For": test_ip}
        )
        assert response.status_code == 429, f"Expected 429 after 5 failed attempts, got {response.status_code}"
        assert "bloqueada" in response.json().get("detail", "").lower()
        print(f"✓ IP {test_ip} blocked after 5 failed admin login attempts")
        
        # Cleanup: unblock the IP
        requests.delete(
            f"{BASE_URL}/api/security/blocked-ips/{test_ip}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
    
    def test_rate_limiting_member_login(self, admin_token):
        """Test that 5 failed member login attempts block the IP"""
        test_ip = random_ip()
        
        # Make 5 failed attempts with wrong code
        for i in range(5):
            response = requests.post(
                f"{BASE_URL}/api/auth/member/login?code=WRONGCODE{i}",
                headers={"X-Forwarded-For": test_ip}
            )
            if i < 4:
                assert response.status_code == 404, f"Attempt {i+1} should return 404 (code not found)"
        
        # 6th attempt should be blocked with 429
        response = requests.post(
            f"{BASE_URL}/api/auth/member/login?code=WRONGCODE99",
            headers={"X-Forwarded-For": test_ip}
        )
        assert response.status_code == 429, f"Expected 429 after 5 failed attempts, got {response.status_code}"
        assert "bloqueada" in response.json().get("detail", "").lower()
        print(f"✓ IP {test_ip} blocked after 5 failed member login attempts")
        
        # Cleanup: unblock the IP
        requests.delete(
            f"{BASE_URL}/api/security/blocked-ips/{test_ip}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
    
    def test_blocked_ip_receives_429_on_admin_login(self, admin_token):
        """Test that a blocked IP receives 429 on admin login attempt"""
        test_ip = random_ip()
        fake_email = random_email()
        
        # Block the IP by making 5 failed attempts
        for i in range(5):
            requests.post(
                f"{BASE_URL}/api/auth/admin/login",
                json={"email": fake_email, "password": "wrongpass"},
                headers={"X-Forwarded-For": test_ip}
            )
        
        # Now try with valid credentials - should still be blocked
        response = requests.post(
            f"{BASE_URL}/api/auth/admin/login",
            json={"email": "admin@gymaccess.com", "password": "admin123"},
            headers={"X-Forwarded-For": test_ip}
        )
        assert response.status_code == 429, f"Blocked IP should get 429 even with valid credentials, got {response.status_code}"
        print(f"✓ Blocked IP {test_ip} receives 429 on admin login")
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/security/blocked-ips/{test_ip}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
    
    def test_blocked_ip_receives_429_on_member_login(self, admin_token):
        """Test that a blocked IP receives 429 on member login attempt"""
        test_ip = random_ip()
        
        # Block the IP by making 5 failed attempts
        for i in range(5):
            requests.post(
                f"{BASE_URL}/api/auth/member/login?code=WRONGCODE{i}",
                headers={"X-Forwarded-For": test_ip}
            )
        
        # Now try member login - should be blocked
        response = requests.post(
            f"{BASE_URL}/api/auth/member/login?code=ANYCODE",
            headers={"X-Forwarded-For": test_ip}
        )
        assert response.status_code == 429, f"Blocked IP should get 429, got {response.status_code}"
        print(f"✓ Blocked IP {test_ip} receives 429 on member login")
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/security/blocked-ips/{test_ip}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )


class TestSecurityEndpoints:
    """Test security management endpoints - super_admin only"""
    
    @pytest.fixture
    def admin_token(self):
        """Get super admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": "admin@gymaccess.com",
            "password": "admin123"
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    def test_get_security_stats(self, admin_token):
        """GET /api/security/stats returns security statistics"""
        response = requests.get(
            f"{BASE_URL}/api/security/stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify expected fields
        assert "active_blocks" in data
        assert "total_blocks_history" in data
        assert "failed_24h" in data
        assert "failed_7d" in data
        assert "success_24h" in data
        
        # Verify types
        assert isinstance(data["active_blocks"], int)
        assert isinstance(data["failed_24h"], int)
        assert isinstance(data["success_24h"], int)
        print(f"✓ Security stats: {data}")
    
    def test_get_blocked_ips(self, admin_token):
        """GET /api/security/blocked-ips returns active and expired blocks"""
        response = requests.get(
            f"{BASE_URL}/api/security/blocked-ips",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "active" in data
        assert "expired" in data
        assert isinstance(data["active"], list)
        assert isinstance(data["expired"], list)
        print(f"✓ Blocked IPs: {len(data['active'])} active, {len(data['expired'])} expired")
    
    def test_get_login_attempts(self, admin_token):
        """GET /api/security/login-attempts returns login attempts with filters"""
        # Test without filters
        response = requests.get(
            f"{BASE_URL}/api/security/login-attempts",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "attempts" in data
        assert "total" in data
        print(f"✓ Login attempts: {data['total']} total")
        
        # Test with type filter
        response = requests.get(
            f"{BASE_URL}/api/security/login-attempts?attempt_type=admin",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        for attempt in data["attempts"]:
            assert attempt["type"] == "admin"
        print(f"✓ Login attempts filtered by type=admin: {data['total']}")
        
        # Test with success filter
        response = requests.get(
            f"{BASE_URL}/api/security/login-attempts?success=true",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        for attempt in data["attempts"]:
            assert attempt["success"] == True
        print(f"✓ Login attempts filtered by success=true: {data['total']}")
    
    def test_unblock_specific_ip(self, admin_token):
        """DELETE /api/security/blocked-ips/{ip} unblocks a specific IP"""
        test_ip = random_ip()
        
        # First, block the IP
        for i in range(5):
            requests.post(
                f"{BASE_URL}/api/auth/admin/login",
                json={"email": random_email(), "password": "wrongpass"},
                headers={"X-Forwarded-For": test_ip}
            )
        
        # Verify IP is blocked
        response = requests.get(
            f"{BASE_URL}/api/security/blocked-ips",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        active_ips = [b["ip"] for b in response.json()["active"]]
        assert test_ip in active_ips, f"IP {test_ip} should be blocked"
        
        # Unblock the IP
        response = requests.delete(
            f"{BASE_URL}/api/security/blocked-ips/{test_ip}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert "desbloqueada" in response.json().get("message", "").lower()
        
        # Verify IP is no longer blocked
        response = requests.get(
            f"{BASE_URL}/api/security/blocked-ips",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        active_ips = [b["ip"] for b in response.json()["active"]]
        assert test_ip not in active_ips, f"IP {test_ip} should be unblocked"
        print(f"✓ IP {test_ip} successfully unblocked")
    
    def test_unblock_all_ips(self, admin_token):
        """DELETE /api/security/blocked-ips unblocks all IPs"""
        # Block a few IPs first
        test_ips = [random_ip() for _ in range(2)]
        for test_ip in test_ips:
            for i in range(5):
                requests.post(
                    f"{BASE_URL}/api/auth/admin/login",
                    json={"email": random_email(), "password": "wrongpass"},
                    headers={"X-Forwarded-For": test_ip}
                )
        
        # Unblock all
        response = requests.delete(
            f"{BASE_URL}/api/security/blocked-ips",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert "desbloqueadas" in response.json().get("message", "").lower()
        
        # Verify no active blocks
        response = requests.get(
            f"{BASE_URL}/api/security/blocked-ips",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert len(response.json()["active"]) == 0, "All IPs should be unblocked"
        print("✓ All IPs successfully unblocked")
    
    def test_security_endpoints_require_super_admin(self):
        """Security endpoints should return 403 for non-super_admin"""
        # Try without auth
        response = requests.get(f"{BASE_URL}/api/security/stats")
        assert response.status_code in [401, 403], "Should require authentication"
        
        response = requests.get(f"{BASE_URL}/api/security/blocked-ips")
        assert response.status_code in [401, 403], "Should require authentication"
        
        response = requests.get(f"{BASE_URL}/api/security/login-attempts")
        assert response.status_code in [401, 403], "Should require authentication"
        print("✓ Security endpoints require authentication")


class TestLoginAttemptRecording:
    """Test that login attempts are properly recorded"""
    
    @pytest.fixture
    def admin_token(self):
        """Get super admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "email": "admin@gymaccess.com",
            "password": "admin123"
        })
        return response.json()["token"]
    
    def test_successful_admin_login_recorded(self, admin_token):
        """Successful admin login should be recorded"""
        test_ip = random_ip()
        
        # Login successfully
        response = requests.post(
            f"{BASE_URL}/api/auth/admin/login",
            json={"email": "admin@gymaccess.com", "password": "admin123"},
            headers={"X-Forwarded-For": test_ip}
        )
        assert response.status_code == 200
        
        # Check login attempts
        response = requests.get(
            f"{BASE_URL}/api/security/login-attempts?attempt_type=admin&success=true&limit=50",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        attempts = response.json()["attempts"]
        
        # Find our attempt
        found = any(a["ip"] == test_ip and a["success"] == True and a["identifier"] == "admin@gymaccess.com" for a in attempts)
        assert found, f"Successful login from {test_ip} should be recorded"
        print(f"✓ Successful admin login from {test_ip} recorded")
    
    def test_failed_admin_login_recorded(self, admin_token):
        """Failed admin login should be recorded"""
        test_ip = random_ip()
        fake_email = random_email()
        
        # Fail login
        response = requests.post(
            f"{BASE_URL}/api/auth/admin/login",
            json={"email": fake_email, "password": "wrongpass"},
            headers={"X-Forwarded-For": test_ip}
        )
        assert response.status_code == 401
        
        # Check login attempts
        response = requests.get(
            f"{BASE_URL}/api/security/login-attempts?attempt_type=admin&success=false&limit=50",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        attempts = response.json()["attempts"]
        
        # Find our attempt
        found = any(a["ip"] == test_ip and a["success"] == False and a["identifier"] == fake_email for a in attempts)
        assert found, f"Failed login from {test_ip} should be recorded"
        print(f"✓ Failed admin login from {test_ip} recorded")
    
    def test_failed_member_login_recorded(self, admin_token):
        """Failed member login should be recorded"""
        test_ip = random_ip()
        wrong_code = f"WRONG{random.randint(1000,9999)}"
        
        # Fail login
        response = requests.post(
            f"{BASE_URL}/api/auth/member/login?code={wrong_code}",
            headers={"X-Forwarded-For": test_ip}
        )
        assert response.status_code == 404
        
        # Check login attempts
        response = requests.get(
            f"{BASE_URL}/api/security/login-attempts?attempt_type=member&success=false&limit=50",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        attempts = response.json()["attempts"]
        
        # Find our attempt
        found = any(a["ip"] == test_ip and a["success"] == False and a["identifier"] == wrong_code for a in attempts)
        assert found, f"Failed member login from {test_ip} should be recorded"
        print(f"✓ Failed member login from {test_ip} recorded")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
