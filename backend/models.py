from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional

class GymCreate(BaseModel):
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    logo_url: Optional[str] = None
    primary_color: str = "#E1FF01"
    qr_refresh_seconds: int = 10
    max_members: Optional[int] = None
    business_type: str = "gym"
    admin_email: Optional[EmailStr] = None
    admin_password: Optional[str] = None
    admin_name: Optional[str] = None

class GymUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    bg_color: Optional[str] = None
    menu_color: Optional[str] = None
    text_color: Optional[str] = None
    qr_refresh_seconds: Optional[int] = None
    qr_mode: Optional[str] = None
    max_members: Optional[int] = None
    business_type: Optional[str] = None
    custom_domain: Optional[str] = None
    stripe_secret_key: Optional[str] = None
    stripe_currency: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: Optional[str] = None
    currency: Optional[str] = None
    mercadopago_access_token: Optional[str] = None
    auto_approve_members: Optional[bool] = None
    show_pwa_install_prompt: Optional[bool] = None

class AdminCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str = "gym_admin"
    gym_id: Optional[str] = None

class AdminLogin(BaseModel):
    email: EmailStr
    password: str

class MemberCreate(BaseModel):
    email: EmailStr
    name: str
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    gym_id: str
    gender: Optional[str] = None  # male, female, prefer_not_to_say

class MemberPublicRegister(BaseModel):
    email: EmailStr
    name: str
    phone: Optional[str] = None
    gym_id: str
    plan_id: Optional[str] = None
    gender: Optional[str] = None  # male, female, prefer_not_to_say
    form_responses: Optional[dict] = None  # Custom form answers

class MemberUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    status: Optional[str] = None
    can_bring_guests: Optional[bool] = None
    max_guests_per_month: Optional[int] = None
    suspension_reason: Optional[str] = None
    gender: Optional[str] = None

class PlanCreate(BaseModel):
    gym_id: str
    name: str
    description: Optional[str] = None
    price: float
    duration_days: int
    access_type: str = "unlimited"

class MembershipCreate(BaseModel):
    member_id: str
    plan_id: str

class AccessValidation(BaseModel):
    qr_code: str
    gym_token: str
    direction: str

class DeviceCreate(BaseModel):
    gym_id: str
    name: str
    location: Optional[str] = None

class EmailTemplateUpdate(BaseModel):
    subject: str
    body: str

class ManualPayment(BaseModel):
    member_id: str
    plan_id: str
    payment_method: str
    amount: float
    notes: Optional[str] = None

class ClassCreate(BaseModel):
    gym_id: str
    name: str
    description: Optional[str] = None
    trainer_id: Optional[str] = None
    max_capacity: int = 20
    duration_minutes: int = 60
    class_type: str = "group"
    recurring: bool = False
    days_of_week: Optional[List[int]] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    single_date: Optional[str] = None
    single_start_time: Optional[str] = None

class ClassUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    trainer_id: Optional[str] = None
    max_capacity: Optional[int] = None
    duration_minutes: Optional[int] = None
    class_type: Optional[str] = None
    recurring: Optional[bool] = None
    days_of_week: Optional[List[int]] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    active: Optional[bool] = None

class ClassScheduleCreate(BaseModel):
    class_id: str
    date: str
    start_time: str
    end_time: str
    trainer_id: Optional[str] = None
    max_capacity: Optional[int] = None

class BookingCreate(BaseModel):
    schedule_id: str

class TrainerCreate(BaseModel):
    gym_id: str
    email: EmailStr
    password: str
    name: str
    phone: Optional[str] = None
    specialties: Optional[List[str]] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None

class NotificationCreate(BaseModel):
    gym_id: str
    title: str
    message: str
    notification_type: str = "general"
    target: str = "all"

class GuestCreate(BaseModel):
    name: str
    phone: Optional[str] = None
    valid_days: int = 1

# ==================== SaaS Plan Models ====================

class SaaSPlanCreate(BaseModel):
    name: str
    max_members: int = 500
    has_qr_access: bool = True
    has_guest_passes: bool = False
    has_classes: bool = False
    has_pos: bool = False
    has_analytics: bool = False
    has_gamification: bool = False
    has_routines: bool = False
    has_email_smtp: bool = False
    has_stripe_members: bool = False
    has_mercadopago: bool = False
    has_iframes: bool = False
    has_advanced_accounting: bool = False
    price_monthly: float = 0
    currency: str = "EUR"
    description: Optional[str] = None

class SaaSPlanUpdate(BaseModel):
    name: Optional[str] = None
    max_members: Optional[int] = None
    has_qr_access: Optional[bool] = None
    has_guest_passes: Optional[bool] = None
    has_classes: Optional[bool] = None
    has_pos: Optional[bool] = None
    has_analytics: Optional[bool] = None
    has_gamification: Optional[bool] = None
    has_routines: Optional[bool] = None
    has_email_smtp: Optional[bool] = None
    has_stripe_members: Optional[bool] = None
    has_mercadopago: Optional[bool] = None
    has_iframes: Optional[bool] = None
    has_advanced_accounting: Optional[bool] = None
    price_monthly: Optional[float] = None
    currency: Optional[str] = None
    description: Optional[str] = None

# ==================== POS Models ====================

class ProductCreate(BaseModel):
    gym_id: str
    name: str
    description: Optional[str] = None
    cost_price: float = 0
    sale_price: float
    stock: int = 0
    category: Optional[str] = None
    barcode: Optional[str] = None

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    cost_price: Optional[float] = None
    sale_price: Optional[float] = None
    stock: Optional[int] = None
    category: Optional[str] = None
    barcode: Optional[str] = None
    active: Optional[bool] = None

class SaleItem(BaseModel):
    product_id: str
    quantity: int
    unit_price: float

class SaleCreate(BaseModel):
    gym_id: str
    items: List[SaleItem]
    payment_method: str  # cash, card, mercadopago
    member_id: Optional[str] = None
    notes: Optional[str] = None

class CashWithdrawalCreate(BaseModel):
    gym_id: str
    amount: float
    reason: str
    notes: Optional[str] = None

class BroadcastCreate(BaseModel):
    title: str
    message: str
    priority: str = "normal"  # normal, urgent


# ==================== Custom Form Models ====================

class FormFieldCreate(BaseModel):
    label: str
    field_type: str = "text"  # text, textarea, select, checkbox, number
    required: bool = False
    options: Optional[List[str]] = None  # For select type
    placeholder: Optional[str] = None

class CustomFormCreate(BaseModel):
    gym_id: str
    name: str
    description: Optional[str] = None
    fields: List[FormFieldCreate]
    active: bool = True
    show_on_registration: bool = True
