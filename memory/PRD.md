# GymAccess - Sistema de Control de Acceso para Gimnasios

## Fecha: 24/03/2026

## Problem Statement Original
Sistema de control de acceso para gimnasios multi-tenant con:
- Panel Admin para gestionar socios, membresías, planes, accesos, dispositivos Raspberry Pi
- PWA para socios con QR dinámico (5-15 segundos configurable)
- Integración con Raspberry Pi 3B+ con 2 relés (entrada/salida)
- Pagos online con Stripe
- Emails configurables con plantillas editables
- Multi-gym: una app para todos los gimnasios con branding dinámico

## User Personas
1. **Super Admin**: Gestiona múltiples gimnasios
2. **Admin de Gimnasio**: Gestiona su propio gym, socios, planes
3. **Socio**: Usa la PWA para acceder con QR

## Arquitectura
- **Backend**: FastAPI + MongoDB
- **Frontend**: React + Tailwind + Shadcn
- **PWA**: Instalable en Android/iOS
- **Hardware**: Raspberry Pi 3B+ con módulo de 2 relés

## Funcionalidades Implementadas ✅

### Panel de Administración
- [x] Login con JWT
- [x] Dashboard con estadísticas
- [x] Gestión de gimnasios (Super Admin)
- [x] Gestión de socios (CRUD, aprobar, bloquear)
- [x] Planes de membresía configurables
- [x] Asignación de membresías
- [x] Historial de accesos con filtros y exportación CSV
- [x] Configuración de dispositivos Raspberry Pi
- [x] Plantillas de email personalizables
- [x] Configuración de branding (logo, color)
- [x] Configuración de tiempo QR (5/10/15/30 seg)

### PWA para Socios
- [x] Login con código de socio (6 caracteres)
- [x] QR dinámico con countdown visual
- [x] Modo pantalla completa para QR
- [x] Historial de accesos personal
- [x] Información de membresía
- [x] Renovación con Stripe
- [x] Perfil del socio
- [x] Botón "Crear Acceso Directo" (instalación PWA)
- [x] Branding dinámico por gimnasio

### Backend/API
- [x] Autenticación JWT para admin/socio
- [x] CRUD completo de gyms, members, plans, memberships
- [x] Generación de QR dinámico encriptado
- [x] Endpoint de validación para Raspberry Pi
- [x] Logs de acceso
- [x] Estadísticas de dashboard
- [x] Integración Stripe para pagos

### Raspberry Pi
- [x] Script Python completo
- [x] Control de GPIO para relés
- [x] Validación de QR contra servidor
- [x] Heartbeat/ping al servidor
- [x] Documentación de instalación

## Backlog P0/P1/P2

### P0 - Crítico
- (Completado)

### P1 - Alta Prioridad
- [ ] Sistema de emails real (SMTP)
- [ ] Cron job para enviar recordatorios de vencimiento
- [ ] Notificaciones push en PWA

### P2 - Media Prioridad
- [ ] Reportes avanzados con gráficos
- [ ] Exportación de datos a PDF
- [ ] Sistema de backup de datos
- [ ] Modo offline mejorado para Raspberry Pi
- [ ] Panel de recepcionista (rol intermedio)

## Credenciales por Defecto
- Admin: admin@gymaccess.com / admin123
- Test Member Code: LRF4HL

## Próximos Pasos
1. Configurar SMTP real para emails
2. Implementar cron para recordatorios automáticos
3. Agregar más reportes y estadísticas
4. Probar en Raspberry Pi física
