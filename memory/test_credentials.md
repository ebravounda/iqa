# Test Credentials

## Super Admin
- Email: admin@gymaccess.com
- Password: admin123
- Login URL: /admin/login
- API Login: POST /api/auth/admin/login

## Test Member
- Code: RMB8S5
- Member Login URL: /app/login
- Gym ID: efe99507-15d5-4e54-9f07-30d2507894e0

## Notes
- Super Admin has full access to all features
- The admin panel is at /admin/login
- Production super admin is soporte@ingresoqr.com (different credentials)
- JWT tokens expire in 30 days (720 hours)
- Member /me endpoint returns fresh token for silent session refresh
