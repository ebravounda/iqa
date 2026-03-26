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
  server.py, database.py, auth.py, models.py, qr_utils.py, storage.py
  routes/ (auth, gym, member, plan, access, device, payment, class, 
           notification_guest, accounting, saas, pos, mercadopago, 
           upload, form, analytics, misc)
```

## Funcionalidades Implementadas

### Core (Fases 1-8)
- Auth JWT, QR dinamicos/estaticos, Raspberry Pi anti-passback
- CRUD gimnasios/socios/planes/membresias, Clases/horarios/reservas
- Notificaciones, pases invitado, Email SMTP, Kiosko registro
- Suspender/Eliminar gimnasios y socios, Guias deploy
- Backend refactorizado de monolito a modulos APIRouter
- Planes SaaS, Multi-moneda, TPV/POS, MercadoPago
- Contabilidad avanzada (PDF, retiros caja), Iframes, Broadcast
- Formularios personalizados, Avatares (Object Storage), Analytics dashboard

### Fase 9: Exportacion de Datos y Mejoras UX (2026-02-28)
- Columna telefono visible en tabla socios
- Menu "Datos" con exportacion Excel
- Selector de gimnasio para Super Admin en Analytics/TPV/Formularios
- Auto-suspension membresias vencidas (background task)

### Fase 10: Filtros Excel Avanzados e Imagenes POS (2026-02-28)
- **Filtros Excel**: Estado (activo/suspendido/pendiente/bloqueado), rango fechas, incluir datos de membresias (plan activo, inicio, fin, precio)
- **Imagenes POS**: Upload de imagenes para cada producto, thumbnails en lista y vista de venta, boton "Foto" en tabla de productos
- React key warning corregido en AdminAnalytics.js

## Credenciales
- Super Admin: admin@gymaccess.com / admin123

## Integraciones 3P
- Stripe (Payments) - MOCKED
- MercadoPago (Payments) - REAL
- Emergent Object Storage (Fotos perfil + productos)

## Backlog Pendiente

### P1
- Emails recordatorio vencimiento membresia
- Check-in asistencia a clases

### P2
- Dashboards para Trainers
- Push notifications (Firebase/PWA)

### P3
- Facturacion SaaS automatica
- App nativa, Wearables, Gamificacion
