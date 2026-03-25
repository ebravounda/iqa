# GymAccess - PRD

## Última actualización: 25/03/2026

## Problem Statement
Sistema SaaS multi-tenant de control de acceso para gimnasios con QR dinámico/estático, pagos con Stripe, roles multi-tenant, página de auto-registro público, y control de tornos con Raspberry Pi.

## Funcionalidades Implementadas

### Core
- Panel Admin: dashboard, gestión de gyms/socios/planes/clases/horarios/personal
- PWA para socios: QR dinámico/estático, reservas, notificaciones, invitados
- Roles: super_admin, gym_admin, gym_manager, trainer
- JWT Authentication + Impersonación
- Raspberry Pi: script de control de tornos con relés GPIO

### SaaS Multi-tenant
- Configuración de Stripe por Gimnasio (cada gym configura su propia clave)
- Auto-creación de gym admin al crear gimnasio
- Impersonación: Super Admin puede "Iniciar sesión como Admin" en cualquier gym
- CRUD completo: Gimnasios (Editar/Suspender/Eliminar), Socios, Planes, Clases, Dispositivos

### QR y Accesos
- **QR Dinámico**: cambia cada X segundos (5/10/15/30 configurable)
- **QR Estático**: código fijo por socio (opción por gym)
- Gráficos de accesos reales en Dashboard (BarChart diario)
- Estadísticas de acceso por socio
- Auto-suspensión automática de membresías expiradas

### Nuevas funcionalidades (25/03/2026)
- **Página de Registro Público**: `/register/{gym_id}` - socios se registran, eligen plan, reciben código QR y acceso inmediato
- **QR Estático/Dinámico**: cada gym elige si el QR de sus socios es fijo o dinámico
- **Dashboard Super Admin mejorado**: accesos recientes con nombre del gimnasio
- **Exportar a Excel (XLSX)**: reemplaza CSV con archivo Excel formateado
- **Enlace de Registro Público**: visible en configuración del gym con botón copiar
- **Eliminación de dispositivos**: DELETE endpoint + botón UI
- **Corrección de 6 bugs**: login/impersonación, config guardable, QR sin rotación, clases sin pantalla negra, export ordenado

## Credenciales
- Super Admin: admin@gymaccess.com / admin123
- Gym Admin FitZone: admin@fitzone.com / admin123

## Arquitectura
```
/app
├── backend/
│   ├── server.py              # FastAPI (2360+ lines)
│   ├── tests/
│   └── .env
├── frontend/
│   ├── build/                 # Production build
│   ├── src/
│   │   ├── lib/api.js
│   │   ├── context/AuthContext.js
│   │   ├── pages/admin/
│   │   └── pages/pwa/
├── memory/PRD.md
├── raspberry_access_control.py
└── GUIA_PLESK_RASPBERRY.md
```

## DB Collections
gyms, admins, members, memberships, plans, classes, class_schedules, bookings, notifications, guests, access_logs, devices, payment_transactions

## Backlog
### P1
- Integración SMTP para emails del sistema (registro, reset password, recordatorios)
- Check-in de asistencia a clases

### P2
- Módulo Kiosko
- Planes SaaS con tiers para gimnasios
- Vista mejorada para trainers
- Push notifications (Firebase)

### P3
- Reportes PDF, App nativa, Wearables, Gamificación
