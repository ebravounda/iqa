# GymAccess - PRD (Product Requirements Document)

## Problema Original
Sistema SaaS multi-tenant de control de acceso para gimnasios. Incluye dashboard admin, PWA para socios, QR dinamicos/estaticos, pagos Stripe y MercadoPago, POS (TPV), formularios personalizados, avatares de perfil, analytics, roles multi-nivel, reservas de clases, y script para Raspberry Pi con control de torniquetes.

## Arquitectura
- **Backend**: FastAPI (Python) modular con APIRouter
- **Frontend**: React + Tailwind + Shadcn UI
- **Base de datos**: MongoDB
- **Auth**: JWT
- **Multi-tenant**: Super Admin (gym_id=null), Gym Admin (gym_id=UUID)

### Estructura Backend (Refactorizada)
```
/app/backend/
  server.py         # Entry point (~120 lines)
  database.py       # MongoDB connection
  auth.py           # JWT, password hashing, auth deps
  models.py         # All Pydantic models
  qr_utils.py       # QR generation/validation
  storage.py        # Emergent Object Storage
  routes/
    auth_routes.py
    gym_routes.py
    member_routes.py     # Includes Excel export
    plan_routes.py
    access_routes.py
    device_routes.py
    payment_routes.py
    class_routes.py
    notification_guest_routes.py
    accounting_routes.py
    saas_routes.py
    pos_routes.py
    mercadopago_routes.py
    upload_routes.py
    form_routes.py
    analytics_routes.py
    misc_routes.py
```

## Roles
- **Super Admin**: Gestiona todo, crea gimnasios, asigna planes SaaS
- **Gym Admin**: Gestiona su gimnasio, socios, pagos, POS
- **Gym Manager**: Operaciones diarias, ventas, clases
- **Trainer**: Ve sus clases y asistencia

## Funcionalidades Implementadas

### Core
- Auth JWT, QR dinamicos/estaticos, Raspberry Pi con anti-passback
- CRUD de gimnasios, socios, planes, membresias
- Clases, horarios, reservas, asistencia
- Notificaciones, pases de invitado
- Email SMTP configurable por gym
- Kiosko de registro publico
- Descarga de scripts (server.py, raspberry_access_control.py)
- Gestion: Suspender/Eliminar gimnasios y socios
- Guias de deploy: Plesk y Raspberry Pi

### Fase 1: Reestructuracion Backend (COMPLETADO)
- Refactorizado server.py de 3000+ lineas a modulos con APIRouter

### Fase 2: Planes SaaS y Multi-moneda (COMPLETADO)
- CRUD de planes SaaS (Super Admin), Multi-moneda por gym

### Fase 3: Modulo TPV/POS (COMPLETADO)
- CRUD de productos, vista de venta rapida, checkout, historial, tickets 80mm

### Fase 4: Integracion MercadoPago (COMPLETADO)
- Preferencias de pago, webhook, activacion automatica

### Fase 5: Contabilidad Avanzada (COMPLETADO)
- Retiros de caja, reportes PDF, poda de registros

### Fase 6: Iframes y QR Estaticos (COMPLETADO)
- Generador de iframes, QR estatico asignable por miembro

### Fase 7: Comunicados/Broadcast (COMPLETADO)
- Comunicados con prioridad, auto-suspension de membresias vencidas (background task)

### Fase 8: Formularios, Avatares y Analytics (COMPLETADO)
- Formularios personalizados por gym, fotos de perfil (Object Storage), analytics dashboard

### Fase 9: Exportacion de Datos y Mejoras UX (COMPLETADO - 2026-02-28)
- Columna de telefono visible en tabla de socios
- Nuevo menu "Datos" con exportacion Excel (.xlsx) de base de datos de socios
- Excel incluye: Nombre, Numero de Socio, Telefono, Email, Estado, Fecha Registro (ordenado alfabeticamente)
- Selector de gimnasio para Super Admin en Analytics, TPV/POS y Formularios
- Corregido referencia fetchData -> fetchMembers en AdminMembers.js
- Auto-suspension automatica de membresias vencidas (background task cada hora)

## Credenciales
- Super Admin: admin@gymaccess.com / admin123

## Integraciones 3P
- **Stripe**: Pagos con tarjeta (global y por gimnasio) - MOCKED
- **MercadoPago**: Pagos CLP (credenciales en .env) - REAL
- **Emergent Object Storage**: Fotos de perfil

## Backlog Pendiente

### P1
- Emails de recordatorio de vencimiento de membresia
- Check-in de asistencia a clases (sistema de marcado al llegar)

### P2
- Dashboards especificos para Trainers
- Push notifications (Firebase/PWA)
- Mejoras UI detalladas en cada modulo

### P3
- Facturacion SaaS automatica (cobro a gimnasios)
- App nativa, Wearables, Gamificacion
