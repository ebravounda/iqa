# GymAccess - PRD

## Última actualización: 25/03/2026

## Problem Statement
Sistema SaaS multi-tenant de control de acceso para gimnasios con QR dinámico/estático, pagos con Stripe, roles multi-tenant, página de auto-registro público, check-in de asistencia, SMTP por gym, y control de tornos con Raspberry Pi.

## Funcionalidades Implementadas

### Core
- Panel Admin completo: dashboard, gestión de gyms/socios/planes/clases/horarios/personal
- PWA para socios: QR dinámico/estático, reservas, notificaciones, invitados
- Roles: super_admin, gym_admin, gym_manager, trainer
- JWT Authentication + Impersonación
- Raspberry Pi: script de control de tornos con relés GPIO (evdev + RPi.GPIO)

### SaaS Multi-tenant
- Configuración de Stripe por Gimnasio
- Configuración SMTP por Gimnasio (emails automáticos)
- Auto-creación de gym admin al crear gimnasio
- Impersonación: Super Admin puede "Iniciar sesión como Admin" en cualquier gym

### QR y Accesos
- QR Dinámico (cambia cada X segundos) y Estático (código fijo)
- Opción configurable por gym
- Gráficos de accesos en Dashboard
- Estadísticas de acceso por socio
- Auto-suspensión de membresías expiradas
- Exportación a Excel (XLSX)

### Check-in de Asistencia
- Página /admin/attendance para registrar asistencia a clases
- Botones de check-in/anular por reserva
- Barra de progreso de asistencia
- Accesible para trainers también

### Email (SMTP por gym)
- Configuración SMTP en panel del gym admin
- Email de bienvenida con código QR
- Botón de prueba SMTP
- Soporte TLS/SSL

### Registro Público
- Página /register/{gym_id} para auto-registro de socios
- Selección de plan, registro inmediato con código QR
- Enlace copiable en configuración del gym

## Credenciales
- Super Admin: admin@gymaccess.com / admin123
- Gym Admin FitZone: admin@fitzone.com / admin123

## DB Collections
gyms, admins, members, memberships, plans, classes, class_schedules, bookings, notifications, guests, access_logs, devices, payment_transactions

## Backlog
### P2
- Módulo Kiosko (controlado por super admin por gym)
- Planes SaaS con tiers para gimnasios
- Vista mejorada para trainers
- Push notifications (Firebase)

### P3
- Reportes PDF, App nativa, Wearables, Gamificación
