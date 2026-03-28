#!/usr/bin/env python3
"""
IngresoQR - System Documentation PDF Generator
Generates comprehensive documentation in English and Spanish
"""
from fpdf import FPDF
import os

class DocPDF(FPDF):
    def __init__(self, lang="en"):
        super().__init__()
        self.lang = lang
        self.set_auto_page_break(auto=True, margin=20)
        
    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(100, 100, 100)
        title = "IngresoQR - System Documentation" if self.lang == "en" else "IngresoQR - Documentacion del Sistema"
        self.cell(0, 8, title, align="L")
        self.ln(10)
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)
    
    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")
    
    def chapter_title(self, title, level=1):
        if level == 1:
            self.set_font("Helvetica", "B", 18)
            self.set_text_color(20, 20, 40)
            self.ln(6)
            self.cell(0, 12, title)
            self.ln(4)
            self.set_draw_color(225, 255, 1)
            self.set_line_width(1)
            self.line(10, self.get_y(), 80, self.get_y())
            self.set_line_width(0.2)
            self.ln(8)
        elif level == 2:
            self.set_font("Helvetica", "B", 14)
            self.set_text_color(40, 40, 60)
            self.ln(4)
            self.cell(0, 10, title)
            self.ln(10)
        elif level == 3:
            self.set_font("Helvetica", "B", 11)
            self.set_text_color(60, 60, 80)
            self.ln(2)
            self.cell(0, 8, title)
            self.ln(8)
    
    def body_text(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 5.5, text)
        self.ln(3)
    
    def bullet(self, text, indent=10):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(30, 30, 30)
        x = self.get_x()
        self.cell(indent, 5.5, "")
        self.set_font("Helvetica", "B", 10)
        self.cell(5, 5.5, "- ")
        self.set_font("Helvetica", "", 10)
        self.multi_cell(0, 5.5, text)
        self.ln(1)
    
    def code_block(self, text, title=""):
        if title:
            self.set_font("Helvetica", "I", 9)
            self.set_text_color(80, 80, 80)
            self.cell(0, 5, title)
            self.ln(5)
        self.set_fill_color(240, 240, 245)
        self.set_font("Courier", "", 8.5)
        self.set_text_color(30, 30, 30)
        lines = text.split("\n")
        for line in lines:
            safe = line.encode('latin-1', 'replace').decode('latin-1')
            self.cell(0, 4.5, "  " + safe, fill=True)
            self.ln(4.5)
        self.ln(4)
    
    def table_row(self, cols, widths, header=False):
        if header:
            self.set_font("Helvetica", "B", 9)
            self.set_fill_color(30, 30, 50)
            self.set_text_color(255, 255, 255)
        else:
            self.set_font("Helvetica", "", 9)
            self.set_fill_color(248, 248, 250)
            self.set_text_color(30, 30, 30)
        for i, col in enumerate(cols):
            safe = str(col).encode('latin-1', 'replace').decode('latin-1')
            self.cell(widths[i], 7, safe, border=1, fill=True)
        self.ln(7)
    
    def info_box(self, title, text):
        self.set_fill_color(255, 253, 230)
        self.set_draw_color(225, 255, 1)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(60, 60, 0)
        self.cell(0, 6, "  " + title, fill=True, border="LTR")
        self.ln(6)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 5, "  " + text, fill=True, border="LBR")
        self.ln(4)


