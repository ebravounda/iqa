# IngresoQR - PRD (Product Requirements Document)

## Problema Original
Sistema SaaS multi-tenant de control de acceso para gimnasios con dashboard admin, PWA para socios, QR, pagos Stripe/MercadoPago, POS, analytics, roles multi-nivel, y control de torniquetes via Raspberry Pi.

## Dominios de Produccion
- **Frontend**: https://app.ingresoqr.com
- **Backend API**: https://c.ingresoqr.com

## Version Actual: V 1.3.2

## Funcionalidades Implementadas (Resumen)
- Core: Auth JWT, QR dinamicos/estaticos, Raspberry Pi anti-passback, CRUD completo
- Clases, Notificaciones, Email SMTP, Kiosko registro
- POS/TPV, MercadoPago, Stripe real multi-tenant
- Contabilidad, Iframes, Broadcast, Formularios, Avatares
- Permisos granulares RBAC, Analytics, Exportacion datos
- Monitor RPi Heartbeat, Gamificacion, Rutinas, Demo accounts
- Sistema seguridad (Rate limiting, IP blocking)

### Fase 18: Modo Dark/Light (27 Mar 2026)
- CSS Variables + overrides globales Tailwind zinc + text-white

### Fase 19: Sistema Facturacion SaaS (27 Mar 2026)
- Planes SaaS con 12 features configurables, precios, asignacion a gyms
- Planes membresia agrupados por gym para Super Admin
- Seccion "Mi Plan SaaS" en Settings del Gym Admin
- Suscripcion Stripe SaaS (requiere PLATFORM_STRIPE_KEY)

### Fase 20: Suspension por Impago (27 Mar 2026)
- PUT /api/gyms/{id}/payment-suspend toggle suspension
- Gym Admin: pantalla fullscreen "Cuenta Suspendida por falta de pago"
- Socios: pantalla "Cuenta Bloqueada" al intentar login
- QR Raspberry Pi: acceso denegado "Gimnasio suspendido por falta de pago"
- Badge "IMPAGO" naranja en tarjeta del gym (Super Admin)
- Dropdown: "Suspender por Impago" / "Reactivar (Pago recibido)"
- Testing: iteration_20.json - 12/12 tests pasados

## Variables de Entorno Backend
- MONGO_URL, DB_NAME
- PLATFORM_STRIPE_KEY (clave Stripe del propietario para cobrar a gyms)

## Credenciales Test
- Super Admin: admin@ingresoqr.com / admin123
- Gym Admin: admin@fitzone.com / admin123

## Backlog Pendiente
- P1: Portal de registro publico (auto-registro + pago online)
- P1: Check-in de clases reservadas
- P2: Push notifications reales (Firebase)
- P3: Chat trainer-socio | Reportes PDF
