# IngresoQR - PRD (Product Requirements Document)

## Problema Original
Sistema SaaS multi-tenant de control de acceso para gimnasios. Incluye dashboard admin, PWA para socios, QR dinamicos/estaticos, pagos Stripe y MercadoPago, POS (TPV), formularios personalizados, avatares de perfil, analytics, roles multi-nivel, reservas de clases, y script para Raspberry Pi con control de torniquetes.

## Dominios de Produccion
- **Frontend**: https://app.ingresoqr.com
- **Backend API**: https://c.ingresoqr.com

## Version Actual: V 1.3.0

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
1. Frontend: Hacer `yarn build`, Guardar en Github, subir build/ a app.ingresoqr.com/ via Plesk File Manager
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

### Fase 9-11: Exportacion, POS Imagenes, Tabla Rediseniada
### Fase 12: Sistema de Permisos Granulares (RBAC)
### Fase 13: Control de Dispositivos y Estadisticas PWA
### Fase 14: Automatizacion y Dashboard Trainer
### Fase 15: Rebranding a IngresoQR
### Fase 16: Sistema de Seguridad (Rate limiting, IP blocking, login tracking)
### Fase 17: V1.3.0 - Modulos Avanzados
- Monitor remoto de Raspberry Pi (Heartbeat)
- Gamificacion (Insignias/Rachas/Ranking)
- Rutinas de entrenamiento para socios
- Facturacion automatizada con Stripe (real, multi-tenant)
- Sistema de cuentas Demo
- Pases de invitado configurables por admin
- Moneda por defecto EUR

### Fase 18: Modo Dark/Light (27 Mar 2026)
- CSS Variables en :root (dark) y .light-theme (light)
- Toggle en AdminLayout.js (sidebar) y PWALayout.js (header)
- Overrides globales para clases Tailwind zinc en .light-theme
- Override global de text-white -> dark text en light-theme con excepciones para botones con fondos de color
- Layouts actualizados con inline styles usando CSS variables
- Persistencia en localStorage (key: ingresoqr-theme)
- Testing: 15/15 tests pasados (iteration_18.json) + verificacion visual de 10+ paginas
- Build de produccion generado con URL https://c.ingresoqr.com

## Credenciales
- Super Admin: admin@ingresoqr.com / admin123

## Integraciones
- MercadoPago (Payments) - REAL
- Stripe (Payments) - REAL (multi-tenant, cada gym usa su propia API key)
- Almacenamiento local (Imagenes) - /opt/gymaccess/uploads/

## Backlog Pendiente
- P1: Portal de registro publico (auto-registro + pago online)
- P1: Check-in de clases reservadas
- P2: Push notifications reales (Firebase)
- P3: Chat directo entre trainers y socios
- P3: Reportes PDF exportables
