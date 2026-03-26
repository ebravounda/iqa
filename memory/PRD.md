# GymAccess - PRD (Product Requirements Document)

## Problema Original
Sistema SaaS multi-tenant de control de acceso para gimnasios. Incluye dashboard admin, PWA para socios, QR dinamicos, pagos Stripe y MercadoPago, roles multi-nivel, reservas de clases, notificaciones, pases de invitado, y script para Raspberry Pi con control de torniquetes.

## Arquitectura
- **Backend**: FastAPI (Python) modular con APIRouter
- **Frontend**: React + Tailwind + Shadcn UI
- **Base de datos**: MongoDB
- **Auth**: JWT
- **Multi-tenant**: Super Admin (gym_id=null), Gym Admin (gym_id=UUID)

### Estructura Backend (Refactorizada)
```
/app/backend/
  server.py         # Entry point (~100 lines)
  database.py       # MongoDB connection
  auth.py           # JWT, password hashing, auth deps
  models.py         # All Pydantic models
  qr_utils.py       # QR generation/validation
  routes/
    auth_routes.py
    gym_routes.py
    member_routes.py
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
    misc_routes.py
```

## Roles
- **Super Admin**: Gestiona todo, crea gimnasios, asigna planes SaaS
- **Gym Admin**: Gestiona su gimnasio, socios, pagos, POS
- **Gym Manager**: Operaciones diarias, ventas, clases
- **Trainer**: Ve sus clases y asistencia

## Funcionalidades Implementadas

### Core (Anteriores)
- Auth JWT, QR dinamicos/estaticos, Raspberry Pi con anti-passback
- CRUD de gimnasios, socios, planes, membresias
- Clases, horarios, reservas, asistencia
- Notificaciones, pases de invitado
- Email SMTP configurable por gym
- Kiosko de registro publico
- Descarga de scripts (server.py, raspberry_access_control.py)
- Gestion: Suspender/Eliminar gimnasios y socios
- Guias de deploy: Plesk y Raspberry Pi

### Fase 1: Reestructuracion Backend (COMPLETADO - 2026-03-26)
- Refactorizado server.py de 3000+ lineas a modulos con APIRouter
- Zero downtime, todas las rutas funcionan

### Fase 2: Planes SaaS y Multi-moneda (COMPLETADO - 2026-03-26)
- CRUD de planes SaaS (Super Admin)
- Asignar planes a gimnasios
- Features gating: POS, MercadoPago, Iframes, Contabilidad Avanzada
- Multi-moneda por gym: EUR, USD, CLP, ARS (con config decimales)

### Fase 3: Modulo TPV/POS (COMPLETADO - 2026-03-26)
- CRUD de productos (nombre, costo, precio venta, stock, categoria, barcode)
- Vista de venta rapida con carrito
- Checkout efectivo/tarjeta
- Historial de ventas
- Impresion de tickets 80mm
- Control de stock
- Estadisticas (ventas hoy, mes, productos con stock bajo)
- Acceso gating por plan SaaS (has_pos)

### Fase 4: Integracion MercadoPago (COMPLETADO - 2026-03-26)
- Creacion de preferencias de pago
- Webhook para recibir confirmaciones
- Activacion automatica de membresias
- Configuracion por gimnasio (access_token)
- Solo disponible para moneda CLP
- Credenciales de produccion configuradas

### Fase 5: Contabilidad Avanzada (COMPLETADO - 2026-03-26)
- Retiros de caja con motivo y notas
- Impresion de comprobante de retiro 80mm
- Ventas POS integradas en reporte contable
- Totales por metodo de pago (Efectivo, Tarjeta, Stripe, MercadoPago)
- Caja neta (efectivo - retiros)
- Poda de registros > 6 meses

### Fase 6: Iframes y QR Estaticos (COMPLETADO - 2026-03-26)
- Generador de iframes para Registro Publico y Kiosko
- Copiar URL directa o codigo iframe
- Vista previa integrada
- QR estatico asignable por miembro (Super Admin)
- Badge visual "QR Fijo" en tabla de socios

### Fase 7: Comunicados/Broadcast (COMPLETADO - 2026-03-26)
- Super Admin crea comunicados con prioridad normal/urgente
- Todos los admin de gym los ven
- Dismiss individual por admin
- Auto-suspension de membresias vencidas (cron task background)

## Credenciales
- Super Admin: admin@gymaccess.com / admin123
- MongoDB: gymadmin / Ed2526759

## Integraciones 3P
- **Stripe**: Pagos con tarjeta (global y por gimnasio)
- **MercadoPago**: Pagos CLP (credenciales en .env)

## Backlog Pendiente

### P1
- Dashboards especificos para Trainers
- Push notifications (Firebase/PWA)
- Mejoras UI detalladas en cada modulo

### P2
- Facturacion SaaS automatica (cobro a gimnasios)
- App nativa, Wearables, Gamificacion
