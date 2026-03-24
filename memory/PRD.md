# GymAccess - PRD

## Fecha: 24/03/2026

## Problem Statement
Sistema SaaS multi-tenant de control de acceso para gimnasios con QR dinámico, pagos con Stripe, roles multi-tenant, y control de tornos con Raspberry Pi.

## Funcionalidades Implementadas
- Panel Admin con dashboard, gestión de gyms/socios/planes/clases/horarios/personal
- CRUD de Gimnasios con Editar/Suspender/Eliminar (con confirmación)
- PWA para socios: QR dinámico, reservas, notificaciones, invitados
- Roles: super_admin, gym_admin, gym_manager, trainer
- Raspberry Pi: script de control de tornos con relés GPIO
- Badge "Made with Emergent" eliminado
- Sidebar scrollable
- Notificaciones: fix para super_admin sin gym_id
- Build de producción compilado para gym.ticketpro.es / gymapi.ticketpro.es
- **Configuración de Stripe por Gimnasio** (cada gym admin configura su propia clave)
- **Selector de moneda** (USD, EUR, MXN, ARS, CLP, COP, PEN, BRL, GBP)
- **Gráficos de accesos reales** en Dashboard (BarChart con datos diarios reales)
- **Estadísticas de acceso por socio** (modal con gráfico de asistencia)
- **Alerta de pago en PWA** cuando membresía por vencer/vencida con botón "Pagar Ahora"
- **Auto-suspensión automática** de membresías expiradas (background task cada 60 min)
- **Endpoints de estadísticas**: daily, hourly, member attendance
- **Historial de pagos** con enriquecimiento de datos de socio y plan
- **Tabla de accesos mejorada** con stats summary, tipo (socio/invitado), acciones

## Credenciales
- Super Admin: admin@gymaccess.com / admin123
- Gym Admin: admin@fitzone.com / admin123
- Trainer: carlos@trainer.com / trainer123
- Member: LRF4HL

## Bugs Corregidos
- Schedule creation: SelectItem value="" → "default"
- Notificaciones: super_admin sin gym_id → selector de gym agregado
- Sidebar overflow → scrollbar-thin
- Badge Emergent → eliminado de index.html
- Dashboard chart mock data → datos reales de API

## Backlog
### P1
- SMTP real para emails
- Cron para recordatorios de expiración por email
- Vista mejorada para trainers
- Check-in de asistencia a clases

### P2
- Push notifications (Firebase)
- Reportes PDF
- Historial de pagos detallado en el admin panel

### P3
- App nativa
- Wearables
- Gamificación

## Arquitectura
```
/app
├── backend/
│   ├── server.py              # FastAPI (2100+ lines)
│   ├── requirements-prod.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── lib/api.js         # API calls
│   │   ├── context/AuthContext.js
│   │   ├── pages/admin/       # Admin: Dashboard, Settings, Access, Gyms, Members...
│   │   └── pages/pwa/         # PWA: Home, Membership, Classes...
├── memory/PRD.md
├── raspberry_access_control.py
└── GUIA_PLESK_RASPBERRY.md
```

## Key API Endpoints
- POST /api/auth/admin/login
- POST /api/auth/member/login
- PUT /api/gyms/{id}/stripe-config
- GET /api/gyms/{id}/stripe-config
- GET /api/gyms/{id}/has-payments
- GET /api/access/stats/daily
- GET /api/access/stats/hourly
- GET /api/access/stats/member/{id}
- GET /api/payments/history
- POST /api/payments/checkout
- POST /api/access/validate

## DB Collections
- gyms, admins, members, memberships, plans, classes, class_schedules, bookings, notifications, guests, access_logs, devices, payment_transactions
