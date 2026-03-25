# GymAccess - PRD

## Última actualización: 25/03/2026

## Problem Statement
Sistema SaaS multi-tenant de control de acceso para gimnasios con QR dinámico/estático, pagos Stripe + efectivo + tarjeta, módulo kiosko, contabilidad con PDF, plantillas de email editables, check-in de asistencia, y control de tornos con Raspberry Pi.

## Todas las Funcionalidades Implementadas

### Core
- Panel Admin completo con 14 módulos en sidebar
- PWA responsive para socios
- Roles: super_admin, gym_admin, gym_manager, trainer
- JWT Authentication + Impersonación
- Raspberry Pi con GPIO para tornos

### SaaS Multi-tenant
- Stripe por gym, SMTP por gym, plantillas email por gym
- Auto-creación de gym admin
- Impersonación de gym

### QR y Accesos
- QR Dinámico/Estático (configurable por gym)
- Exportación a Excel (XLSX)
- Logs detallados con gráficos

### Módulo Kiosko
- Página `/kiosk/{gymId}` optimizada para tablets
- Registro presencial, envío de email con código
- Auto-reset de pantalla tras 30 segundos

### Contabilidad
- Dashboard financiero con gráficos por día y método de pago
- Filtros rápidos (7d, semana, mes, todo) + rango fechas
- Export a PDF con ReportLab
- Tabla de transacciones detallada

### Pagos Manuales
- Efectivo y tarjeta en recepción desde panel admin
- Modal en vista de Socios con selector de plan y método
- Activa membresía y reactiva socios suspendidos

### Plantillas Email
- 6 plantillas editables por gym (bienvenida, vencimiento, pago)
- Variables dinámicas ({gym_name}, {member_name}, {member_code}, etc.)
- Panel de referencia de variables

### Check-in de Asistencia
- Página `/admin/attendance` para registrar asistencia
- Botones check-in/anular por reserva
- Barra de progreso

## Credenciales
- Super Admin: admin@gymaccess.com / admin123
- Gym Admin FitZone: admin@fitzone.com / admin123

## Backlog
### P2
- Módulo Kiosko: aceptar pagos directos
- Planes SaaS con tiers para gimnasios
- Push notifications (Firebase)

### P3
- Reportes PDF avanzados, App nativa, Wearables, Gamificación
