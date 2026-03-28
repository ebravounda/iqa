# IngresoQR - PRD (Product Requirements Document)

## Vision
Sistema SaaS multi-tenant de control de acceso para gimnasios con QR dinamico, pagos Stripe/MercadoPago, control fisico via Raspberry Pi, y app PWA para socios.

## Stack Tecnologico
- Backend: FastAPI + MongoDB (Motor) + JWT
- Frontend: React 18 + Tailwind + Shadcn/UI
- IoT: Raspberry Pi 3B+ + GPIO relays + USB QR scanner
- Deploy: Plesk VPS (c.ingresoqr.com / app.ingresoqr.com)

## Roles
- super_admin (gym_id=null): Plataforma completa
- gym_admin (gym_id=UUID): Su gimnasio
- gym_manager: Permisos configurables
- trainer: Sus clases y rutinas
- member: PWA con QR, reservas, perfil

## Completado
- Sistema base multi-tenant con auth JWT
- QR dinamico/estatico con HMAC y anti-passback
- Raspberry Pi script con GPIO y evdev
- Stripe + MercadoPago por gimnasio
- Pagos manuales
- Clases recurrentes con reservas y check-in
- SaaS plans con 12 feature flags
- POS (Punto de Venta)
- Gamificacion (insignias y rachas)
- Rutinas de entrenamiento
- Formularios personalizados
- Guest passes con QR
- Email SMTP por gimnasio
- Analytics avanzadas
- Exportar Excel socios
- PDF informes ventas
- Seguridad: bloqueo IP, intentos login
- Device management (limitar dispositivos por socio)
- Modo kiosko
- Dark/Light theme
- ErrorBoundary para crashes React
- Impersonation (Super Admin -> Gym Admin)
- Broadcasts plataforma
- Despliegue Plesk + sync backend via GitHub
- **Documentacion tecnica completa en PDF (EN + ES) - Feb 2026**

## P0 - Resuelto
- Fix division por cero en AdminPlans.js (duration_days || 1)
- Fix import DollarSign en AdminPlans.js
- Fix guardado booleanos False en SaaS plans
- Fix logo upload y serving via /api/files/
- Fix Stripe fallback a env key
- Fix dark/light mode CSS variables

## P1 - Pendiente
- Portal de registro publico (auto-registro + seleccion plan + pago online)
- Check-in / seguimiento de asistencia para clases reservadas
- Cron job automatico para auto-suspender membresias vencidas (actualmente es boton manual)

## P2 - Futuro
- Push Notifications reales (Firebase/PWA Push API)
- Dashboard mejorado para Trainers
- Reportes PDF exportables adicionales

## P3 - Backlog
- Chat trainer-socio
- Integraciones adicionales

## Notas de Despliegue
- git clone SOLO actualiza backend .py files
- Frontend requiere yarn build + subir build/ a Plesk manualmente
- Backend: c.ingresoqr.com (proxy a :8001)
- Frontend: app.ingresoqr.com (static build en httpdocs/)
