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
           notification_guest, accounting, saas, pos, mercadopago, upload, form, analytics, misc)
```

## Roles y Permisos
- **Super Admin**: Control total. Bypass de todos los permisos.
- **Gym Admin**: Control total sobre su gimnasio. Bypass de permisos. Crea/configura gestores.
- **Gym Manager (Gestor)**: Permisos granulares configurables.
  - Por defecto: Ver/Crear/Editar socios, Registrar pagos, Ventas TPV, Ver accesos, Gestionar clases
  - Requiere activacion: Eliminar socios, Suspender socios, Gestionar productos TPV, Exportar datos, Enviar notificaciones
- **Trainer**: Ve sus clases y asistencia.

### Catálogo de Permisos (12 total)
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

### Fase 11: Tabla de Socios Rediseñada (2026-02-28)
- Tabla compacta sin scroll horizontal, popover de contacto, acciones siempre visibles

### Fase 12: Sistema de Permisos Granulares (2026-03-26)
- 12 permisos configurables por gestor (gym_manager)
- Backend: check_permission() en endpoints sensibles
- Frontend: hasPermission() oculta acciones sin permiso
- Sidebar filtra menu segun permisos del gestor
- Modal de permisos con toggles agrupados (Socios, Pagos, Operaciones)
- Barra visual de permisos activos en cards de gestores
- Cuentas desactivadas bloqueadas en login (HTTP 403)

## Credenciales
- Super Admin: admin@gymaccess.com / admin123
- Test Manager: maria@test.com / manager123

## Integraciones 3P
- Stripe (Payments) - MOCKED
- MercadoPago (Payments) - REAL
- Emergent Object Storage (Fotos perfil + productos)

## Backlog Pendiente

### P1
- Emails recordatorio vencimiento membresia
- Check-in asistencia a clases

### P2
- Dashboards para Trainers
- Push notifications (Firebase/PWA)
- Endpoint para desactivar/activar gestores via API (actualmente solo trainers)

### P3
- Facturacion SaaS automatica
- App nativa, Wearables, Gamificacion
