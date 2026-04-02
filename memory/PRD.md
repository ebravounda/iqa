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
- Documentacion tecnica completa en PDF (EN + ES)
- Capturas Google Play (8 screenshots + feature graphic 1024x500)

## Bugs Corregidos (Abril 2026)
- FIX: Registro publico creaba membresia activa sin pago -> Ahora crea status "pending" + membresia "pending_payment"
- FIX: Contabilidad mostraba transacciones sin pago como ingreso -> Solo cuenta payment_status="paid"
- FIX: Tabla transacciones ahora muestra columna Estado (Pagado/Pendiente) + tarjeta "Pendiente de Cobro"
- FIX: Dropdown de subir foto se cerraba antes de abrir selector -> onSelect preventDefault
- FIX: Reenviar emails ahora disponible para todos los tipos (no solo welcome)
- FIX: QR bloqueado para miembros pendientes (403)
- FIX: Reserva de clases requiere membresia activa (403)
- FIX: JWT token de registro publico usaba "type" en vez de "role"
- FIX: Division por cero en AdminPlans.js (duration_days || 1)
- FIX: PublicRegister muestra bloque "Pago Pendiente" con boton pagar
- FIX: MemberHome muestra bloque pendiente y oculta QR si no tiene membresia

## P1 - Pendiente (solicitado por usuario)
1. Email de pago al registrarse (boton de pagar en el correo de bienvenida)
2. Auto-eliminacion socios inactivos 60+ dias sin pago ni accesos (o boton)
3. Socio sube su propia foto desde PWA
4. Colores corporativos por gimnasio (Super Admin configura fondo, menu, texto)
5. TPV mas profesional con categorias de productos
6. Modulo RFID para tarjetas fisicas

## P2 - Futuro
- Portal de registro publico mejorado
- Push Notifications reales (Firebase/PWA Push API)
- Dashboard mejorado para Trainers
- Reportes PDF exportables adicionales
- Multi-vertical (condominios, hoteles, coworking)

## P3 - Backlog
- Chat trainer-socio
- Integraciones adicionales

## Notas de Despliegue
- git clone SOLO actualiza backend .py files
- Frontend requiere yarn build + subir build/ a Plesk manualmente
- Backend: c.ingresoqr.com (proxy a :8001)
- Frontend: app.ingresoqr.com (static build en httpdocs/)
