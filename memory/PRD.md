# IngresoQR - PRD (Product Requirements Document)

## Problema Original
Sistema SaaS multi-tenant de control de acceso para gimnasios con QR dinamico, dashboard admin, PWA para socios, control de torniquetes con Raspberry Pi, pagos con Stripe/MercadoPago, emails automaticos, roles multi-nivel.

## Arquitectura
- **Backend**: FastAPI (Python) con MongoDB, rutas modulares en `/backend/routes/`
- **Frontend**: React + Tailwind + Shadcn UI
- **IoT**: Script Python para Raspberry Pi 3B+ (2 relays: entrada/salida, pin 12)
- **Base de datos**: MongoDB
- **Autenticacion**: JWT
- **Deployment**: Plesk (app.ingresoqr.com / c.ingresoqr.com)

## Roles
1. Super Admin (gym_id=null): Gestion global, planes SaaS
2. Gym Admin (gym_id=UUID): Gestion de su gimnasio
3. Gym Manager: Permisos configurables
4. Trainer: Clases y rutinas
5. Member: Acceso via PWA/QR

## Funcionalidades Implementadas

### Core
- [x] Autenticacion JWT multi-rol
- [x] Dashboard admin con estadisticas
- [x] CRUD gimnasios (capacidad, suspender, eliminar)
- [x] CRUD socios (suspender con razon, eliminar)
- [x] QR dinamico (refresh 5/10/15 seg)
- [x] Control de acceso Raspberry Pi (2 relays, pin 12)
- [x] Registro Kiosk PWA
- [x] Dispositivos IoT (registro, token, copia ID)

### SaaS & Planes
- [x] CRUD Planes SaaS con 12 features booleanas
- [x] Edicion de planes guarda True Y False correctamente
- [x] "Mi Plan SaaS" para Gym Admin en Configuracion
- [x] Suspension por impago (bloquea Admin, Socios, API)

### Clases & Horarios
- [x] CRUD completo de clases (crear, editar, eliminar)
- [x] Clases recurrentes con end_date respetada
- [x] Edicion regenera horarios automaticamente
- [x] Eliminacion borra clase y horarios en cascada
- [x] Trainer Dashboard filtra clases eliminadas

### Personal & Staff
- [x] CRUD staff con selector de gimnasio para Super Admin
- [x] Permisos configurables por gestor

### Pagos
- [x] Stripe y MercadoPago (configuracion por gimnasio)
- [x] Planes de membresia

### Uploads
- [x] Subida de avatar por admin (funciona con storage local)
- [x] Subida de logo de gimnasio (nuevo endpoint)
- [x] Servicio de archivos via /api/files/{path}

### Emails
- [x] Historial de emails por socio con reenvio

### UI/UX
- [x] Dark/Light mode con variables CSS completas
- [x] Error Boundary para prevenir pantallas negras
- [x] Boton "Ver" contacto siempre visible en Socios
- [x] Modal de Asistencia con scroll
- [x] Demo button removido de Admin Login
- [x] Logo de gym mostrado correctamente en PWA (rutas relativas)

## Info Critica
- **Produccion**: REACT_APP_BACKEND_URL=https://c.ingresoqr.com
- **Frontend**: app.ingresoqr.com
- **Super Admin**: admin@ingresoqr.com / admin123
- **Idioma**: Responder siempre en espanol

## Tareas Pendientes

### P1 - Proximo
- Portal de registro publico (auto-registro + pago online)
- Check-in de asistencia para clases reservadas

### P2 - Futuro
- Push notifications reales (Firebase/PWA)
- Dashboard especifico para Trainers mejorado
- Reportes PDF exportables

### P3 - Backlog
- Chat trainer-socio
- Integraciones adicionales
