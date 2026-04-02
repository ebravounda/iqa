# IngresoQR - PRD (Product Requirements Document)

## Vision
Sistema SaaS multi-tenant de control de acceso para gimnasios, condominios, hoteles y coworkings con QR dinamico, pagos Stripe/MercadoPago, control fisico via Raspberry Pi, y app PWA para socios/residentes/huespedes/miembros.

## Stack Tecnologico
- Backend: FastAPI + MongoDB (Motor) + JWT
- Frontend: React 18 + Tailwind + Shadcn/UI
- IoT: Raspberry Pi 3B+ + GPIO relays + USB QR scanner
- Deploy: Plesk VPS (c.ingresoqr.com / app.ingresoqr.com)

## Completado

### Core (historico)
- Sistema base multi-tenant con auth JWT
- QR dinamico/estatico con HMAC y anti-passback
- Raspberry Pi script con GPIO y evdev
- Stripe + MercadoPago por gimnasio + pagos manuales
- Clases recurrentes con reservas y check-in
- SaaS plans con 12 feature flags
- POS, Gamificacion, Rutinas, Formularios, Guest passes
- Email SMTP por gimnasio, Analytics, Excel export, PDF ventas
- Seguridad: bloqueo IP, device management, dark/light theme
- ErrorBoundary, Impersonation, Broadcasts
- Despliegue Plesk + sync backend via GitHub
- Documentacion tecnica PDF (EN + ES)
- Capturas Google Play (8 screenshots + feature graphic)

### Bugs P0 Corregidos (Abril 2026)
- Registro publico creaba membresia activa sin pago -> status "pending" + "pending_payment"
- Contabilidad mostraba ingresos sin cobrar -> columna Estado (Pagado/Pendiente) + solo paid en revenue
- Dropdown foto admin se cerraba -> onSelect preventDefault
- QR y reservas sin restriccion -> 403 para miembros pending sin membresia activa
- JWT de registro publico usaba "type" -> corregido a "role"
- Division por cero AdminPlans.js -> (duration_days || 1)
- Modal "Editar Negocio" no permitia scroll -> agregado max-h-[90vh] overflow-y-auto (2 Abr 2026)

### Features P1 Implementadas
- Email de bienvenida con boton de pago al registrarse con plan
- Limpieza de socios inactivos 60+ dias (boton "Limpiar Inactivos" en Admin)
- Socio sube/cambia su foto desde PWA (icono camara en perfil)
- Endpoint /api/accounting/transactions con resumen pagado/pendiente
- Boton reenviar email para todos los tipos
- Colores corporativos por gimnasio (primary, bg, menu, text, secondary) con pickers y vista previa
- TPV/POS profesional con categorias, 4 tabs (TPV, Productos, Ventas, Estadisticas), carrito
- Modulo RFID para tarjetas/llaveros fisicos: asignacion, validacion, anti-passback

### Multi-Vertical (Abril 2026)
- Campo `business_type` en modelo Gym (gym, condominium, hotel, coworking)
- Selector visual de 4 tipos de negocio al crear/editar en AdminGyms
- Badge de tipo de negocio en tarjetas de gym
- Labels dinamicos en sidebar, Dashboard, Members, Plans, Classes, PWA
- BusinessContext React context para propagar labels a toda la app
- Pagina "Gimnasios" renombrada a "Negocios"

### Custom Domain (Abril 2026)
- Campo custom_domain por tenant con login branded
- Resolucion de dominio via /api/gyms/resolve-domain/{domain}
- Hook useCustomDomain para deteccion automatica
- Dominio personalizado botwtsp.com funcionando en produccion
- Guia completa de configuracion de dominios personalizados (GUIA_DOMINIOS_PERSONALIZADOS.md)
- Script de actualizacion masiva para multiples dominios

## P1 - Pendiente
1. Portal de registro publico mejorado (landing page independiente)
2. Check-in de asistencia a clases (trainers marcan asistencia)

## P2 - Futuro
- Push Notifications reales (Firebase/PWA Push API)
- Dashboard mejorado para Trainers
- Chat trainer-socio
- Reportes PDF exportables adicionales

## Notas de Despliegue
- git clone SOLO actualiza backend .py files
- Frontend requiere yarn build + subir build/ a Plesk manualmente
- Backend: c.ingresoqr.com (proxy a :8001)
- Frontend: app.ingresoqr.com (static build en httpdocs/)
- Dominios personalizados: copiar build a httpdocs/ del dominio + .htaccess + SSL Let's Encrypt
- Script masivo disponible para actualizar todos los dominios a la vez