def generate_english_doc():
    pdf = DocPDF(lang="en")
    pdf.alias_nb_pages()
    
    # ===== COVER =====
    pdf.add_page()
    pdf.ln(40)
    pdf.set_font("Helvetica", "B", 36)
    pdf.set_text_color(20, 20, 40)
    pdf.cell(0, 20, "IngresoQR", align="C")
    pdf.ln(18)
    pdf.set_font("Helvetica", "", 16)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 10, "Multi-Tenant Gym Access Control System", align="C")
    pdf.ln(8)
    pdf.cell(0, 10, "Complete Technical Documentation", align="C")
    pdf.ln(20)
    pdf.set_draw_color(225, 255, 1)
    pdf.set_line_width(2)
    pdf.line(70, pdf.get_y(), 140, pdf.get_y())
    pdf.set_line_width(0.2)
    pdf.ln(20)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 8, "Version 2.0  |  February 2026", align="C")
    pdf.ln(6)
    pdf.cell(0, 8, "FastAPI + React + MongoDB + Raspberry Pi", align="C")
    
    # ===== TABLE OF CONTENTS =====
    pdf.add_page()
    pdf.chapter_title("Table of Contents")
    toc = [
        "1. System Overview",
        "2. Architecture & Technology Stack",
        "3. Project Structure (File Tree)",
        "4. User Roles & Permissions",
        "5. Database Schema (MongoDB Collections)",
        "6. Backend API Reference",
        "7. Frontend Pages & Routing",
        "8. Authentication & Security",
        "9. QR Code System (Dynamic & Static)",
        "10. Raspberry Pi / IoT Integration",
        "11. Payment System (Stripe & MercadoPago)",
        "12. SaaS Multi-Tenant Model",
        "13. Email System (SMTP per Gym)",
        "14. Background Jobs (Cron Tasks)",
        "15. Deployment Guide (Plesk VPS)",
        "16. Environment Variables",
        "17. Troubleshooting & FAQ",
    ]
    for item in toc:
        pdf.bullet(item, indent=5)
    
    # ===== 1. SYSTEM OVERVIEW =====
    pdf.add_page()
    pdf.chapter_title("1. System Overview")
    pdf.body_text(
        "IngresoQR is a comprehensive SaaS multi-tenant gym access control system. "
        "It provides gym owners with a complete solution for managing memberships, "
        "controlling physical access via QR codes, processing payments, tracking attendance, "
        "and managing classes. The system consists of three main components:"
    )
    pdf.bullet("Admin Dashboard: Web interface for gym administrators to manage all aspects of their gym")
    pdf.bullet("Member PWA: Progressive Web App for gym members to access their QR code, book classes, view stats")
    pdf.bullet("Raspberry Pi Controller: Physical IoT device that reads QR codes and controls entry/exit turnstiles via GPIO relays")
    
    pdf.chapter_title("Key Features", level=2)
    features = [
        "Dynamic QR codes refreshing every 5/10/15 seconds (configurable per gym)",
        "Static QR mode for members with connectivity issues",
        "Anti-passback: Alternates entry/exit direction automatically",
        "Multi-tier roles: Super Admin, Gym Admin, Manager, Trainer, Member",
        "Stripe & MercadoPago payment integration (per-gym API keys)",
        "SaaS plan management with 12 configurable feature flags",
        "Class scheduling with recurring patterns and booking system",
        "POS (Point of Sale) for product inventory and sales",
        "Gamification with badges and streaks",
        "Custom routines assigned by trainers to members",
        "Custom registration forms per gym",
        "Guest pass system with QR access",
        "SMTP email system (configurable per gym)",
        "Analytics dashboard with hourly heatmaps and retention metrics",
        "Excel export of member data",
        "PDF sales reports",
        "Security: IP blocking after failed login attempts",
        "Member device management (limit devices per member)",
        "Kiosk mode for self-registration at the gym",
        "Dark/Light theme support",
    ]
    for f in features:
        pdf.bullet(f)
    
    # ===== 2. ARCHITECTURE =====
    pdf.add_page()
    pdf.chapter_title("2. Architecture & Technology Stack")
    
    pdf.chapter_title("Backend", level=2)
    pdf.bullet("Framework: FastAPI (Python 3.11+)")
    pdf.bullet("Database: MongoDB (via Motor async driver)")
    pdf.bullet("Authentication: JWT (python-jose + bcrypt)")
    pdf.bullet("ASGI Server: Uvicorn")
    pdf.bullet("File Storage: Local filesystem (/opt/gymaccess/uploads)")
    pdf.bullet("Email: aiosmtplib (async SMTP)")
    pdf.bullet("Payments: Stripe SDK, MercadoPago SDK")
    pdf.bullet("Excel: openpyxl")
    pdf.bullet("PDF: reportlab or fpdf2")
    
    pdf.chapter_title("Frontend", level=2)
    pdf.bullet("Framework: React 18 (Create React App)")
    pdf.bullet("Styling: Tailwind CSS + custom CSS variables for theming")
    pdf.bullet("UI Components: Shadcn/UI (Radix-based)")
    pdf.bullet("HTTP Client: Axios")
    pdf.bullet("Routing: React Router v6")
    pdf.bullet("Toasts: Sonner")
    pdf.bullet("Fonts: Chivo (headings) + Manrope (body)")
    pdf.bullet("Icons: Lucide React")
    
    pdf.chapter_title("IoT (Raspberry Pi)", level=2)
    pdf.bullet("Hardware: Raspberry Pi 3B+ with 2-channel relay module")
    pdf.bullet("QR Scanner: USB barcode/QR scanner (HID keyboard emulation)")
    pdf.bullet("GPIO: BCM mode, Pin 12 (entry relay), Pin 16 (exit relay)")
    pdf.bullet("Libraries: RPi.GPIO, evdev, requests, python-dotenv")
    
    pdf.chapter_title("Communication Flow", level=2)
    pdf.body_text(
        "1. Member opens PWA -> Frontend requests QR from backend -> Backend generates HMAC-signed QR\n"
        "2. Member shows QR at turnstile -> Raspberry Pi scanner reads QR\n"
        "3. Raspberry Pi sends QR to POST /api/access/validate\n"
        "4. Backend validates signature, checks membership, records access log\n"
        "5. Backend responds valid/invalid -> Raspberry Pi activates entry or exit relay for 3 seconds"
    )
    
    # ===== 3. PROJECT STRUCTURE =====
    pdf.add_page()
    pdf.chapter_title("3. Project Structure")
    pdf.code_block(
        "/app\n"
        "|-- backend/\n"
        "|   |-- server.py              # FastAPI app, routers, startup tasks\n"
        "|   |-- models.py              # Pydantic request models\n"
        "|   |-- auth.py                # JWT, password hashing, role checks\n"
        "|   |-- database.py            # MongoDB connection (Motor)\n"
        "|   |-- qr_utils.py            # QR generation & validation (HMAC)\n"
        "|   |-- storage.py             # Local file storage helper\n"
        "|   |-- requirements.txt       # Python dependencies\n"
        "|   |-- requirements-prod.txt  # Production dependencies\n"
        "|   |-- .env                   # Environment variables\n"
        "|   |-- routes/\n"
        "|   |   |-- auth_routes.py         # Login, register, profile\n"
        "|   |   |-- gym_routes.py          # CRUD gyms, capacity, suspend\n"
        "|   |   |-- member_routes.py       # CRUD members, export Excel\n"
        "|   |   |-- plan_routes.py         # Membership plans & assign\n"
        "|   |   |-- access_routes.py       # QR gen, validate, access logs\n"
        "|   |   |-- device_routes.py       # IoT device registration\n"
        "|   |   |-- payment_routes.py      # Stripe checkout, webhooks\n"
        "|   |   |-- mercadopago_routes.py  # MercadoPago integration\n"
        "|   |   |-- class_routes.py        # Classes, schedules, bookings\n"
        "|   |   |-- saas_routes.py         # SaaS plans, subscriptions\n"
        "|   |   |-- pos_routes.py          # Products, sales, POS stats\n"
        "|   |   |-- accounting_routes.py   # Financial reports, PDF\n"
        "|   |   |-- analytics_routes.py    # Heatmaps, retention, stats\n"
        "|   |   |-- notification_guest_routes.py  # Notifications & guests\n"
        "|   |   |-- security_routes.py     # IP blocking, login attempts\n"
        "|   |   |-- upload_routes.py       # Avatar, logo, product images\n"
        "|   |   |-- form_routes.py         # Custom registration forms\n"
        "|   |   |-- gamification_routes.py # Badges and streaks\n"
        "|   |   |-- routine_routes.py      # Trainer routines\n"
        "|   |   |-- device_member_routes.py # Member device management\n"
        "|   |   |-- device_management_routes.py  # Device admin tools\n"
        "|   |   |-- stripe_auto_routes.py  # Automated Stripe billing\n"
        "|   |   |-- misc_routes.py         # Email, dashboard, downloads\n"
        "|   |   |-- demo_routes.py         # Demo data generation\n"
        "|   |-- downloads/\n"
        "|   |   |-- raspberry_access_control.py  # Raspberry Pi script\n"
        "|   |   |-- test_gpio.py                 # GPIO test utility\n"
        "|   |-- tests/                 # Pytest test files\n"
        "|-- frontend/\n"
        "|   |-- src/\n"
        "|   |   |-- App.js             # Main router\n"
        "|   |   |-- App.css            # Global styles + CSS variables\n"
        "|   |   |-- context/AuthContext.js  # Auth state management\n"
        "|   |   |-- lib/api.js         # Axios API functions\n"
        "|   |   |-- lib/utils.js       # Utility functions\n"
        "|   |   |-- components/\n"
        "|   |   |   |-- ErrorBoundary.js   # React error catch\n"
        "|   |   |   |-- MemberAvatar.js    # Avatar component\n"
        "|   |   |   |-- ui/                # Shadcn UI components\n"
        "|   |   |-- layouts/\n"
        "|   |   |   |-- AdminLayout.js     # Admin sidebar + header\n"
        "|   |   |   |-- PWALayout.js       # Member bottom nav\n"
        "|   |   |-- pages/admin/       # 28 admin page components\n"
        "|   |   |-- pages/pwa/         # 14 member page components\n"
        "|   |-- build/                 # Production build output\n"
        "|   |-- package.json\n"
        "|-- memory/PRD.md              # Product requirements\n"
    )
    
    # ===== 4. ROLES =====
    pdf.add_page()
    pdf.chapter_title("4. User Roles & Permissions")
    
    pdf.chapter_title("Role Hierarchy", level=2)
    roles = [
        ["super_admin", "null", "Full platform control. Manages all gyms, SaaS plans, devices, security."],
        ["gym_admin", "UUID", "Full control of their gym. Members, plans, payments, classes, settings."],
        ["gym_manager", "UUID", "Configurable permissions. Subset of gym_admin capabilities."],
        ["trainer", "UUID", "Manages classes assigned to them. Creates routines. Views own dashboard."],
        ["member", "UUID", "Accesses PWA. Views QR, books classes, manages profile."],
    ]
    widths = [30, 20, 140]
    pdf.table_row(["Role", "gym_id", "Description"], widths, header=True)
    for r in roles:
        pdf.table_row(r, widths)
    
    pdf.ln(4)
    pdf.chapter_title("Manager Permissions (Configurable)", level=2)
    perms = [
        ["members_view", "View member list"],
        ["members_create", "Create new members"],
        ["members_edit", "Edit member details"],
        ["members_delete", "Delete members"],
        ["members_suspend", "Suspend/Reactivate members"],
        ["payments_register", "Register manual payments"],
        ["pos_sell", "Process POS sales"],
        ["pos_products", "Manage POS products"],
        ["access_view", "View access logs"],
        ["classes_manage", "Manage classes & schedules"],
        ["data_export", "Export data (Excel)"],
        ["notifications_send", "Send notifications"],
    ]
    widths = [50, 140]
    pdf.table_row(["Permission Key", "Description"], widths, header=True)
    for p in perms:
        pdf.table_row(p, widths)
    
    # ===== 5. DATABASE =====
    pdf.add_page()
    pdf.chapter_title("5. Database Schema (MongoDB)")
    pdf.body_text("MongoDB is used as the primary database. All documents use a UUID string 'id' field as the primary key (not ObjectId). The '_id' field is always excluded from API responses.")
    
    collections = [
        ("admins", "Admin users (super_admin, gym_admin, gym_manager, trainer)", 
         "id, email, password (bcrypt), name, role, gym_id, permissions[], active, created_at"),
        ("gyms", "Gym tenants", 
         "id, name, address, phone, email, logo_url, primary_color, qr_refresh_seconds, qr_mode, max_members, api_token, stripe_secret_key, stripe_currency, mercadopago_access_token, currency, smtp_host, smtp_port, smtp_user, smtp_password, smtp_from_email, email_templates[], saas_plan_id, status, created_at"),
        ("members", "Gym members", 
         "id, email, name, phone, code (6-char), gym_id, status (active/suspended/pending/blocked), gender, avatar_path, qr_mode, suspension_reason, can_bring_guests, max_guests_per_month, form_responses, created_at"),
        ("plans", "Membership plans", 
         "id, gym_id, name, description, price, duration_days, access_type, active, created_at"),
        ("memberships", "Active/expired memberships", 
         "id, member_id, plan_id, gym_id, start_date, end_date, status (active/expired), payment_id, created_at"),
        ("access_logs", "Entry/exit records", 
         "id, member_id, member_name, member_code, gym_id, direction (entrada/salida), timestamp, is_guest, guest_id"),
        ("payment_transactions", "Payment records (Stripe/Manual/MP)", 
         "id, session_id, member_id, plan_id, gym_id, amount, currency, status, payment_status, payment_method, notes, created_at"),
        ("classes", "Class definitions", 
         "id, gym_id, name, description, trainer_id, max_capacity, duration_minutes, class_type, recurring, days_of_week[], start_time, end_time, start_date, end_date, active, created_at"),
        ("class_schedules", "Individual class occurrences", 
         "id, class_id, gym_id, date, start_time, end_time, trainer_id, max_capacity, current_bookings, status, created_at"),
        ("bookings", "Class bookings by members", 
         "id, member_id, member_name, schedule_id, class_id, gym_id, date, status, checked_in, checked_in_at, created_at"),
        ("devices", "Registered IoT devices (Raspberry Pi)", 
         "id, gym_id, name, location, status, last_ping, created_at"),
        ("notifications", "Gym notifications for members", 
         "id, gym_id, title, message, notification_type, target, created_by, read_by[], created_at"),
        ("guests", "Guest passes", 
         "id, code, name, phone, invited_by, invited_by_name, gym_id, valid_until, valid_days, status, accesses, created_at"),
        ("saas_plans", "Platform SaaS tier plans", 
         "id, name, max_members, has_qr_access, has_guest_passes, has_classes, has_pos, has_analytics, has_gamification, has_routines, has_email_smtp, has_stripe_members, has_mercadopago, has_iframes, has_advanced_accounting, price_monthly, currency, active"),
        ("pos_products", "POS product inventory", 
         "id, gym_id, name, description, cost_price, sale_price, stock, category, barcode, image_path, active, created_at"),
        ("pos_sales", "POS sales transactions", 
         "id, gym_id, items[], total, currency, payment_method, member_id, registered_by, created_at"),
        ("email_logs", "Sent email history", 
         "id, gym_id, member_id, to_email, subject, email_type, status, error, sent_at"),
        ("routines", "Trainer-assigned routines", 
         "id, gym_id, name, description, trainer_id, member_id, days[], active, created_at"),
        ("broadcasts", "Platform-wide announcements (Super Admin)", 
         "id, title, message, priority, created_by, active, dismissed_by[], created_at"),
        ("blocked_ips", "Blocked IPs from brute force", 
         "ip, blocked_until, reason, blocked_at, last_identifier"),
        ("login_attempts", "Login attempt audit trail", 
         "ip, identifier, type, user_agent, timestamp, success"),
        ("files", "Uploaded file metadata", 
         "id, user_id, storage_path, original_filename, content_type, size, file_type, created_at"),
    ]
    
    for name, desc, fields in collections:
        pdf.chapter_title(f"Collection: {name}", level=3)
        pdf.body_text(desc)
        pdf.set_font("Courier", "", 8)
        safe = fields.encode('latin-1', 'replace').decode('latin-1')
        pdf.set_fill_color(240, 240, 245)
        pdf.multi_cell(0, 4.5, safe, fill=True)
        pdf.ln(3)
    
    # ===== 6. API REFERENCE =====
    pdf.add_page()
    pdf.chapter_title("6. Backend API Reference")
    pdf.body_text("All API endpoints are prefixed with /api. Authentication is via Bearer JWT token in the Authorization header unless marked as public.")
    
    api_sections = [
        ("Authentication", [
            ("POST", "/api/auth/admin/register", "Register a new admin user"),
            ("POST", "/api/auth/admin/login", "Admin login, returns JWT token"),
            ("POST", "/api/auth/admin/impersonate/{gym_id}", "Super Admin impersonates Gym Admin"),
            ("PUT", "/api/auth/admin/update-profile", "Update email/password"),
            ("POST", "/api/auth/member/login?code=XXX", "Member login by access code"),
            ("GET", "/api/auth/member/me", "Get current member profile + gym + membership"),
        ]),
        ("Gyms", [
            ("POST", "/api/gyms", "Create gym (+ optional gym admin)"),
            ("GET", "/api/gyms", "List gyms (filtered by role)"),
            ("GET", "/api/gyms/{id}", "Get gym details"),
            ("PUT", "/api/gyms/{id}", "Update gym settings"),
            ("DELETE", "/api/gyms/{id}", "Delete gym + all related data"),
            ("PUT", "/api/gyms/{id}/suspend", "Toggle gym suspension"),
            ("PUT", "/api/gyms/{id}/payment-suspend", "Toggle payment suspension"),
            ("GET", "/api/gyms/{id}/capacity", "Get member capacity stats"),
            ("GET", "/api/gyms/{id}/public-info", "Public: gym name, logo, payment status"),
        ]),
        ("Members", [
            ("POST", "/api/members", "Create member (admin)"),
            ("POST", "/api/members/register", "Public self-registration"),
            ("GET", "/api/members", "List members (?gym_id, ?status)"),
            ("GET", "/api/members/{id}", "Get member details"),
            ("PUT", "/api/members/{id}", "Update member"),
            ("POST", "/api/members/{id}/suspend", "Suspend with reason"),
            ("DELETE", "/api/members/{id}", "Delete member + related data"),
            ("POST", "/api/members/check-expired-memberships", "Suspend expired members"),
            ("GET", "/api/members/export/excel", "Export members to .xlsx"),
        ]),
        ("Plans & Memberships", [
            ("POST", "/api/plans", "Create membership plan"),
            ("GET", "/api/plans", "List plans"),
            ("GET", "/api/plans/public/{gym_id}", "Public: plans for a gym"),
            ("PUT", "/api/plans/{id}", "Update plan"),
            ("DELETE", "/api/plans/{id}", "Soft-delete plan"),
            ("POST", "/api/memberships", "Assign membership to member"),
            ("GET", "/api/memberships", "List memberships"),
            ("GET", "/api/memberships/expiring?days=10", "Expiring memberships"),
        ]),
        ("Access & QR", [
            ("GET", "/api/qr/generate", "Generate QR for logged-in member"),
            ("POST", "/api/access/validate", "PUBLIC: Validate QR (Raspberry Pi)"),
            ("GET", "/api/access/logs", "Access logs (?gym_id, ?member_id, ?dates)"),
            ("GET", "/api/access/stats", "Access statistics"),
            ("GET", "/api/access/stats/daily?days=7", "Daily access breakdown"),
            ("GET", "/api/access/stats/hourly", "Hourly distribution"),
            ("GET", "/api/access/stats/member/{id}", "Individual member stats"),
            ("PUT", "/api/members/{id}/qr-mode", "Set static/dynamic QR"),
        ]),
        ("Payments", [
            ("POST", "/api/payments/checkout?plan_id=X", "Create Stripe checkout session"),
            ("GET", "/api/payments/status/{session_id}", "Check payment status"),
            ("POST", "/api/payments/manual", "Register manual payment"),
            ("GET", "/api/payments/history", "Payment history"),
            ("GET", "/api/gyms/{id}/stripe-config", "Get Stripe config (masked)"),
            ("PUT", "/api/gyms/{id}/stripe-config", "Update Stripe API key"),
            ("POST", "/api/webhook/stripe", "Stripe webhook handler"),
        ]),
        ("Classes & Bookings", [
            ("POST", "/api/classes", "Create class"),
            ("GET", "/api/classes", "List classes"),
            ("PUT", "/api/classes/{id}", "Update class (regenerates schedules)"),
            ("DELETE", "/api/classes/{id}", "Delete class + schedules"),
            ("POST", "/api/schedules", "Create individual schedule"),
            ("GET", "/api/schedules", "List schedules"),
            ("GET", "/api/schedules/public/{gym_id}", "Public: upcoming schedules"),
            ("POST", "/api/bookings", "Book a class (member)"),
            ("GET", "/api/bookings/member", "Member's bookings"),
            ("DELETE", "/api/bookings/{id}", "Cancel booking"),
            ("POST", "/api/bookings/{id}/checkin", "Check-in for class"),
            ("POST", "/api/classes/cleanup-stale-schedules", "Remove orphaned schedules"),
        ]),
        ("SaaS Management", [
            ("POST", "/api/saas/plans", "Create SaaS plan (Super Admin)"),
            ("GET", "/api/saas/plans", "List SaaS plans"),
            ("PUT", "/api/saas/plans/{id}", "Update SaaS plan"),
            ("PUT", "/api/gyms/{id}/saas-plan", "Assign SaaS plan to gym"),
            ("GET", "/api/gyms/{id}/saas-features", "Get gym's active features"),
            ("GET", "/api/saas/my-subscription", "Gym Admin: my subscription"),
            ("POST", "/api/saas/subscribe", "Subscribe to SaaS plan (Stripe)"),
        ]),
        ("POS", [
            ("POST", "/api/pos/products", "Create product"),
            ("GET", "/api/pos/products", "List products"),
            ("PUT", "/api/pos/products/{id}", "Update product"),
            ("POST", "/api/pos/sales", "Create sale"),
            ("GET", "/api/pos/sales", "List sales"),
            ("GET", "/api/pos/stats", "POS statistics"),
        ]),
        ("Security", [
            ("GET", "/api/security/blocked-ips", "List blocked IPs"),
            ("DELETE", "/api/security/blocked-ips/{ip}", "Unblock IP"),
            ("GET", "/api/security/login-attempts", "Login attempt audit"),
            ("GET", "/api/security/stats", "Security statistics"),
        ]),
    ]
    
    for section_name, endpoints in api_sections:
        pdf.chapter_title(section_name, level=2)
        widths = [15, 75, 100]
        pdf.table_row(["Method", "Endpoint", "Description"], widths, header=True)
        for method, endpoint, desc in endpoints:
            safe_ep = endpoint.encode('latin-1', 'replace').decode('latin-1')
            safe_desc = desc.encode('latin-1', 'replace').decode('latin-1')
            pdf.table_row([method, safe_ep, safe_desc], widths)
        pdf.ln(4)
    
    # ===== 7. FRONTEND =====
    pdf.add_page()
    pdf.chapter_title("7. Frontend Pages & Routing")
    
    pdf.chapter_title("Admin Panel (/admin/*)", level=2)
    admin_pages = [
        ["/admin/login", "AdminLogin.js", "Admin login form"],
        ["/admin", "AdminDashboard.js", "Main dashboard with stats"],
        ["/admin/gyms", "AdminGyms.js", "Gym management (CRUD)"],
        ["/admin/members", "AdminMembers.js", "Member management"],
        ["/admin/plans", "AdminPlans.js", "Membership plans"],
        ["/admin/classes", "AdminClasses.js", "Class management"],
        ["/admin/attendance", "AdminAttendance.js", "Class attendance"],
        ["/admin/schedules", "AdminSchedules.js", "Schedule calendar"],
        ["/admin/staff", "AdminStaff.js", "Staff management"],
        ["/admin/access", "AdminAccess.js", "Access logs viewer"],
        ["/admin/devices", "AdminDevices.js", "IoT device management"],
        ["/admin/notifications", "AdminNotifications.js", "Push notifications"],
        ["/admin/guests", "AdminGuests.js", "Guest passes"],
        ["/admin/accounting", "AdminAccounting.js", "Financial reports"],
        ["/admin/pos", "AdminPOS.js", "Point of Sale"],
        ["/admin/analytics", "AdminAnalytics.js", "Advanced analytics"],
        ["/admin/saas-plans", "AdminSaaSPlans.js", "SaaS plan config"],
        ["/admin/settings", "AdminSettings.js", "Gym settings"],
        ["/admin/templates", "AdminTemplates.js", "Email templates"],
        ["/admin/forms", "AdminForms.js", "Custom forms"],
        ["/admin/security", "AdminSecurity.js", "Security dashboard"],
        ["/admin/broadcast", "AdminBroadcast.js", "Platform broadcasts"],
        ["/admin/data", "AdminData.js", "Data management/export"],
        ["/admin/iframes", "AdminIframes.js", "Embeddable widgets"],
        ["/admin/gamification", "AdminGamification.js", "Badges config"],
        ["/admin/routines", "AdminRoutines.js", "Workout routines"],
        ["/admin/device-monitor", "AdminDeviceMonitor.js", "Device status"],
    ]
    widths = [45, 50, 95]
    pdf.table_row(["Route", "Component", "Description"], widths, header=True)
    for p in admin_pages:
        pdf.table_row(p, widths)
    
    pdf.ln(4)
    pdf.chapter_title("Member PWA (/app/*)", level=2)
    pwa_pages = [
        ["/app/login", "MemberLogin.js", "Member code login"],
        ["/app", "MemberHome.js", "QR code display + quick access"],
        ["/app/classes", "MemberClasses.js", "Book classes"],
        ["/app/history", "MemberHistory.js", "Access history"],
        ["/app/stats", "MemberStats.js", "Personal statistics"],
        ["/app/membership", "MemberMembership.js", "Membership details + pay"],
        ["/app/notifications", "MemberNotifications.js", "Notifications"],
        ["/app/guests", "MemberGuests.js", "Invite guests"],
        ["/app/achievements", "MemberGamification.js", "Badges & streaks"],
        ["/app/routines", "MemberRoutines.js", "Training routines"],
        ["/app/profile", "MemberProfile.js", "Profile settings"],
        ["/app/payment-success", "PaymentSuccess.js", "Post-payment confirmation"],
    ]
    widths = [45, 50, 95]
    pdf.table_row(["Route", "Component", "Description"], widths, header=True)
    for p in pwa_pages:
        pdf.table_row(p, widths)
    
    pdf.ln(4)
    pdf.chapter_title("Public Routes", level=2)
    pdf.bullet("/register/:gymId  ->  PublicRegister.js  (Self-registration page)")
    pdf.bullet("/kiosk/:gymId  ->  KioskPage.js  (On-premises kiosk registration)")
    
    # ===== 8. AUTH & SECURITY =====
    pdf.add_page()
    pdf.chapter_title("8. Authentication & Security")
    
    pdf.chapter_title("JWT Authentication", level=2)
    pdf.body_text(
        "Authentication uses JWT tokens with HS256 algorithm. Tokens expire after 24 hours. "
        "The token payload contains: sub (user ID), role, gym_id, and optionally impersonating/original_role fields."
    )
    pdf.code_block(
        "# Token payload structure:\n"
        "{\n"
        '  "sub": "user-uuid",\n'
        '  "role": "gym_admin",\n'
        '  "gym_id": "gym-uuid",\n'
        '  "exp": 1234567890\n'
        "}"
    )
    
    pdf.chapter_title("Password Security", level=2)
    pdf.body_text("Passwords are hashed using bcrypt with auto-generated salt. Minimum 6 characters for password changes.")
    
    pdf.chapter_title("IP Blocking (Brute Force Protection)", level=2)
    pdf.body_text(
        "After 5 failed login attempts from the same IP within 15 minutes, the IP is blocked for 15 minutes. "
        "Applies to both admin and member logins. Super Admin can view and unblock IPs from the Security dashboard."
    )
    
    pdf.chapter_title("Impersonation", level=2)
    pdf.body_text(
        "Super Admin can impersonate any Gym Admin via POST /api/auth/admin/impersonate/{gym_id}. "
        "This creates a special JWT with impersonating=true and original_role=super_admin, "
        "allowing them to see the gym admin's view without logging out."
    )
    
    # ===== 9. QR SYSTEM =====
    pdf.add_page()
    pdf.chapter_title("9. QR Code System")
    
    pdf.chapter_title("Dynamic QR", level=2)
    pdf.body_text(
        "Dynamic QR codes are regenerated every N seconds (configurable per gym: 5, 10, or 15). "
        "Each QR contains: member_id, gym_id, Unix timestamp, and an HMAC-SHA256 signature (first 16 hex chars). "
        "The data is base64url-encoded."
    )
    pdf.code_block(
        "# Dynamic QR structure (before base64):\n"
        "member_id|gym_id|timestamp|hmac_signature\n\n"
        "# Static QR structure (before base64):\n"
        "STATIC|member_id|gym_id|hmac_signature\n\n"
        "# HMAC secret is set via QR_SECRET env variable"
    )
    
    pdf.chapter_title("Static QR", level=2)
    pdf.body_text(
        "For members with poor connectivity, Super Admin can assign static QR mode. "
        "Static QR codes don't expire (no timestamp check). The mode can be set per-gym or per-member."
    )
    
    pdf.chapter_title("Anti-Passback", level=2)
    pdf.body_text(
        "The system implements automatic anti-passback by checking the last access log for the member. "
        "If the last log was 'entrada' (entry), the next scan becomes 'salida' (exit) and vice versa. "
        "The first scan is always treated as 'entrada'."
    )
    
    # ===== 10. RASPBERRY PI =====
    pdf.add_page()
    pdf.chapter_title("10. Raspberry Pi Integration")
    
    pdf.chapter_title("Hardware Requirements", level=2)
    pdf.bullet("Raspberry Pi 3B+ or newer")
    pdf.bullet("2-channel relay module (5V)")
    pdf.bullet("USB QR code scanner (HID mode - acts as keyboard)")
    pdf.bullet("Wiring: GPIO 12 -> Entry relay, GPIO 16 -> Exit relay")
    pdf.bullet("Relays are active LOW (GPIO.HIGH = relay off)")
    
    pdf.chapter_title("Software Configuration", level=2)
    pdf.code_block(
        "# /opt/gymaccess/.env\n"
        "GYMACCESS_SERVER_URL=https://c.ingresoqr.com\n"
        "GYMACCESS_GYM_TOKEN=your_gym_api_token\n"
        "GYMACCESS_DEVICE_ID=your_device_uuid\n"
        "GYMACCESS_RELAY_ENTRADA=12\n"
        "GYMACCESS_RELAY_SALIDA=16",
        title=".env file on Raspberry Pi"
    )
    
    pdf.chapter_title("Operation Flow", level=2)
    pdf.body_text(
        "1. The script uses evdev to read USB QR scanners as raw input devices\n"
        "2. Multiple scanners can be configured via scanner_map.json (maps device to direction)\n"
        "3. When a QR is scanned, it POSTs to /api/access/validate\n"
        "4. On valid response: activates the appropriate relay for 3 seconds\n"
        "5. Heartbeat ping sent every 60 seconds to /api/devices/{id}/ping\n"
        "6. Auto-reconnects on network errors"
    )
    
    pdf.chapter_title("Running as Service", level=2)
    pdf.code_block(
        "# /etc/systemd/system/gymaccess.service\n"
        "[Unit]\n"
        "Description=GymAccess QR Controller\n"
        "After=network.target\n\n"
        "[Service]\n"
        "User=root\n"
        "WorkingDirectory=/opt/gymaccess\n"
        "ExecStart=/usr/bin/python3 raspberry_access_control.py\n"
        "Restart=always\n"
        "RestartSec=10\n\n"
        "[Install]\n"
        "WantedBy=multi-user.target",
        title="systemd service file"
    )
    
    # ===== 11. PAYMENTS =====
    pdf.add_page()
    pdf.chapter_title("11. Payment System")
    
    pdf.chapter_title("Stripe Integration", level=2)
    pdf.body_text(
        "Each gym can configure its own Stripe secret key. If a gym doesn't have one, "
        "the system falls back to the global STRIPE_API_KEY environment variable. "
        "Payments use Stripe Checkout Sessions for PCI compliance."
    )
    pdf.body_text("Flow: Member selects plan -> Backend creates Checkout Session -> Member pays on Stripe -> Webhook/redirect confirms -> Membership activated")
    
    pdf.chapter_title("MercadoPago Integration", level=2)
    pdf.body_text("Each gym can configure its own MercadoPago access token for Latin American markets. Uses MercadoPago Preferences API.")
    
    pdf.chapter_title("Manual Payments", level=2)
    pdf.body_text("Admins can register manual payments (cash, card, transfer) that immediately create a membership for the member.")
    
    pdf.chapter_title("SaaS Platform Payments", level=2)
    pdf.body_text("Gym owners pay the platform via Stripe subscription. Uses PLATFORM_STRIPE_KEY env variable (separate from gym-level keys).")
    
    # ===== 12. SAAS MODEL =====
    pdf.add_page()
    pdf.chapter_title("12. SaaS Multi-Tenant Model")
    pdf.body_text(
        "The platform operates as a SaaS where each gym is a tenant. Super Admin creates SaaS plans "
        "with configurable feature flags. Each gym is assigned a SaaS plan that determines what features "
        "they can access."
    )
    
    pdf.chapter_title("Feature Flags (12 toggles)", level=2)
    flags = [
        ["has_qr_access", "QR code access control"],
        ["has_guest_passes", "Guest invitation system"],
        ["has_classes", "Class scheduling & booking"],
        ["has_pos", "Point of Sale system"],
        ["has_analytics", "Advanced analytics dashboard"],
        ["has_gamification", "Badges and streak system"],
        ["has_routines", "Trainer-assigned workout routines"],
        ["has_email_smtp", "Custom SMTP email sending"],
        ["has_stripe_members", "Stripe payment for members"],
        ["has_mercadopago", "MercadoPago payment"],
        ["has_iframes", "Embeddable widget iframes"],
        ["has_advanced_accounting", "Advanced accounting reports"],
    ]
    widths = [55, 135]
    pdf.table_row(["Feature Key", "Description"], widths, header=True)
    for f in flags:
        pdf.table_row(f, widths)
    
    pdf.ln(4)
    pdf.chapter_title("Gym Suspension", level=2)
    pdf.body_text(
        "Super Admin can suspend gyms in two ways:\n"
        "1. Manual suspension: Blocks all access (admin login, member login, API)\n"
        "2. Payment suspension: Same block, triggered by unpaid SaaS subscription"
    )
    
    # ===== 13. EMAIL =====
    pdf.add_page()
    pdf.chapter_title("13. Email System")
    pdf.body_text(
        "Each gym configures its own SMTP server in Settings. The system sends emails for:\n"
        "- Welcome emails (with access code)\n"
        "- Membership expiration reminders (1, 3, 7 days before)\n"
        "- Payment confirmations\n"
        "- Custom template emails (editable per gym)"
    )
    pdf.code_block(
        "# Gym SMTP Configuration fields:\n"
        "smtp_host:       SMTP server hostname\n"
        "smtp_port:       Port (587 for STARTTLS, 465 for SSL)\n"
        "smtp_user:       SMTP username\n"
        "smtp_password:   SMTP password\n"
        "smtp_from_email: Sender email address"
    )
    
    pdf.chapter_title("Email Templates", level=2)
    pdf.body_text(
        "Templates support variables like {gym_name}, {member_name}, {member_code}, {expiry_date}, {amount}. "
        "Each gym gets default templates on creation that can be customized."
    )
    
    # ===== 14. BACKGROUND JOBS =====
    pdf.add_page()
    pdf.chapter_title("14. Background Jobs (Cron Tasks)")
    pdf.body_text("Two background tasks run daily at midnight UTC via asyncio:")
    pdf.bullet("Auto-Suspend: Checks all active memberships. If end_date has passed, marks membership as expired and suspends the member (if no other active membership exists).")
    pdf.bullet("Expiration Reminders: Sends email reminders for memberships expiring in 1, 3, or 7 days. Only sends if the gym has SMTP configured.")
    pdf.body_text("Additionally, auto-suspend runs once on server startup to catch any expired memberships.")
    
    # ===== 15. DEPLOYMENT =====
    pdf.add_page()
    pdf.chapter_title("15. Deployment Guide (Plesk VPS)")
    
    pdf.chapter_title("Backend (c.ingresoqr.com)", level=2)
    pdf.code_block(
        "# 1. SSH into server\n"
        "ssh root@your-server\n\n"
        "# 2. Install dependencies\n"
        "apt install python3.11 python3.11-venv mongodb-org\n\n"
        "# 3. Create app directory\n"
        "mkdir -p /opt/gymaccess\n"
        "cd /opt/gymaccess\n\n"
        "# 4. Create virtual environment\n"
        "python3.11 -m venv venv\n"
        "source venv/bin/activate\n"
        "pip install -r requirements-prod.txt\n\n"
        "# 5. Configure .env\n"
        "cp .env.example .env\n"
        "# Edit MONGO_URL, JWT_SECRET, QR_SECRET, etc.\n\n"
        "# 6. Run with uvicorn\n"
        "nohup venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001 &\n\n"
        "# 7. Configure Nginx/Plesk proxy:\n"
        "#    c.ingresoqr.com -> proxy_pass http://127.0.0.1:8001"
    )
    
    pdf.chapter_title("Frontend (app.ingresoqr.com)", level=2)
    pdf.code_block(
        "# 1. Build locally (or download from Emergent)\n"
        "cd frontend\n"
        "REACT_APP_BACKEND_URL=https://c.ingresoqr.com yarn build\n\n"
        "# 2. Upload build/ folder to Plesk\n"
        "#    Go to app.ingresoqr.com in Plesk File Manager\n"
        "#    Upload contents of build/ to httpdocs/\n\n"
        "# 3. Add .htaccess for SPA routing:\n"
        "RewriteEngine On\n"
        "RewriteBase /\n"
        "RewriteRule ^index.html$ - [L]\n"
        "RewriteCond %{REQUEST_FILENAME} !-f\n"
        "RewriteCond %{REQUEST_FILENAME} !-d\n"
        "RewriteRule . /index.html [L]"
    )
    
    pdf.info_box("IMPORTANT", "The git clone command only syncs backend .py files. Frontend changes require rebuilding and manually uploading the build/ folder to Plesk.")
    
    # ===== 16. ENV VARIABLES =====
    pdf.add_page()
    pdf.chapter_title("16. Environment Variables")
    
    pdf.chapter_title("Backend (.env)", level=2)
    env_vars = [
        ["MONGO_URL", "MongoDB connection string", "mongodb://localhost:27017"],
        ["DB_NAME", "Database name", "gym_access"],
        ["JWT_SECRET", "Secret for JWT signing", "(random string)"],
        ["QR_SECRET", "Secret for QR HMAC signing", "(random string)"],
        ["STRIPE_API_KEY", "Global Stripe fallback key", "sk_live_..."],
        ["PLATFORM_STRIPE_KEY", "Stripe key for SaaS payments", "sk_live_..."],
        ["UPLOAD_DIR", "File upload directory", "/opt/gymaccess/uploads"],
    ]
    widths = [45, 75, 70]
    pdf.table_row(["Variable", "Description", "Default/Example"], widths, header=True)
    for v in env_vars:
        pdf.table_row(v, widths)
    
    pdf.ln(4)
    pdf.chapter_title("Frontend (.env)", level=2)
    pdf.code_block("REACT_APP_BACKEND_URL=https://c.ingresoqr.com")
    
    # ===== 17. TROUBLESHOOTING =====
    pdf.add_page()
    pdf.chapter_title("17. Troubleshooting & FAQ")
    
    issues = [
        ("'Algo salio mal' error in browser", 
         "This is the ErrorBoundary catching a React crash. Check browser console (F12) for the actual error. Common causes: missing data fields, division by zero, undefined variables."),
        ("Frontend changes not appearing in production",
         "The git clone/sync command ONLY updates backend Python files. You must rebuild the frontend (yarn build) and manually upload the build/ folder to Plesk."),
        ("QR code not validating at turnstile",
         "Check: 1) QR_SECRET matches between backend and .env 2) Time sync between Raspberry Pi and server 3) qr_refresh_seconds + 5s tolerance 4) Use /api/access/debug-qr to diagnose"),
        ("IP blocked after failed logins",
         "IPs are blocked after 5 failed attempts in 15 minutes. Super Admin can unblock from Security dashboard, or wait 15 minutes."),
        ("Stripe payments failing",
         "Check: 1) gym has stripe_secret_key set in Settings 2) Or STRIPE_API_KEY env variable exists 3) Key is valid (sk_live_ or sk_test_)"),
        ("Member suspended automatically",
         "The daily cron job auto-suspends members whose memberships have expired. Renew their membership to reactivate."),
        ("Raspberry Pi relay not activating",
         "Run test_gpio.py to verify GPIO wiring. Check: 1) Running as root 2) RPi.GPIO installed 3) Correct BCM pin numbers"),
        ("MongoDB connection error",
         "Verify MONGO_URL in .env. Check MongoDB is running: systemctl status mongod"),
    ]
    
    for title, solution in issues:
        pdf.chapter_title(title, level=3)
        pdf.body_text(solution)
    
    return pdf


