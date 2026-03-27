# IngresoQR - PRD (Product Requirements Document)

## Problema Original
Sistema SaaS multi-tenant de control de acceso para gimnasios. Incluye dashboard admin, PWA para socios, QR dinamicos/estaticos, pagos Stripe y MercadoPago, POS (TPV), formularios personalizados, avatares de perfil, analytics, roles multi-nivel, reservas de clases, y script para Raspberry Pi con control de torniquetes.

## Dominios de Produccion
- **Frontend**: https://app.ingresoqr.com
- **Backend API**: https://c.ingresoqr.com

## Version Actual: V 1.3.1

## Arquitectura
- **Backend**: FastAPI (Python) modular con APIRouter
- **Frontend**: React + Tailwind + Shadcn UI
- **Base de datos**: MongoDB
- **Auth**: JWT + Permisos granulares por rol
- **Multi-tenant**: Super Admin (gym_id=null), Gym Admin (gym_id=UUID)

## Procedimiento de Actualizacion
1. Frontend: yarn build (con REACT_APP_BACKEND_URL=https://c.ingresoqr.com), Guardar en Github, subir build/ a Plesk
2. Backend: Subir archivos a Plesk, SSH: sudo /opt/gymaccess/actualizar.sh

## Funcionalidades Implementadas

### Core (Fases 1-17): Ver historial completo
- Auth JWT, QR, Raspberry Pi, CRUD, Clases, Notificaciones, POS, Email
- Permisos granulares, Analytics, Gamificacion, Rutinas, Demo, Stripe real

### Fase 18: Modo Dark/Light (27 Mar 2026)
- CSS Variables + overrides globales Tailwind zinc
- Toggle en AdminLayout y PWALayout con localStorage
- Override text-white con excepciones para botones de color

### Fase 19: Sistema de Facturacion SaaS (27 Mar 2026)
- **Planes SaaS**: CRUD con 12 caracteristicas configurables (QR, Invitados, Clases, POS, Analytics, Gamificacion, Rutinas, SMTP, Stripe, MercadoPago, Iframes, Contabilidad)
- **AdminPlans**: Planes de membresia agrupados por gimnasio para Super Admin
- **AdminSaaSPlans**: Gestion de planes SaaS con badges, precios, asignacion a gyms
- **Mi Plan SaaS**: Seccion en Settings del Gym Admin mostrando plan contratado, barra de capacidad, lista de features con checks
- **Stripe SaaS Subscription**: Endpoint para que Gym Admin pague su plan via Stripe (requiere PLATFORM_STRIPE_KEY en .env del backend)
- **Webhook**: POST /api/saas/stripe-webhook para activar planes automaticamente
- Testing: iteration_19.json - 18/18 tests pasados

## Credenciales
- Super Admin: admin@ingresoqr.com / admin123
- Gym Admin: admin@fitzone.com / admin123 (FitZone Gym, Plan Profesional)

## Variables de Entorno Necesarias (Backend)
- MONGO_URL, DB_NAME (existentes)
- PLATFORM_STRIPE_KEY (NUEVO - clave Stripe del propietario de la plataforma para cobrar a los gyms)

## Integraciones
- Stripe (Pagos socios) - Cada gym configura su propia API key
- Stripe (SaaS billing) - Platform key cobra a los gyms
- MercadoPago (Pagos socios) - Cada gym configura su token

## Backlog Pendiente
- P1: Portal de registro publico (auto-registro + pago online)
- P1: Check-in de clases reservadas
- P2: Push notifications reales (Firebase)
- P3: Chat directo entre trainers y socios
- P3: Reportes PDF exportables
