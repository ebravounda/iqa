# GymAccess - PRD

## Fecha: 24/03/2026

## Problem Statement
Sistema SaaS multi-tenant de control de acceso para gimnasios con QR dinámico, pagos con Stripe, roles multi-tenant, y control de tornos con Raspberry Pi.

## Funcionalidades Implementadas
- Panel Admin con dashboard, gestión de gyms/socios/planes/clases/horarios/personal
- CRUD de Gimnasios con Editar/Suspender/Eliminar (con confirmación)
- PWA para socios: QR dinámico, reservas, notificaciones, invitados
- Roles: super_admin, gym_admin, gym_manager, trainer
- Raspberry Pi: script de control de tornos con relés GPIO (evdev + RPi.GPIO)
- Sidebar scrollable, Badge Emergent eliminado
- Configuración de Stripe por Gimnasio (cada gym admin configura su propia clave + moneda)
- Gráficos de accesos reales en Dashboard (BarChart diario)
- Estadísticas de acceso por socio (modal con gráfico de asistencia 30 días)
- Alerta de pago en PWA cuando membresía por vencer/vencida con botón "Pagar Ahora"
- Auto-suspensión automática de membresías expiradas (background task cada 60 min)
- Credenciales automáticas por gimnasio: Al crear un gym, se auto-crea un gym_admin
- Impersonación de gym: Super Admin puede "Iniciar sesión como Admin" en cualquier gym
- PWA responsive mejorada: Diseño adaptable a cualquier dispositivo (mobile-first)
- Endpoints de estadísticas: daily, hourly, member attendance, payment history
- **Eliminación de dispositivos**: DELETE endpoint + botón en UI
- **Configuración guardable**: Fix de validación EmailStr para campos vacíos
- **QR sin rotación**: Animación simplificada (scale/opacity en vez de rotateY)
- **Clases con selector de gym**: Super admin puede seleccionar gym al crear clases
- **Export CSV ordenado**: Datos ordenados por fecha ascendente

## Credenciales
- Super Admin: admin@gymaccess.com / admin123
- Gym Admin FitZone: admin@fitzone.com / admin123
- Gym Admin PowerFit: admin@powerfit.com / powerfit123
- Member: LRF4HL

## Arquitectura
```
/app
├── backend/
│   ├── server.py              # FastAPI (2270+ lines)
│   ├── tests/                 # pytest tests
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── lib/api.js
│   │   ├── context/AuthContext.js
│   │   ├── layouts/AdminLayout.js
│   │   ├── layouts/PWALayout.js
│   │   ├── pages/admin/
│   │   └── pages/pwa/
├── memory/PRD.md
├── raspberry_access_control.py
└── GUIA_PLESK_RASPBERRY.md
```

## Key API Endpoints
- POST /api/auth/admin/login
- POST /api/auth/admin/impersonate/{gym_id}
- POST /api/auth/member/login
- PUT /api/gyms/{id}
- PUT /api/gyms/{id}/stripe-config
- GET /api/gyms/{id}/stripe-config
- DELETE /api/devices/{device_id}
- GET /api/access/stats/daily
- GET /api/access/stats/hourly
- GET /api/access/stats/member/{id}
- GET /api/payments/history
- POST /api/payments/checkout
- POST /api/access/validate

## DB Collections
gyms, admins, members, memberships, plans, classes, class_schedules, bookings, notifications, guests, access_logs, devices, payment_transactions

## Backlog
### P1
- Opción QR estático/dinámico por gym
- Integración SMTP para emails del sistema
- Página pública de auto-registro para socios
- Contador de accesos recientes en dashboard super admin
- Exportar a Excel (XLSX) en vez de CSV
- Check-in de asistencia a clases

### P2
- Módulo Kiosko (controlado por super admin por gym)
- Planes SaaS con tiers para gimnasios
- Vista mejorada para trainers
- Push notifications (Firebase)

### P3
- Reportes PDF
- App nativa
- Wearables
- Gamificación
