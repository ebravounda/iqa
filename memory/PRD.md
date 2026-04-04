# IngresoQR - PRD (Product Requirements Document)

## Problema Original
Sistema SaaS multi-tenant de control de acceso para gimnasios, condominios, hoteles, etc. con QR dinámico, control de torniquetes (Raspberry Pi), pagos Stripe, roles multi-tier, PWA para socios y panel admin.

## Arquitectura
- **Backend**: FastAPI + MongoDB (rutas en `/app/backend/routes/`)
- **Frontend**: React + Tailwind + Shadcn UI
- **Producción**: EC2 con Plesk (`c.ingresoqr.com` backend, `app.ingresoqr.com` frontend)

## Notas de Despliegue
- Backend actualizar: `cd /opt/gymaccess && git pull origin main && git checkout -- backend/ && sudo systemctl restart gymaccess-api`
- **Frontend ruta real**: `/var/www/vhosts/ingresoqr.com/app.ingresoqr.com/`
- Frontend deploy: `\cp -rf /opt/gymaccess/frontend/build/* /var/www/vhosts/ingresoqr.com/app.ingresoqr.com/ && chown -R ingresoqr:psaserv /var/www/vhosts/ingresoqr.com/app.ingresoqr.com/`
- Comando completo: `cd /opt/gymaccess && git pull origin main && git checkout -- backend/ && sudo systemctl restart gymaccess-api && \cp -rf frontend/build/* /var/www/vhosts/ingresoqr.com/app.ingresoqr.com/ && chown -R ingresoqr:psaserv /var/www/vhosts/ingresoqr.com/app.ingresoqr.com/`
- La carpeta /opt/gymaccess/routes/ es symlink a /opt/gymaccess/backend/routes/
- Dominios personalizados: `sudo cp -rf /var/www/vhosts/ingresoqr.com/app.ingresoqr.com/* /var/www/vhosts/botwtsp.com/httpdocs/`

## Features Completadas

### Core (Sesiones anteriores)
- JWT Authentication multi-tier (Super Admin, Gym Admin, Manager, Trainer)
- QR dinámico con refresh configurable (5/10/15s)
- Control de torniquetes via Raspberry Pi + API
- Stripe payments (tenant-specific keys)
- PWA para socios (QR, clases, perfil, stats, gamificación)
- Panel Admin (Dashboard, Socios, Planes, Clases, Horarios, Accesos, Dispositivos)
- Multi-tenant: cada gym/negocio tiene su propio admin y datos aislados
- WHMCS integration para billing automatizado
- Colores corporativos por negocio
- TPV/POS con categorías, carrito, estadísticas
- RFID para tarjetas/llaveros físicos
- Ocupación en tiempo real en Dashboard
- Auto-approve members toggle
- Avatar upload para socios

### Sesión 4 Abr 2026
- Diferenciación de suspensión: manual (cierre sesión inmediato) vs pago (permite login para pagar)
- Chequeo periódico 30s para detectar suspensiones en tiempo real
- Pago manual reactiva automáticamente socios suspendidos/pendientes
- Banner PWA "Instalar App" (Android nativo + iOS instrucciones), dismissible, toggle por negocio
- Cambiar credenciales gym admin desde Super Admin
- Eliminar categorías POS
- Hora local en ventas POS
- Scroll en modal dispositivos de socio
- Soft-delete dispositivos con historial últimos 8
- Avatar PWA con cache-busting
- Filtro active:True en categorías POS

## Backlog Priorizado

### P1 - Próximas
- Portal de registro público / landing page por negocio (slideshow, tarifas, auto-registro)
- Check-in de asistencia a clases

### P2 - Futuras
- Push Notifications reales (Firebase/PWA Push API)
- Chat trainer-socio
- Reportes PDF exportables
- Dashboard mejorado para Trainers

### Sesion 5 Abr 2026
- Fix modulo WHMCS 7.9.0: reescritura completa de ingresoqr.php con logging robusto a archivo local, limpieza de configoptions dropdown, boton "Test Provision Manual" en admin WHMCS, endpoint /api/whmcs/diagnostico
- Backend: eliminado patron Header(alias=...) problematico, ahora usa x_whmcs_key: str = Header(None) directo
- Backend: logging detallado en provision (request + resultado + errores)
- Backend: try/catch con error 500 explícito en provision

### Bug Conocido
- "Save to Github" de Emergent solo empuja .emergent/emergent.yml y .gitignore (reportado a soporte)