def generate_spanish_doc():
    pdf = DocPDF(lang="es")
    pdf.alias_nb_pages()
    
    # ===== PORTADA =====
    pdf.add_page()
    pdf.ln(40)
    pdf.set_font("Helvetica", "B", 36)
    pdf.set_text_color(20, 20, 40)
    pdf.cell(0, 20, "IngresoQR", align="C")
    pdf.ln(18)
    pdf.set_font("Helvetica", "", 16)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 10, "Sistema Multi-Tenant de Control de Acceso", align="C")
    pdf.ln(8)
    pdf.cell(0, 10, "Documentacion Tecnica Completa", align="C")
    pdf.ln(20)
    pdf.set_draw_color(225, 255, 1)
    pdf.set_line_width(2)
    pdf.line(70, pdf.get_y(), 140, pdf.get_y())
    pdf.set_line_width(0.2)
    pdf.ln(20)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 8, "Version 2.0  |  Febrero 2026", align="C")
    pdf.ln(6)
    pdf.cell(0, 8, "FastAPI + React + MongoDB + Raspberry Pi", align="C")
    
    # ===== INDICE =====
    pdf.add_page()
    pdf.chapter_title("Indice de Contenido")
    toc = [
        "1. Vision General del Sistema",
        "2. Arquitectura y Stack Tecnologico",
        "3. Estructura del Proyecto (Arbol de Archivos)",
        "4. Roles de Usuario y Permisos",
        "5. Esquema de Base de Datos (Colecciones MongoDB)",
        "6. Referencia de API del Backend",
        "7. Paginas del Frontend y Rutas",
        "8. Autenticacion y Seguridad",
        "9. Sistema de Codigos QR (Dinamico y Estatico)",
        "10. Integracion Raspberry Pi / IoT",
        "11. Sistema de Pagos (Stripe y MercadoPago)",
        "12. Modelo SaaS Multi-Tenant",
        "13. Sistema de Email (SMTP por Gimnasio)",
        "14. Tareas en Segundo Plano (Cron)",
        "15. Guia de Despliegue (Plesk VPS)",
        "16. Variables de Entorno",
        "17. Resolucion de Problemas y FAQ",
    ]
    for item in toc:
        pdf.bullet(item, indent=5)
    
    # ===== 1. VISION GENERAL =====
    pdf.add_page()
    pdf.chapter_title("1. Vision General del Sistema")
    pdf.body_text(
        "IngresoQR es un sistema SaaS multi-tenant completo para el control de acceso en gimnasios. "
        "Proporciona a los propietarios de gimnasios una solucion integral para gestionar membresias, "
        "controlar el acceso fisico mediante codigos QR, procesar pagos, hacer seguimiento de asistencia "
        "y administrar clases. El sistema consta de tres componentes principales:"
    )
    pdf.bullet("Panel de Administracion: Interfaz web para que los administradores gestionen todos los aspectos del gimnasio")
    pdf.bullet("PWA para Socios: Aplicacion Web Progresiva para que los socios accedan a su QR, reserven clases y vean estadisticas")
    pdf.bullet("Controlador Raspberry Pi: Dispositivo IoT que lee codigos QR y controla los torniquetes de entrada/salida mediante reles GPIO")
    
    pdf.chapter_title("Funcionalidades Principales", level=2)
    features = [
        "Codigos QR dinamicos que se refrescan cada 5/10/15 segundos (configurable por gimnasio)",
        "Modo QR estatico para socios con problemas de conectividad",
        "Anti-passback: Alterna automaticamente entre entrada y salida",
        "Roles multi-nivel: Super Admin, Gym Admin, Gestor, Entrenador, Socio",
        "Integracion con Stripe y MercadoPago (claves API por gimnasio)",
        "Gestion de planes SaaS con 12 flags de funcionalidades configurables",
        "Programacion de clases con patrones recurrentes y sistema de reservas",
        "TPV (Punto de Venta) para inventario de productos y ventas",
        "Gamificacion con insignias y rachas",
        "Rutinas personalizadas asignadas por entrenadores a socios",
        "Formularios de registro personalizados por gimnasio",
        "Sistema de pases de invitados con acceso QR",
        "Sistema de email SMTP (configurable por gimnasio)",
        "Dashboard de analiticas con mapas de calor horarios y metricas de retencion",
        "Exportacion Excel de datos de socios",
        "Informes de ventas en PDF",
        "Seguridad: Bloqueo de IP tras intentos fallidos de login",
        "Gestion de dispositivos de socios (limitar dispositivos por socio)",
        "Modo kiosko para auto-registro en el gimnasio",
        "Soporte de tema oscuro/claro",
    ]
    for f in features:
        pdf.bullet(f)
    
    # ===== 2. ARQUITECTURA =====
    pdf.add_page()
    pdf.chapter_title("2. Arquitectura y Stack Tecnologico")
    
    pdf.chapter_title("Backend", level=2)
    pdf.bullet("Framework: FastAPI (Python 3.11+)")
    pdf.bullet("Base de datos: MongoDB (via Motor async driver)")
    pdf.bullet("Autenticacion: JWT (python-jose + bcrypt)")
    pdf.bullet("Servidor ASGI: Uvicorn")
    pdf.bullet("Almacenamiento de archivos: Sistema de archivos local (/opt/gymaccess/uploads)")
    pdf.bullet("Email: aiosmtplib (SMTP asincrono)")
    pdf.bullet("Pagos: Stripe SDK, MercadoPago SDK")
    pdf.bullet("Excel: openpyxl")
    
    pdf.chapter_title("Frontend", level=2)
    pdf.bullet("Framework: React 18 (Create React App)")
    pdf.bullet("Estilos: Tailwind CSS + variables CSS personalizadas para temas")
    pdf.bullet("Componentes UI: Shadcn/UI (basados en Radix)")
    pdf.bullet("Cliente HTTP: Axios")
    pdf.bullet("Enrutamiento: React Router v6")
    pdf.bullet("Notificaciones: Sonner")
    pdf.bullet("Fuentes: Chivo (titulos) + Manrope (cuerpo)")
    pdf.bullet("Iconos: Lucide React")
    
    pdf.chapter_title("IoT (Raspberry Pi)", level=2)
    pdf.bullet("Hardware: Raspberry Pi 3B+ con modulo de 2 reles")
    pdf.bullet("Escaner QR: Escaner USB de codigos de barras/QR (emulacion de teclado HID)")
    pdf.bullet("GPIO: Modo BCM, Pin 12 (rele entrada), Pin 16 (rele salida)")
    pdf.bullet("Librerias: RPi.GPIO, evdev, requests, python-dotenv")
    
    pdf.chapter_title("Flujo de Comunicacion", level=2)
    pdf.body_text(
        "1. Socio abre la PWA -> Frontend solicita QR al backend -> Backend genera QR firmado con HMAC\n"
        "2. Socio muestra QR en el torniquete -> Escaner del Raspberry Pi lee el QR\n"
        "3. Raspberry Pi envia QR a POST /api/access/validate\n"
        "4. Backend valida firma, verifica membresia, registra log de acceso\n"
        "5. Backend responde valido/invalido -> Raspberry Pi activa rele de entrada o salida por 3 segundos"
    )
    
    # ===== 3. ESTRUCTURA =====
    pdf.add_page()
    pdf.chapter_title("3. Estructura del Proyecto")
    pdf.code_block(
        "/app\n"
        "|-- backend/\n"
        "|   |-- server.py              # App FastAPI, routers, tareas inicio\n"
        "|   |-- models.py              # Modelos Pydantic de peticiones\n"
        "|   |-- auth.py                # JWT, hash passwords, checks de rol\n"
        "|   |-- database.py            # Conexion MongoDB (Motor)\n"
        "|   |-- qr_utils.py            # Generacion y validacion QR (HMAC)\n"
        "|   |-- storage.py             # Helper almacenamiento local\n"
        "|   |-- requirements.txt       # Dependencias Python\n"
        "|   |-- .env                   # Variables de entorno\n"
        "|   |-- routes/\n"
        "|   |   |-- auth_routes.py         # Login, registro, perfil\n"
        "|   |   |-- gym_routes.py          # CRUD gimnasios, capacidad\n"
        "|   |   |-- member_routes.py       # CRUD socios, exportar Excel\n"
        "|   |   |-- plan_routes.py         # Planes de membresia\n"
        "|   |   |-- access_routes.py       # QR, validar, logs acceso\n"
        "|   |   |-- device_routes.py       # Registro dispositivos IoT\n"
        "|   |   |-- payment_routes.py      # Stripe checkout, webhooks\n"
        "|   |   |-- mercadopago_routes.py  # Integracion MercadoPago\n"
        "|   |   |-- class_routes.py        # Clases, horarios, reservas\n"
        "|   |   |-- saas_routes.py         # Planes SaaS, suscripciones\n"
        "|   |   |-- pos_routes.py          # Productos, ventas, TPV\n"
        "|   |   |-- accounting_routes.py   # Informes financieros, PDF\n"
        "|   |   |-- analytics_routes.py    # Mapas calor, retencion\n"
        "|   |   |-- notification_guest_routes.py  # Notificaciones e invitados\n"
        "|   |   |-- security_routes.py     # Bloqueo IP, intentos login\n"
        "|   |   |-- upload_routes.py       # Avatar, logo, imagenes\n"
        "|   |   |-- form_routes.py         # Formularios personalizados\n"
        "|   |   |-- gamification_routes.py # Insignias y rachas\n"
        "|   |   |-- routine_routes.py      # Rutinas de entrenamiento\n"
        "|   |   |-- misc_routes.py         # Email, dashboard, descargas\n"
        "|   |-- downloads/             # Scripts descargables\n"
        "|   |-- tests/                 # Tests con Pytest\n"
        "|-- frontend/\n"
        "|   |-- src/\n"
        "|   |   |-- App.js             # Router principal\n"
        "|   |   |-- App.css            # Estilos globales + variables CSS\n"
        "|   |   |-- context/AuthContext.js  # Estado de autenticacion\n"
        "|   |   |-- lib/api.js         # Funciones API con Axios\n"
        "|   |   |-- lib/utils.js       # Funciones utilitarias\n"
        "|   |   |-- components/        # Componentes reutilizables\n"
        "|   |   |-- layouts/           # Layouts Admin y PWA\n"
        "|   |   |-- pages/admin/       # 28 paginas del panel admin\n"
        "|   |   |-- pages/pwa/         # 14 paginas de la PWA socio\n"
        "|   |-- build/                 # Build de produccion\n"
    )
    
    # ===== 4. ROLES =====
    pdf.add_page()
    pdf.chapter_title("4. Roles de Usuario y Permisos")
    
    roles = [
        ["super_admin", "null", "Control total de la plataforma. Gestiona gimnasios, planes SaaS, dispositivos."],
        ["gym_admin", "UUID", "Control total de su gimnasio. Socios, planes, pagos, clases, config."],
        ["gym_manager", "UUID", "Permisos configurables. Subconjunto de gym_admin."],
        ["trainer", "UUID", "Gestiona clases asignadas. Crea rutinas. Dashboard propio."],
        ["member", "UUID", "Accede a la PWA. Ve QR, reserva clases, perfil."],
    ]
    widths = [30, 20, 140]
    pdf.table_row(["Rol", "gym_id", "Descripcion"], widths, header=True)
    for r in roles:
        pdf.table_row(r, widths)
    
    pdf.ln(4)
    pdf.chapter_title("Permisos del Gestor (Configurables)", level=2)
    perms = [
        ["members_view", "Ver lista de socios"],
        ["members_create", "Crear nuevos socios"],
        ["members_edit", "Editar datos de socios"],
        ["members_delete", "Eliminar socios"],
        ["members_suspend", "Suspender/Reactivar socios"],
        ["payments_register", "Registrar pagos manuales"],
        ["pos_sell", "Procesar ventas TPV"],
        ["pos_products", "Gestionar productos TPV"],
        ["access_view", "Ver logs de acceso"],
        ["classes_manage", "Gestionar clases y horarios"],
        ["data_export", "Exportar datos (Excel)"],
        ["notifications_send", "Enviar notificaciones"],
    ]
    widths = [50, 140]
    pdf.table_row(["Clave Permiso", "Descripcion"], widths, header=True)
    for p in perms:
        pdf.table_row(p, widths)
    
    # ===== 5. BASE DE DATOS =====
    pdf.add_page()
    pdf.chapter_title("5. Esquema de Base de Datos (MongoDB)")
    pdf.body_text("MongoDB es la base de datos principal. Todos los documentos usan un campo 'id' UUID string como clave primaria (no ObjectId). El campo '_id' siempre se excluye de las respuestas API.")
    
    collections_es = [
        ("admins", "Usuarios administradores (super_admin, gym_admin, gym_manager, trainer)", 
         "id, email, password (bcrypt), name, role, gym_id, permissions[], active, created_at"),
        ("gyms", "Gimnasios (tenants)", 
         "id, name, address, phone, email, logo_url, primary_color, qr_refresh_seconds, qr_mode, max_members, api_token, stripe_secret_key, currency, smtp_*, saas_plan_id, status, created_at"),
        ("members", "Socios del gimnasio", 
         "id, email, name, phone, code (6 chars), gym_id, status, gender, avatar_path, qr_mode, suspension_reason, can_bring_guests, created_at"),
        ("plans", "Planes de membresia", 
         "id, gym_id, name, description, price, duration_days, access_type, active, created_at"),
        ("memberships", "Membresias activas/vencidas", 
         "id, member_id, plan_id, gym_id, start_date, end_date, status (active/expired), payment_id, created_at"),
        ("access_logs", "Registros de entrada/salida", 
         "id, member_id, member_name, member_code, gym_id, direction (entrada/salida), timestamp, is_guest"),
        ("payment_transactions", "Registros de pagos", 
         "id, session_id, member_id, plan_id, gym_id, amount, currency, status, payment_method, created_at"),
        ("classes", "Definiciones de clases", 
         "id, gym_id, name, trainer_id, max_capacity, duration_minutes, recurring, days_of_week[], start_time, end_date, active"),
        ("class_schedules", "Horarios individuales de clases", 
         "id, class_id, gym_id, date, start_time, end_time, max_capacity, current_bookings, status"),
        ("bookings", "Reservas de clases por socios", 
         "id, member_id, schedule_id, class_id, gym_id, date, status, checked_in, checked_in_at"),
        ("devices", "Dispositivos IoT registrados", 
         "id, gym_id, name, location, status, last_ping, created_at"),
        ("notifications", "Notificaciones del gimnasio para socios", 
         "id, gym_id, title, message, target, read_by[], created_at"),
        ("guests", "Pases de invitados", 
         "id, code, name, invited_by, gym_id, valid_until, status, accesses, created_at"),
        ("saas_plans", "Planes SaaS de la plataforma", 
         "id, name, max_members, has_qr_access, has_classes, has_pos, ... (12 flags), price_monthly, currency, active"),
        ("pos_products", "Inventario de productos TPV", 
         "id, gym_id, name, cost_price, sale_price, stock, category, active"),
        ("pos_sales", "Transacciones de ventas TPV", 
         "id, gym_id, items[], total, payment_method, registered_by, created_at"),
        ("email_logs", "Historial de emails enviados", 
         "id, gym_id, member_id, to_email, subject, status, sent_at"),
        ("routines", "Rutinas de entrenamiento", 
         "id, gym_id, trainer_id, member_id, name, days[], active"),
        ("broadcasts", "Anuncios de la plataforma (Super Admin)", 
         "id, title, message, priority, active, dismissed_by[]"),
        ("blocked_ips", "IPs bloqueadas por fuerza bruta", 
         "ip, blocked_until, reason, blocked_at"),
    ]
    
    for name, desc, fields in collections_es:
        pdf.chapter_title(f"Coleccion: {name}", level=3)
        pdf.body_text(desc)
        pdf.set_font("Courier", "", 8)
        safe = fields.encode('latin-1', 'replace').decode('latin-1')
        pdf.set_fill_color(240, 240, 245)
        pdf.multi_cell(0, 4.5, safe, fill=True)
        pdf.ln(3)
    
    # ===== 6. API =====
    pdf.add_page()
    pdf.chapter_title("6. Referencia de API del Backend")
    pdf.body_text("Todos los endpoints estan prefijados con /api. La autenticacion es via Bearer JWT token en el header Authorization, excepto los marcados como publicos.")
    
    api_sections = [
        ("Autenticacion", [
            ("POST", "/api/auth/admin/register", "Registrar nuevo admin"),
            ("POST", "/api/auth/admin/login", "Login admin, devuelve JWT"),
            ("POST", "/api/auth/admin/impersonate/{gym_id}", "Super Admin suplanta Gym Admin"),
            ("PUT", "/api/auth/admin/update-profile", "Actualizar email/password"),
            ("POST", "/api/auth/member/login?code=XXX", "Login socio por codigo"),
            ("GET", "/api/auth/member/me", "Perfil socio actual + gym + membresia"),
        ]),
        ("Gimnasios", [
            ("POST", "/api/gyms", "Crear gimnasio (+ admin opcional)"),
            ("GET", "/api/gyms", "Listar gimnasios (filtrado por rol)"),
            ("PUT", "/api/gyms/{id}", "Actualizar configuracion"),
            ("DELETE", "/api/gyms/{id}", "Eliminar gimnasio + datos"),
            ("PUT", "/api/gyms/{id}/suspend", "Suspender/Reactivar"),
            ("GET", "/api/gyms/{id}/capacity", "Stats de capacidad"),
            ("GET", "/api/gyms/{id}/public-info", "Publico: nombre, logo, pagos"),
        ]),
        ("Socios", [
            ("POST", "/api/members", "Crear socio (admin)"),
            ("POST", "/api/members/register", "Auto-registro publico"),
            ("GET", "/api/members", "Listar socios"),
            ("PUT", "/api/members/{id}", "Actualizar socio"),
            ("POST", "/api/members/{id}/suspend", "Suspender con motivo"),
            ("DELETE", "/api/members/{id}", "Eliminar socio"),
            ("GET", "/api/members/export/excel", "Exportar a .xlsx"),
        ]),
        ("Planes y Membresias", [
            ("POST", "/api/plans", "Crear plan"),
            ("GET", "/api/plans", "Listar planes"),
            ("POST", "/api/memberships", "Asignar membresia"),
            ("GET", "/api/memberships/expiring", "Membresias por vencer"),
        ]),
        ("Acceso y QR", [
            ("GET", "/api/qr/generate", "Generar QR del socio logueado"),
            ("POST", "/api/access/validate", "PUBLICO: Validar QR (Raspberry Pi)"),
            ("GET", "/api/access/logs", "Logs de acceso"),
            ("GET", "/api/access/stats", "Estadisticas de acceso"),
            ("GET", "/api/access/stats/daily", "Accesos diarios"),
            ("GET", "/api/access/stats/hourly", "Distribucion horaria"),
        ]),
        ("Pagos", [
            ("POST", "/api/payments/checkout", "Crear sesion Stripe"),
            ("GET", "/api/payments/status/{session_id}", "Estado del pago"),
            ("POST", "/api/payments/manual", "Registrar pago manual"),
            ("GET", "/api/payments/history", "Historial de pagos"),
            ("PUT", "/api/gyms/{id}/stripe-config", "Actualizar clave Stripe"),
        ]),
        ("Clases y Reservas", [
            ("POST", "/api/classes", "Crear clase"),
            ("GET", "/api/classes", "Listar clases"),
            ("PUT", "/api/classes/{id}", "Editar clase (regenera horarios)"),
            ("DELETE", "/api/classes/{id}", "Eliminar clase + horarios"),
            ("POST", "/api/bookings", "Reservar clase (socio)"),
            ("POST", "/api/bookings/{id}/checkin", "Check-in de asistencia"),
            ("POST", "/api/classes/cleanup-stale-schedules", "Limpiar horarios huerfanos"),
        ]),
        ("Gestion SaaS", [
            ("POST", "/api/saas/plans", "Crear plan SaaS"),
            ("PUT", "/api/saas/plans/{id}", "Editar plan SaaS"),
            ("PUT", "/api/gyms/{id}/saas-plan", "Asignar plan SaaS a gym"),
            ("GET", "/api/gyms/{id}/saas-features", "Features activas del gym"),
            ("POST", "/api/saas/subscribe", "Suscribirse a plan SaaS"),
        ]),
        ("TPV (Punto de Venta)", [
            ("POST", "/api/pos/products", "Crear producto"),
            ("POST", "/api/pos/sales", "Registrar venta"),
            ("GET", "/api/pos/stats", "Estadisticas TPV"),
        ]),
        ("Seguridad", [
            ("GET", "/api/security/blocked-ips", "IPs bloqueadas"),
            ("DELETE", "/api/security/blocked-ips/{ip}", "Desbloquear IP"),
            ("GET", "/api/security/login-attempts", "Intentos de login"),
        ]),
    ]
    
    for section_name, endpoints in api_sections:
        pdf.chapter_title(section_name, level=2)
        widths = [15, 75, 100]
        pdf.table_row(["Metodo", "Endpoint", "Descripcion"], widths, header=True)
        for method, endpoint, desc in endpoints:
            safe_ep = endpoint.encode('latin-1', 'replace').decode('latin-1')
            safe_desc = desc.encode('latin-1', 'replace').decode('latin-1')
            pdf.table_row([method, safe_ep, safe_desc], widths)
        pdf.ln(4)
    
    # ===== 7-17 SECTIONS (Spanish equivalents) =====
    
    # 7. Frontend
    pdf.add_page()
    pdf.chapter_title("7. Paginas del Frontend y Rutas")
    
    pdf.chapter_title("Panel Admin (/admin/*)", level=2)
    admin_pages = [
        ["/admin/login", "AdminLogin.js", "Formulario de login admin"],
        ["/admin", "AdminDashboard.js", "Dashboard principal con estadisticas"],
        ["/admin/gyms", "AdminGyms.js", "Gestion de gimnasios"],
        ["/admin/members", "AdminMembers.js", "Gestion de socios"],
        ["/admin/plans", "AdminPlans.js", "Planes de membresia"],
        ["/admin/classes", "AdminClasses.js", "Gestion de clases"],
        ["/admin/attendance", "AdminAttendance.js", "Asistencia a clases"],
        ["/admin/schedules", "AdminSchedules.js", "Calendario de horarios"],
        ["/admin/staff", "AdminStaff.js", "Gestion de personal"],
        ["/admin/access", "AdminAccess.js", "Visor de logs de acceso"],
        ["/admin/devices", "AdminDevices.js", "Gestion dispositivos IoT"],
        ["/admin/notifications", "AdminNotifications.js", "Notificaciones"],
        ["/admin/guests", "AdminGuests.js", "Pases de invitados"],
        ["/admin/accounting", "AdminAccounting.js", "Informes financieros"],
        ["/admin/pos", "AdminPOS.js", "Punto de Venta"],
        ["/admin/analytics", "AdminAnalytics.js", "Analiticas avanzadas"],
        ["/admin/saas-plans", "AdminSaaSPlans.js", "Config planes SaaS"],
        ["/admin/settings", "AdminSettings.js", "Configuracion del gym"],
        ["/admin/security", "AdminSecurity.js", "Dashboard de seguridad"],
    ]
    widths = [45, 50, 95]
    pdf.table_row(["Ruta", "Componente", "Descripcion"], widths, header=True)
    for p in admin_pages:
        pdf.table_row(p, widths)
    
    pdf.ln(4)
    pdf.chapter_title("PWA Socios (/app/*)", level=2)
    pwa_pages = [
        ["/app/login", "MemberLogin.js", "Login con codigo de socio"],
        ["/app", "MemberHome.js", "QR + acceso rapido"],
        ["/app/classes", "MemberClasses.js", "Reservar clases"],
        ["/app/history", "MemberHistory.js", "Historial de accesos"],
        ["/app/stats", "MemberStats.js", "Estadisticas personales"],
        ["/app/membership", "MemberMembership.js", "Detalles membresia + pagar"],
        ["/app/guests", "MemberGuests.js", "Invitar invitados"],
        ["/app/achievements", "MemberGamification.js", "Insignias y rachas"],
        ["/app/routines", "MemberRoutines.js", "Rutinas de entrenamiento"],
        ["/app/profile", "MemberProfile.js", "Configuracion de perfil"],
    ]
    widths = [45, 50, 95]
    pdf.table_row(["Ruta", "Componente", "Descripcion"], widths, header=True)
    for p in pwa_pages:
        pdf.table_row(p, widths)
    
    # 8. Auth & Security
    pdf.add_page()
    pdf.chapter_title("8. Autenticacion y Seguridad")
    pdf.chapter_title("Autenticacion JWT", level=2)
    pdf.body_text("Se usan tokens JWT con algoritmo HS256. Los tokens expiran tras 24 horas. El payload contiene: sub (ID usuario), role, gym_id.")
    
    pdf.chapter_title("Bloqueo de IP (Proteccion Fuerza Bruta)", level=2)
    pdf.body_text("Tras 5 intentos fallidos desde la misma IP en 15 minutos, la IP se bloquea 15 minutos. Aplica a login de admin y socio. El Super Admin puede desbloquear desde el dashboard de Seguridad.")
    
    pdf.chapter_title("Suplantacion", level=2)
    pdf.body_text("El Super Admin puede suplantar a cualquier Gym Admin via POST /api/auth/admin/impersonate/{gym_id}. Esto crea un JWT especial con impersonating=true.")
    
    # 9. QR
    pdf.add_page()
    pdf.chapter_title("9. Sistema de Codigos QR")
    pdf.chapter_title("QR Dinamico", level=2)
    pdf.body_text("Los QR dinamicos se regeneran cada N segundos (configurable: 5, 10 o 15). Cada QR contiene: member_id, gym_id, timestamp Unix, firma HMAC-SHA256 (16 chars hex). Los datos se codifican en base64url.")
    
    pdf.chapter_title("QR Estatico", level=2)
    pdf.body_text("Para socios con mala conectividad, el Super Admin puede asignar modo QR estatico. Estos QR no expiran (sin verificacion de timestamp).")
    
    pdf.chapter_title("Anti-Passback", level=2)
    pdf.body_text("El sistema implementa anti-passback automatico verificando el ultimo log de acceso del socio. Si el ultimo fue 'entrada', el siguiente sera 'salida' y viceversa.")
    
    # 10. Raspberry Pi
    pdf.add_page()
    pdf.chapter_title("10. Integracion Raspberry Pi")
    pdf.chapter_title("Requisitos de Hardware", level=2)
    pdf.bullet("Raspberry Pi 3B+ o superior")
    pdf.bullet("Modulo de 2 reles (5V)")
    pdf.bullet("Escaner QR USB (modo HID - actua como teclado)")
    pdf.bullet("Cableado: GPIO 12 -> Rele entrada, GPIO 16 -> Rele salida")
    
    pdf.chapter_title("Configuracion de Software", level=2)
    pdf.code_block(
        "# /opt/gymaccess/.env\n"
        "GYMACCESS_SERVER_URL=https://c.ingresoqr.com\n"
        "GYMACCESS_GYM_TOKEN=tu_token_del_gimnasio\n"
        "GYMACCESS_DEVICE_ID=tu_device_uuid\n"
        "GYMACCESS_RELAY_ENTRADA=12\n"
        "GYMACCESS_RELAY_SALIDA=16"
    )
    
    pdf.chapter_title("Flujo de Operacion", level=2)
    pdf.body_text(
        "1. El script usa evdev para leer escaners QR USB como dispositivos de entrada\n"
        "2. Se pueden configurar multiples escaners via scanner_map.json\n"
        "3. Al escanear un QR, envia POST a /api/access/validate\n"
        "4. Si es valido: activa el rele correspondiente por 3 segundos\n"
        "5. Ping de heartbeat cada 60 segundos a /api/devices/{id}/ping"
    )
    
    # 11. Pagos
    pdf.add_page()
    pdf.chapter_title("11. Sistema de Pagos")
    pdf.chapter_title("Stripe", level=2)
    pdf.body_text("Cada gimnasio puede configurar su propia clave secreta de Stripe. Si no tiene, se usa la variable STRIPE_API_KEY global. Los pagos usan Stripe Checkout Sessions.")
    
    pdf.chapter_title("MercadoPago", level=2)
    pdf.body_text("Cada gimnasio puede configurar su propio access token de MercadoPago para mercados latinoamericanos.")
    
    pdf.chapter_title("Pagos Manuales", level=2)
    pdf.body_text("Los admins pueden registrar pagos manuales (efectivo, tarjeta, transferencia) que activan inmediatamente la membresia.")
    
    # 12. SaaS
    pdf.add_page()
    pdf.chapter_title("12. Modelo SaaS Multi-Tenant")
    pdf.body_text("La plataforma opera como SaaS donde cada gimnasio es un tenant. El Super Admin crea planes SaaS con flags de funcionalidades configurables. Cada gimnasio se asigna a un plan que determina sus funcionalidades.")
    
    pdf.chapter_title("Feature Flags (12 toggles)", level=2)
    flags = [
        ["has_qr_access", "Control de acceso QR"],
        ["has_guest_passes", "Sistema de invitados"],
        ["has_classes", "Programacion de clases y reservas"],
        ["has_pos", "Punto de Venta (TPV)"],
        ["has_analytics", "Dashboard de analiticas avanzadas"],
        ["has_gamification", "Sistema de insignias y rachas"],
        ["has_routines", "Rutinas de entrenamiento"],
        ["has_email_smtp", "Envio de emails SMTP personalizado"],
        ["has_stripe_members", "Pagos Stripe para socios"],
        ["has_mercadopago", "Pagos MercadoPago"],
        ["has_iframes", "Widgets embebibles (iframes)"],
        ["has_advanced_accounting", "Informes contables avanzados"],
    ]
    widths = [55, 135]
    pdf.table_row(["Clave", "Descripcion"], widths, header=True)
    for f in flags:
        pdf.table_row(f, widths)
    
    # 13-17
    pdf.add_page()
    pdf.chapter_title("13. Sistema de Email")
    pdf.body_text("Cada gimnasio configura su propio servidor SMTP en Configuracion. El sistema envia: emails de bienvenida, recordatorios de vencimiento (1, 3, 7 dias), confirmaciones de pago, y emails con plantillas editables.")
    
    pdf.chapter_title("14. Tareas en Segundo Plano")
    pdf.body_text("Dos tareas ejecutan diariamente a medianoche UTC via asyncio:\n- Auto-Suspender: Verifica membresias activas vencidas y suspende socios.\n- Recordatorios: Envia emails a socios con membresias por vencer en 1, 3 o 7 dias.")
    
    pdf.add_page()
    pdf.chapter_title("15. Guia de Despliegue (Plesk VPS)")
    pdf.chapter_title("Backend (c.ingresoqr.com)", level=2)
    pdf.code_block(
        "# 1. SSH al servidor\n"
        "ssh root@tu-servidor\n\n"
        "# 2. Instalar dependencias\n"
        "apt install python3.11 python3.11-venv mongodb-org\n\n"
        "# 3. Crear directorio de la app\n"
        "mkdir -p /opt/gymaccess && cd /opt/gymaccess\n\n"
        "# 4. Entorno virtual\n"
        "python3.11 -m venv venv\n"
        "source venv/bin/activate\n"
        "pip install -r requirements-prod.txt\n\n"
        "# 5. Configurar .env (MONGO_URL, JWT_SECRET, QR_SECRET)\n\n"
        "# 6. Ejecutar\n"
        "nohup venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001 &\n\n"
        "# 7. Configurar proxy Nginx/Plesk:\n"
        "#    c.ingresoqr.com -> proxy_pass http://127.0.0.1:8001"
    )
    
    pdf.chapter_title("Frontend (app.ingresoqr.com)", level=2)
    pdf.body_text("El comando git clone SOLO actualiza archivos del backend (.py). Para cambios en el frontend, debes reconstruir (yarn build) y subir manualmente la carpeta build/ a Plesk.")
    
    pdf.add_page()
    pdf.chapter_title("16. Variables de Entorno")
    env_vars = [
        ["MONGO_URL", "Cadena de conexion MongoDB"],
        ["DB_NAME", "Nombre de la base de datos"],
        ["JWT_SECRET", "Secreto para firma JWT"],
        ["QR_SECRET", "Secreto para firma HMAC de QR"],
        ["STRIPE_API_KEY", "Clave Stripe global (fallback)"],
        ["PLATFORM_STRIPE_KEY", "Clave Stripe para pagos SaaS"],
        ["UPLOAD_DIR", "Directorio de subida de archivos"],
        ["REACT_APP_BACKEND_URL", "URL del backend (frontend)"],
    ]
    widths = [55, 135]
    pdf.table_row(["Variable", "Descripcion"], widths, header=True)
    for v in env_vars:
        pdf.table_row(v, widths)
    
    pdf.chapter_title("17. Resolucion de Problemas")
    issues = [
        ("Error 'Algo salio mal' en el navegador", 
         "Es el ErrorBoundary capturando un crash de React. Revisa la consola del navegador (F12) para el error real."),
        ("Cambios del frontend no aparecen en produccion",
         "El comando git clone SOLO actualiza archivos Python del backend. Debes reconstruir el frontend (yarn build) y subir la carpeta build/ manualmente a Plesk."),
        ("QR no valida en el torniquete",
         "Verificar: 1) QR_SECRET coincide 2) Sincronizacion de hora 3) Usar /api/access/debug-qr para diagnosticar"),
        ("Socio suspendido automaticamente",
         "El cron diario auto-suspende socios con membresias vencidas. Renovar membresia para reactivar."),
    ]
    for title, solution in issues:
        pdf.chapter_title(title, level=3)
        pdf.body_text(solution)
    
    return pdf


if __name__ == "__main__":
    output_dir = "/app/backend/downloads"
    os.makedirs(output_dir, exist_ok=True)
    
    print("Generating English documentation...")
    en_pdf = generate_english_doc()
    en_path = os.path.join(output_dir, "IngresoQR_Documentation_EN.pdf")
    en_pdf.output(en_path)
    print(f"  -> {en_path}")
    
    print("Generating Spanish documentation...")
    es_pdf = generate_spanish_doc()
    es_path = os.path.join(output_dir, "IngresoQR_Documentacion_ES.pdf")
    es_pdf.output(es_path)
    print(f"  -> {es_path}")
    
    print("Done! Both PDFs generated successfully.")
