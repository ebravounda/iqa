# IngresoQR - Product Requirements Document

## Original Problem Statement
Create a comprehensive SaaS multi-tenant gym access control system ("IngresoQR"). The system requires a backend, an Admin dashboard, and a PWA for gym members. Core features include dynamic QR codes for access, physical turnstile control (Raspberry Pi), POS with thermal printing, role-based access, corporate branding, WHMCS integration for automated tenant lifecycle management, and multi-vertical support.

## Architecture
- **Backend**: FastAPI (Python) on port 8001
- **Frontend**: React PWA (CRA + craco)
- **Database**: MongoDB
- **Deployment**: Plesk on AWS EC2 (`c.ingresoqr.com` backend, `app.ingresoqr.com` frontend)
- **White-label**: `sistema.lafabrikagym.com` via Nginx proxy
- **Centralized services**: `membership_service.py` (create/expire/activate memberships)

## What's Been Implemented
- Full multi-tenant gym management (gyms, members, plans, memberships)
- Dynamic/Static QR codes for member access (QRCodeCanvas for device compatibility)
- Turnstile control (Raspberry Pi integration with gpiozero + evdev)
- POS system with thermal printing
- Role-based access (super_admin, gym_admin, gym_manager with permissions)
- WHMCS 7.9.0 provisioning module
- Stripe/MercadoPago/Redsys payment integration (all using centralized membership_service)
- Per-gym payment gateway selector
- Gamification, routines, classes system
- Auto-suspension cron for expired memberships
- Device management (admin + member self-service)
- Kiosk HDMI display for real-time occupancy
- JWT 30-day token with silent auto-refresh
- "Recordarme" (Remember Me) with auto-login
- Device deactivation auto-logout (via /me polling)
- Kiosk display link in admin Devices page

## Completed - April 2026 (This Session)
- [x] QR Canvas fix for Samsung gama baja (A05s/A14/A15)
- [x] JWT 24h -> 30 days + silent token refresh
- [x] PWA login redesign (6-char individual inputs, paste, auto-submit)
- [x] "Recordarme" toggle with auto-login
- [x] Device limit self-service (member can deactivate own devices)
- [x] Auto-logout on device deactivation (via /me polling every 30s)
- [x] Kiosk display link card in AdminDevices
- [x] REFACTORING: Created membership_service.py (centralized membership logic)
- [x] REFACTORING: Replaced duplicated code in 6 route files (plan, payment, stripe, redsys, mercadopago, stripe_auto)
- [x] REFACTORING: Deleted /backend/downloads/ (3039-line old monolithic copy)
- [x] REFACTORING: Fixed systemd service WorkingDirectory
- [x] QR level restored to "H" (High) for USB scanner compatibility

## Pending / Backlog

### P0 - Verification
- Verify Raspberry Pi HDMI Kiosk green/red flash on QR scan

### P1 - High Priority
- VeriFactu Compliance (Spanish electronic invoicing for POS)
- Class check-in / attendance tracking (QR check-in via PWA)
- Facial Recognition Integration (RGPD legal review needed first)

### P2 - Medium Priority
- WhatsApp Bot (Twilio/OpenClaw) for reminders
- Camera recording on QR scan (5-second clips)
- Interactive muscle map with exercise routines
- AdminSettings.js split into smaller components (1456 lines)
- AdminMembers.js split into smaller components (1281 lines)

## Deployment Commands (Plesk SSH)
```bash
# Backend
cd /opt/gymaccess && rm -rf frontend/build && git checkout -- . && git pull origin main && \cp -rf frontend/build/* /var/www/vhosts/ingresoqr.com/app.ingresoqr.com/ && bash /opt/gymaccess/deploy-whitelabel.sh && systemctl restart gymaccess-api
```

## Key API Endpoints
- POST /api/auth/admin/login
- POST /api/auth/member/login?code=XXX
- GET /api/auth/member/me?device_fingerprint=XXX
- POST /api/memberships (uses membership_service)
- POST /api/payments/manual (uses membership_service)
- GET /api/my-devices-by-code?code=XXX
- PUT /api/my-devices-by-code/{id}/deactivate?code=XXX
- POST /api/access/event
- GET /api/access/display/{gym_id}
