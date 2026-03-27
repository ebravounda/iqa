# IngresoQR - PRD (Product Requirements Document)

## Problema Original
Sistema SaaS multi-tenant de control de acceso para gimnasios con QR dinamico, dashboard admin, PWA para socios, control de torniquetes con Raspberry Pi, pagos con Stripe/MercadoPago, emails automaticos, roles multi-nivel.

## Arquitectura
- **Backend**: FastAPI (Python) con MongoDB
- **Frontend**: React + Tailwind + Shadcn UI
- **IoT**: Script Python para Raspberry Pi 3B+ (2 relays: entrada/salida)
- **Base de datos**: MongoDB
- **Autenticacion**: JWT
- **Deployment**: Plesk (gym.ticketpro.es / c.ingresoqr.com)

## Roles
1. **Super Admin** (gym_id=null): Gestion global, planes SaaS, todos los gimnasios
2. **Gym Admin** (gym_id=UUID): Gestion de su propio gimnasio
3. **Gym Manager**: Permisos configurables por admin
4. **Trainer**: Gestion de clases y rutinas
5. **Member**: Acceso via PWA/QR

## Funcionalidades Implementadas

### Core
- [x] Autenticacion JWT multi-rol
- [x] Dashboard admin con estadisticas
- [x] Gestion de gimnasios (CRUD, capacidad, suspender/eliminar)
- [x] Gestion de socios (CRUD, suspender con razon, eliminar)
- [x] QR dinamico con refresh configurable (5/10/15 seg)
- [x] Control de acceso via Raspberry Pi (2 relays, pin 12 fix)
- [x] Registro via Kiosk PWA
- [x] Dispositivos IoT (registro, token, copia ID)

### SaaS & Planes
- [x] Planes SaaS (Crear, Editar, Asignar a gimnasios)
- [x] "Mi Plan SaaS" visible para Gym Admin en Configuracion
- [x] 12 features configurables por plan
- [x] Barra de capacidad de socios
- [x] Suspension por impago (bloquea Admin, Socios, API)

### Clases & Horarios
- [x] CRUD completo de clases (crear, editar, eliminar)
- [x] Clases recurrentes con dias de semana
- [x] Hora inicio/fin, fecha inicio/fin
- [x] Asignacion de entrenadores
- [x] Eliminacion en cascada (clase + horarios)

### Personal & Staff
- [x] Gestion de staff (Admin, Gestor, Entrenador)
- [x] Selector de gimnasio para Super Admin
- [x] Permisos configurables por gestor
- [x] Creacion de entrenadores con especialidades

### Pagos
- [x] Stripe (configuracion por gimnasio)
- [x] MercadoPago (configuracion por gimnasio)
- [x] Planes de membresia (precio, duracion, modulos)

### Emails
- [x] Historial de emails por socio
- [x] Boton de reenvio de emails
- [x] Email de bienvenida con boton de pago

### UI/UX
- [x] Dark/Light mode con variables CSS
- [x] Error Boundary para prevenir pantallas negras
- [x] Sidebar con scroll
- [x] Modulos autorizados en Settings

### Seguridad
- [x] Verificacion de membresia expirada
- [x] Bloqueo de acceso para suspendidos
- [x] Validacion de QR expirado corregida

## Documentos
- `/app/GUIA_PLESK_RASPBERRY.md` - Guia de despliegue
- `/app/GUIA_GOOGLE_PLAY.md` - Guia para Google Play

## Tareas Pendientes

### P1 - Proximo
- Portal de registro publico (auto-registro + pago online)
- Check-in de asistencia para clases reservadas

### P2 - Futuro
- Push notifications reales (Firebase/PWA)
- Dashboard especifico para Trainers
- Reportes PDF exportables

### P3 - Backlog
- Chat trainer-socio
- Integraciones adicionales

## Info Critica
- **Produccion**: REACT_APP_BACKEND_URL=https://c.ingresoqr.com para yarn build
- **Super Admin**: admin@ingresoqr.com / admin123
- **Gym Admin Test**: admin@fitzone.com / admin123
- **Idioma**: Responder siempre en espanol
