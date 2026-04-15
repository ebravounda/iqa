# IngresoQR - Product Requirements Document

## Original Problem Statement
Create a comprehensive SaaS multi-tenant gym access control system ("IngresoQR"). The system requires a backend, an Admin dashboard, and a PWA for gym members. Core features include dynamic QR codes for access, physical turnstile control (Raspberry Pi), POS with thermal printing, role-based access, corporate branding, WHMCS integration for automated tenant lifecycle management, and multi-vertical support.

## Architecture
- **Backend**: FastAPI (Python) on port 8001
- **Frontend**: React PWA (CRA + craco)
- **Database**: MongoDB
- **Deployment**: Plesk on AWS EC2 (`c.ingresoqr.com` backend, `app.ingresoqr.com` frontend)

## What's Been Implemented
- Full multi-tenant gym management (gyms, members, plans, memberships)
- Dynamic/Static QR codes for member access
- Turnstile control (Raspberry Pi integration)
- POS system with thermal printing
- Role-based access (super_admin, gym_admin, gym_manager with permissions)
- WHMCS 7.9.0 provisioning module
- Member import from Excel (IsMyGym migration)
- Bulk plan import from JSON
- Bulk membership assignment with vencimientos data
- Member expiration date editing with comments and audit log (NEW - Feb 2026)
- RFID card assignment
- Email system (welcome, reminders)
- Stripe/MercadoPago payment integration
- Gamification, routines, classes system
- Auto-suspension cron for expired memberships
- Excel export of members
- Device management per member

## Completed - Feb 2026
- [x] Fixed duplicate useState bug in AdminMembers.js (showMembershipModal conflict)
- [x] PUT /api/members/{member_id}/membership endpoint - edit expiration date with comment
- [x] Edit Expiration Modal in AdminMembers.js (click on Vencimiento date)
- [x] membership_edit permission for gym managers
- [x] Audit logging in membership_logs collection
- [x] GET /api/members/{member_id}/membership-logs endpoint - fetch change history
- [x] Gym logo displayed correctly in PWA Layout (relative URL fix + object-contain for wide logos)
- [x] Gym logo displayed in Admin Layout sidebar and mobile header
- [x] "Historial de cambios" section in edit expiration modal showing who/when/what changed
- [x] Redsys TPV Virtual integration - full payment flow (using official redsys library v0.3.1)
- [x] Per-gym Redsys configuration (merchant code, terminal, secret key SHA-256, environment)
- [x] Payment gateway selector (Ninguna/Redsys/Stripe/MercadoPago) - Super Admin only
- [x] Stripe and Redsys config restricted to Super Admin only (gym admin cannot see)
- [x] Fixed dashboard occupancy widget disappearing (Promise.all → Promise.allSettled + expiring memberships timezone bug)
- [x] Redsys tested and working in production (La Fabrika - Ruralvía bank)

## Pending / Backlog

### P1 - High Priority
- Facial Recognition Integration (face_recognition Python library)
- VeriFactu Compliance (Spanish electronic invoicing for POS)
- Class check-in / attendance tracking (QR check-in via PWA)

### P2 - Medium Priority
- WhatsApp AI Assistant (MyClaw)
- "Live Class" Kiosk Screen
- White-label Frontend for FitnessMNG client
- AdminMembers.js refactoring (extract modals to separate components)

## Deployment Commands (Plesk SSH)
```bash
cd /opt/gymaccess/frontend
export PATH=$PATH:/usr/local/bin:/opt/plesk/node/20/bin
npm install ajv@8 --legacy-peer-deps
npx craco build
```

## Key API Endpoints
- POST /api/auth/admin/login
- GET /api/members
- PUT /api/members/{member_id}/membership (edit expiration)
- POST /api/members/import
- POST /api/plans/import
- POST /api/members/assign-memberships-bulk
