# GymAccess - PRD

## Fecha: 24/03/2026

## Problem Statement
Sistema SaaS multi-tenant de control de acceso para gimnasios.

## Funcionalidades Implementadas
- Panel Admin con dashboard, gestión de gyms/socios/planes/clases/horarios/personal
- CRUD de Gimnasios con Editar/Suspender/Eliminar (con confirmación)
- PWA para socios: QR dinámico, reservas, notificaciones, invitados
- Roles: super_admin, gym_admin, gym_manager, trainer
- Raspberry Pi: script de control de tornos con relés GPIO
- Badge "Made with Emergent" eliminado
- Sidebar scrollable
- Notificaciones: fix para super_admin sin gym_id
- Build de producción compilado para gym.ticketpro.es / gymapi.ticketpro.es

## Credenciales
- Super Admin: admin@gymaccess.com / admin123
- Trainer: carlos@trainer.com / trainer123
- Member: LRF4HL

## Bugs Corregidos
- Schedule creation: SelectItem value="" → "default"
- Notificaciones: super_admin sin gym_id → selector de gym agregado
- Sidebar overflow → scrollbar-thin
- Badge Emergent → eliminado de index.html

## Backlog
### P1
- SMTP real para emails
- Cron para recordatorios de expiración
- Vista mejorada para trainers

### P2
- Check-in de asistencia
- Push notifications (Firebase)
- Reportes PDF

### P3
- App nativa
- Wearables
- Gamificación
