# GymAccess - PRD (Product Requirements Document)

## Problema Original
Sistema SaaS multi-tenant de control de acceso para gimnasios con QR dinámicos, pagos Stripe, roles multi-nivel, y control físico via Raspberry Pi.

## Arquitectura
- **Backend**: FastAPI (Python) - `/app/backend/server.py`
- **Frontend**: React + Tailwind + Shadcn UI
- **Database**: MongoDB (Docker con auth)
- **Hardware**: Raspberry Pi 3B+ con lectores QR USB (evdev) y relés GPIO

## Funcionalidades Implementadas

### Core
- JWT Authentication (Admin + Member)
- Multi-tenancy (Super Admin gym_id=null, Gym Admin gym_id=UUID)
- QR dinámicos con firma HMAC + sanitización
- Anti-passback (auto-detección dirección entrada/salida)
- Raspberry Pi con calibración USB persistente (scanner_map.json)
- GPIO pins: 12 (entrada), 16 (salida)

### Módulos
- Gestión de Gyms (CRUD, suspender, eliminar, max_members)
- Gestión de Miembros (CRUD, suspender con razón, eliminar)
- Planes y Membresías
- Dispositivos (solo super_admin)
- Kiosko (registro público)
- Contabilidad (dashboard + PDF export)
- Pagos Manuales
- Plantillas de Email
- Clases y Reservas
- Notificaciones in-app
- Guest Passes

### Seguridad
- Dispositivos solo visibles/gestionables por super_admin
- Anti-passback: no se puede entrar dos veces sin salir
- QR con tolerancia de 5 minutos
- MongoDB con autenticación + backup diario

## Deployment
- **Servidor**: Plesk (gymapi.ticketpro.es / gym.ticketpro.es)
- **Backend**: systemd service `gymaccess-api`
- **Frontend**: Build estático en /httpdocs/
- **DB**: MongoDB Docker con auth en localhost:27017
- **Pi**: systemd service `gymaccess` en /home/pi/gymaccess/

## Tareas Pendientes
### P1
- Cron job para auto-suspender membresías vencidas
- Módulo de facturación SaaS (super admin cobra a gyms)
- Protección contra eliminación de dispositivos activos

### P2
- Reportes PDF avanzados
- Push notifications (Firebase)
- Dashboards específicos para Trainer

### P3
- App nativa, Wearables, Gamificación
