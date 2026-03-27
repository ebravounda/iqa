# GymAccess - PRD (Product Requirements Document)

## Problema Original
Sistema SaaS multi-tenant de control de acceso para gimnasios. Incluye dashboard admin, PWA para socios, QR dinamicos/estaticos, pagos Stripe y MercadoPago, POS (TPV), formularios personalizados, avatares de perfil, analytics, roles multi-nivel, reservas de clases, y script para Raspberry Pi con control de torniquetes.

## Dominios de Produccion
- **Frontend**: https://app.ingresoqr.com
- **Backend API**: https://c.ingresoqr.com
- **Dominio anterior**: gym.ticketpro.es / gymapi.ticketpro.es (puede seguir activo)

## Arquitectura
- **Backend**: FastAPI (Python) modular con APIRouter - Corre en /opt/gymaccess/
- **Frontend**: React + Tailwind + Shadcn UI - Build en Plesk
- **Base de datos**: MongoDB (localhost:27017, DB: gymaccess)
- **Auth**: JWT + Permisos granulares por rol
- **Multi-tenant**: Super Admin (gym_id=null), Gym Admin (gym_id=UUID)
- **Imagenes**: Almacenamiento local en /opt/gymaccess/uploads/

### Estructura Backend (Servidor)
```
/opt/gymaccess/
  server.py, database.py, auth.py, models.py, qr_utils.py, storage.py, .env
  routes/ (20+ archivos de rutas modulares)
  uploads/ (imagenes de productos y avatares)
  venv/ (entorno virtual Python)
  actualizar.sh (script de despliegue)
```

### Estructura Plesk
```
/var/www/vhosts/ingresoqr.com/
  app.ingresoqr.com/  (frontend build)
  c.ingresoqr.com/    (backend source - staging area)
```

## Procedimiento de Actualizacion
1. Frontend: Subir build/ a app.ingresoqr.com/ via Plesk File Manager
2. Backend: Subir .py y routes/ a c.ingresoqr.com/ via Plesk, luego SSH: sudo /opt/gymaccess/actualizar.sh

## Funcionalidades Implementadas

### Core (Fases 1-8)
- Auth JWT, QR dinamicos/estaticos, Raspberry Pi anti-passback
- CRUD gimnasios/socios/planes/membresias, Clases/horarios/reservas
- Notificaciones, pases invitado, Email SMTP, Kiosko registro
- Backend modular con APIRouter
- Planes SaaS, Multi-moneda, TPV/POS, MercadoPago
- Contabilidad avanzada, Iframes, Broadcast
- Formularios personalizados, Avatares, Analytics dashboard

### Fase 9-11: Exportacion, POS Imagenes, Tabla Rediseñada
### Fase 12: Sistema de Permisos Granulares (RBAC)
### Fase 13: Control de Dispositivos y Estadisticas PWA
### Fase 14: Automatizacion y Dashboard Trainer
- Auto-suspension CRON a medianoche UTC
- Emails recordatorio 1/3/7 dias antes de vencimiento
- Dashboard especifico para Trainers
- Navegacion por fechas en Asistencia
- Almacenamiento local de imagenes (sin dependencia externa)
- Migracion de dominio a ingresoqr.com
- Service Worker + iconos PWA para Google Play

## Credenciales
- Super Admin: admin@gymaccess.com / admin123

## Integraciones
- MercadoPago (Payments) - REAL
- Stripe (Payments) - MOCKED
- Almacenamiento local (Imagenes) - /opt/gymaccess/uploads/

## Backlog Pendiente
- P0: Publicar PWA en Google Play (PWABuilder)
- P2: Push notifications reales (Firebase)
- P3: Facturacion SaaS automatica, Wearables, Gamificacion
