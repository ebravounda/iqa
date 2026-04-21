# IngresoQR - Product Requirements Document

## Original Problem Statement
Create a comprehensive SaaS multi-tenant gym access control system ("IngresoQR"). The system requires a backend, an Admin dashboard, and a PWA for gym members. Core features include dynamic QR codes for access, physical turnstile control (Raspberry Pi), POS with thermal printing, role-based access, corporate branding, WHMCS integration for automated tenant lifecycle management, and multi-vertical support.

## Architecture
- **Backend**: FastAPI (Python) on port 8001
- **Frontend**: React PWA (CRA + craco)
- **Database**: MongoDB
- **Deployment**: Plesk on AWS EC2 (`c.ingresoqr.com` backend, `app.ingresoqr.com` frontend)
- **White-label**: `sistema.lafabrikagym.com` via Nginx proxy

## What's Been Implemented
- Full multi-tenant gym management (gyms, members, plans, memberships)
- Dynamic/Static QR codes for member access (QRCodeCanvas for device compatibility)
- Turnstile control (Raspberry Pi integration with gpiozero + evdev)
- POS system with thermal printing
- Role-based access (super_admin, gym_admin, gym_manager with permissions)
- WHMCS 7.9.0 provisioning module
- Member import from Excel (IsMyGym migration)
- Bulk plan import from JSON
- Bulk membership assignment with vencimientos data
- Member expiration date editing with comments and audit log
- RFID card assignment
- Email system (welcome, reminders)
- Stripe/MercadoPago/Redsys payment integration
- Per-gym payment gateway selector (Stripe/Redsys/MercadoPago/None)
- Gamification, routines, classes system
- Auto-suspension cron for expired memberships
- Excel export of members
- Device management per member (admin + member self-service)
- Kiosk HDMI display for real-time occupancy (KioskDisplay.js)
- Raspberry Pi access_control.py v2.2 with real-time event posting
- JWT 30-day token expiration with silent auto-refresh
- Modern PWA login with 6-character individual code inputs
- "Recordarme" (Remember Me) feature with auto-login
- Device limit self-service: members can deactivate their own devices when limit exceeded

## Completed - April 2026 (This Session)
- [x] QR code rendering: QRCodeSVG -> QRCodeCanvas (fixes budget Samsung A05s/A14/A15 grayish rendering)
- [x] Removed AnimatePresence animation on QR refresh (eliminates gray flash on slow devices)
- [x] Error correction level H -> M (less dense QR, still reliable, better on small screens)
- [x] imageRendering: 'pixelated' on canvas for crisp edges
- [x] JWT expiration 24h -> 30 days (720 hours) - users no longer auto-logout daily
- [x] Silent token refresh: /me endpoint returns fresh token, AuthContext saves it automatically
- [x] PWA MemberLogin.js redesign: 6 individual code input fields with auto-advance, backspace, paste, auto-submit
- [x] "Recordarme" toggle: saves member code in localStorage, auto-logins on next app open
- [x] Device limit self-service: when login fails due to device limit, shows device list with deactivate buttons
- [x] New endpoints: GET/PUT /api/my-devices-by-code for member self-service device management
- [x] Logout clears remembered_code from localStorage

## Completed - Feb 2026 (Previous Sessions)
- [x] Fixed duplicate useState bug in AdminMembers.js
- [x] Edit Expiration Modal with audit logging
- [x] Gym logo object-contain fix across all layouts
- [x] Redsys TPV Virtual integration (official redsys lib v0.3.1)
- [x] Per-gym Redsys configuration and payment gateway selector
- [x] Dashboard timezone fix (naive vs aware datetimes)
- [x] White-label setup for La Fabrika (sistema.lafabrikagym.com)
- [x] Raspberry Pi OS Trixie migration (gpiozero + lgpio + evdev)
- [x] Kiosk Display real-time occupancy screen (KioskDisplay.js)
- [x] access_control.py v2.2 with POST /api/access/event for HDMI green/red flashes

## Pending / Backlog

### P0 - Verification
- Verify Raspberry Pi HDMI Kiosk green/red flash on QR scan (user has script, needs physical test)

### P1 - High Priority
- VeriFactu Compliance (Spanish electronic invoicing for POS)
- Class check-in / attendance tracking (QR check-in via PWA)
- Facial Recognition Integration (face_recognition Python library) - RGPD legal review needed

### P2 - Medium Priority
- WhatsApp Bot (Twilio API or OpenClaw) for reminders and notifications
- AdminSettings.js refactoring (over 1400 lines, monolithic)
- AdminMembers.js refactoring (extract modals to components)

## Deployment Commands (Plesk SSH)
```bash
# Backend
cd /opt/gymaccess && git checkout -- . && git pull origin main && kill $(pgrep -f "uvicorn.*8001") 2>/dev/null; cd /opt/gymaccess/backend && nohup /opt/gymaccess/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001 > /var/log/gymaccess-backend.log 2>&1 &

# Frontend
cd /opt/gymaccess/frontend && export PATH=$PATH:/usr/local/bin:/opt/plesk/node/20/bin && npx craco build && cp -rf build/* /var/www/vhosts/ingresoqr.com/app.ingresoqr.com/

# White-label
bash /opt/gymaccess/deploy-whitelabel.sh
```

## Key API Endpoints
- POST /api/auth/admin/login
- POST /api/auth/member/login?code=XXX
- GET /api/auth/member/me (returns fresh token for session refresh)
- GET /api/my-devices-by-code?code=XXX (member self-service devices)
- PUT /api/my-devices-by-code/{id}/deactivate?code=XXX
- POST /api/access/event (Raspberry Pi -> Kiosk display)
- GET /api/access/display/{gym_id} (Kiosk data feed)
- POST /api/redsys/initiate
- POST /api/redsys/notification
