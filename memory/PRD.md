# GymAccess - Sistema SaaS de Control de Acceso para Gimnasios

## Fecha de última actualización: 24/03/2026

## Problem Statement Original
Sistema SaaS de control de acceso para gimnasios multi-tenant con:
- Panel Admin para gestionar múltiples gimnasios, socios, membresías, clases, horarios
- Sistema de roles: Super Admin, Admin de Gym, Gestor, Entrenador
- PWA para socios con QR dinámico y reserva de clases
- Integración con Raspberry Pi para control de tornos
- Pagos online con Stripe
- Emails configurables con plantillas editables

## Arquitectura SaaS Multi-Tenant
```
Super Admin (TÚ)
    └── Gym 1 (FitZone)
    │       ├── Admin
    │       ├── Gestores
    │       ├── Entrenadores
    │       └── Socios
    └── Gym 2 (otro gym)
    │       ├── ...
    └── Gym N...
```

## Sistema de Roles

| Rol | Permisos |
|-----|----------|
| **super_admin** | Todo: todos los gyms, configuración global, crear gyms |
| **gym_admin** | Su gym: todo, incluyendo configuración, personal, dispositivos |
| **gym_manager** | Su gym: socios, clases, horarios, accesos (sin config ni personal) |
| **trainer** | Solo ver sus clases asignadas y lista de asistentes |

## Funcionalidades Implementadas ✅

### Panel de Administración
- [x] Dashboard con estadísticas (socios, accesos, ingresos, clases)
- [x] Gestión de gimnasios (Super Admin)
- [x] Gestión de socios (CRUD, aprobar, bloquear)
- [x] Planes de membresía
- [x] **Sistema de Clases** (crear clases recurrentes o únicas)
- [x] **Horarios de Clases** (vista semanal, agregar horarios)
- [x] **Gestión de Personal** (crear admins, gestores, entrenadores)
- [x] Historial de accesos con filtros y exportación
- [x] Configuración de Raspberry Pi
- [x] Plantillas de email personalizables
- [x] Configuración de branding

### Sistema de Reservas
- [x] Clases recurrentes (días de la semana)
- [x] Clases únicas (fecha específica)
- [x] Capacidad máxima configurable
- [x] Asignación de entrenador
- [x] Generación automática de horarios (4 semanas)
- [x] Lista de asistentes por clase
- [x] Reserva desde PWA
- [x] Cancelación de reservas

### PWA para Socios
- [x] QR dinámico con countdown
- [x] **Reserva de clases** (vista semanal, reservar, cancelar)
- [x] Historial de accesos
- [x] Información de membresía
- [x] Renovación con Stripe
- [x] Botón "Crear Acceso Directo"
- [x] Branding dinámico por gimnasio

### Backend/API
- [x] Autenticación JWT con roles
- [x] CRUD completo (gyms, members, plans, classes, schedules, bookings)
- [x] QR dinámico encriptado
- [x] Validación para Raspberry Pi
- [x] Stripe para pagos

## Credenciales de Prueba

| Usuario | Email | Contraseña | Rol |
|---------|-------|------------|-----|
| Super Admin | admin@gymaccess.com | admin123 | super_admin |
| Entrenador | carlos@trainer.com | trainer123 | trainer |
| Socio | - | Código: LRF4HL | member |

## Backlog

### P1 - Alta Prioridad
- [ ] Vista específica para entrenadores (mejorar UX)
- [ ] SMTP real para envío de emails
- [ ] Cron para recordatorios automáticos

### P2 - Media Prioridad  
- [ ] Check-in de asistencia en clases (confirmar que el socio llegó)
- [ ] Notificaciones push
- [ ] Reportes avanzados con gráficos
- [ ] Exportación PDF

### P3 - Baja Prioridad
- [ ] App nativa (migrar PWA a React Native)
- [ ] Integración con wearables
- [ ] Gamificación (logros, puntos)

## Próximos Pasos Inmediatos
1. Configurar SMTP para emails reales
2. Probar flujo completo de entrenador
3. Desplegar en servidor de producción
4. Configurar Raspberry Pi física
