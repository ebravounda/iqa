# GymAccess - PRD (Product Requirements Document)

## Problema Original
Sistema SaaS multi-tenant de control de acceso para gimnasios. Incluye dashboard admin, PWA para socios, QR dinamicos/estaticos, pagos Stripe y MercadoPago, POS (TPV), formularios personalizados, avatares de perfil, analytics, roles multi-nivel, reservas de clases, y script para Raspberry Pi con control de torniquetes.

## Arquitectura
- **Backend**: FastAPI (Python) modular con APIRouter
- **Frontend**: React + Tailwind + Shadcn UI
- **Base de datos**: MongoDB
- **Auth**: JWT + Permisos granulares por rol
- **Multi-tenant**: Super Admin (gym_id=null), Gym Admin (gym_id=UUID), Gym Manager (permisos configurables)

### Estructura Backend
```
/app/backend/
  server.py, database.py, auth.py (+ check_permission), models.py, qr_utils.py, storage.py
  routes/ (auth, gym, member, plan, access, device, payment, class/staff,
           notification_guest, accounting, saas, pos, mercadopago, upload, form, analytics, misc, device_member)
```

## Roles y Permisos
- **Super Admin**: Control total. Bypass de todos los permisos.
- **Gym Admin**: Control total sobre su gimnasio. Bypass de permisos. Crea/configura gestores.
- **Gym Manager (Gestor)**: Permisos granulares configurables.
  - Por defecto: Ver/Crear/Editar socios, Registrar pagos, Ventas TPV, Ver accesos, Gestionar clases
  - Requiere activacion: Eliminar socios, Suspender socios, Gestionar productos TPV, Exportar datos, Enviar notificaciones
- **Trainer**: Dashboard propio con clases asignadas, check-in de asistentes, estadisticas semanales.

### Catalogo de Permisos (12 total)
| Permiso | Default | Endpoint protegido |
|---------|---------|-------------------|
| members_view | Si | GET /api/members |
| members_create | Si | POST /api/members |
| members_edit | Si | PUT /api/members/{id} |
| members_delete | No | DELETE /api/members/{id} |
| members_suspend | No | POST /api/members/{id}/suspend |
| payments_register | Si | POST /api/memberships |
| pos_sell | Si | POST /api/pos/sales |
| pos_products | No | POST/DELETE /api/pos/products |
| access_view | Si | GET /api/access-logs |
| classes_manage | Si | POST /api/classes |
| data_export | No | GET /api/members/export/excel |
| notifications_send | No | POST /api/notifications |

## Funcionalidades Implementadas

### Core (Fases 1-8)
- Auth JWT, QR dinamicos/estaticos, Raspberry Pi anti-passback
- CRUD gimnasios/socios/planes/membresias, Clases/horarios/reservas
- Notificaciones, pases invitado, Email SMTP, Kiosko registro
- Backend refactorizado de monolito a modulos APIRouter
- Planes SaaS, Multi-moneda, TPV/POS, MercadoPago
- Contabilidad avanzada (PDF, retiros caja), Iframes, Broadcast
- Formularios personalizados, Avatares (Object Storage), Analytics dashboard

### Fase 9: Exportacion de Datos (2026-02-28)
- Columna telefono en tabla socios, Menu "Datos" con Excel export

### Fase 10: Filtros Excel + Imagenes POS (2026-02-28)
- Filtros: estado, fechas, incluir membresias. Imagenes de productos POS

### Fase 11: Tabla de Socios Rediseniada (2026-02-28)
- Tabla compacta sin scroll horizontal, popover de contacto, acciones siempre visibles

### Fase 12: Sistema de Permisos Granulares (2026-03-26)
- 12 permisos configurables por gestor (gym_manager)
- Backend: check_permission() en endpoints sensibles
- Frontend: hasPermission() oculta acciones sin permiso
- Sidebar filtra menu segun permisos del gestor
- Modal de permisos con toggles agrupados (Socios, Pagos, Operaciones)
- Barra visual de permisos activos en cards de gestores
- Cuentas desactivadas bloqueadas en login (HTTP 403)

### Fase 13: Control de Dispositivos y Estadisticas (2026-03-26)
- Device fingerprinting para socios en la PWA
- Limite de dispositivos configurable por gym (max_devices_per_member)
- Modal admin para ver/revocar dispositivos de un socio
- Estadisticas de visitas personales en la PWA (MemberStats)

### Fase 14: Automatizacion y Dashboard Trainer (2026-03-26)
- Auto-suspension de membresias vencidas via CRON a medianoche UTC
- Emails automaticos de recordatorio 1/3/7 dias antes del vencimiento
- Dashboard especifico para Trainers (clases del dia, check-in, stats semanales, proximas clases)
- Navegacion por fechas en pagina de Asistencia (prev/next day)
- Guia paso a paso para publicar la PWA en Google Play (GUIA_GOOGLE_PLAY.md)

## Credenciales
- Super Admin: admin@gymaccess.com / admin123
- Test Manager: maria@test.com / manager123

## Integraciones 3P
- Stripe (Payments) - MOCKED
- MercadoPago (Payments) - REAL
- Emergent Object Storage (Fotos perfil + productos)

## Backlog Pendiente

### P2
- Push notifications reales (Firebase/PWA Push API)

### P3
- Facturacion SaaS automatica
- App nativa, Wearables, Gamificacion
