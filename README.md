# GymAccess - Sistema de Control de Acceso para Gimnasios

Sistema completo de control de acceso con QR dinámico, panel de administración y app PWA para socios.

## 🚀 Características

- **Panel de Administración**
  - Dashboard con estadísticas en tiempo real
  - Gestión de socios (crear, aprobar, bloquear)
  - Planes de membresía configurables
  - Historial de accesos con filtros y exportación
  - Configuración de dispositivos Raspberry Pi
  - Plantillas de email personalizables
  - Soporte multi-gimnasio

- **App PWA para Socios**
  - QR dinámico que cambia cada 5-15 segundos
  - Historial de accesos personal
  - Renovación de membresía con Stripe
  - Instalable en Android/iOS
  - Branding personalizado por gimnasio

- **Raspberry Pi**
  - Control de tornos con relés
  - Validación de QR en tiempo real
  - Modo offline con cache local
  - Heartbeat al servidor

## 📋 Credenciales por Defecto

- **Admin**: admin@gymaccess.com / admin123

## 🔧 Configuración de Raspberry Pi

### Hardware Necesario
- Raspberry Pi 3B+ o superior
- Módulo de 2 relés 5V
- Lector de códigos QR USB
- Fuente de alimentación 5V 3A

### Conexiones GPIO
```
Raspberry Pi          Módulo Relé
GPIO 17      ───────> IN1 (Entrada)
GPIO 27      ───────> IN2 (Salida)
GND          ───────> GND
5V           ───────> VCC
```

### Instalación
```bash
# 1. Actualizar sistema
sudo apt-get update && sudo apt-get upgrade -y

# 2. Instalar dependencias
sudo apt-get install python3-pip python3-rpi.gpio -y
pip3 install requests python-dotenv

# 3. Descargar script
wget https://tu-servidor.com/raspberry_access_control.py

# 4. Configurar variables
export GYMACCESS_SERVER_URL="https://tu-servidor.com"
export GYMACCESS_GYM_TOKEN="tu_token_aqui"
export GYMACCESS_DEVICE_ID="tu_device_id"

# 5. Ejecutar
python3 raspberry_access_control.py
```

## 🔐 Seguridad del QR

El código QR dinámico incluye:
- ID del socio encriptado
- Timestamp de generación
- Firma HMAC-SHA256
- Tiempo de expiración configurable (5-30 segundos)

Esto evita:
- Capturas de pantalla fraudulentas
- Compartir códigos entre socios
- Reutilización de códigos

## 💳 Pagos con Stripe

Los socios pueden renovar su membresía directamente desde la app con tarjeta de crédito/débito.

## 📧 Plantillas de Email

Plantillas configurables para:
- Bienvenida al registrarse
- Recordatorio de vencimiento (10, 5, 3 días)
- Membresía vencida
- Confirmación de pago

Variables disponibles:
- `{gym_name}` - Nombre del gimnasio
- `{member_name}` - Nombre del socio
- `{member_code}` - Código del socio
- `{expiry_date}` - Fecha de vencimiento
- `{plan_name}` - Nombre del plan
- `{amount}` - Monto del pago

## 🌐 API Endpoints

### Autenticación
- `POST /api/auth/admin/login` - Login administrador
- `POST /api/auth/member/login?code=XXXXXX` - Login socio

### Socios
- `GET /api/members` - Listar socios
- `POST /api/members` - Crear socio
- `PUT /api/members/{id}` - Actualizar socio
- `POST /api/members/{id}/approve` - Aprobar socio
- `POST /api/members/{id}/block` - Bloquear socio

### Acceso
- `POST /api/access/validate` - Validar QR (Raspberry Pi)
- `GET /api/access/logs` - Historial de accesos
- `GET /api/qr/generate` - Generar QR dinámico

### Pagos
- `POST /api/payments/checkout?plan_id=X` - Crear sesión de pago
- `GET /api/payments/status/{session_id}` - Estado del pago

## 📱 PWA - Crear Acceso Directo

La app detecta automáticamente si puede instalarse y muestra un banner para crear un acceso directo en la pantalla del móvil.

En dispositivos Android/iOS, el usuario puede:
1. Tocar "Crear Acceso Directo"
2. Aceptar la instalación
3. La app aparecerá en la pantalla de inicio

## 🎨 Personalización

Cada gimnasio puede personalizar:
- Logo
- Color principal (afecta toda la app)
- Plantillas de email
- Tiempo de refresco del QR

## 📊 Reportes

- Accesos por día/semana/mes
- Socios activos
- Membresías por vencer
- Ingresos mensuales
- Exportación a CSV
