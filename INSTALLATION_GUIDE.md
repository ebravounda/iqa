# 🚀 GUÍA COMPLETA DE INSTALACIÓN - GymAccess

## ÍNDICE
1. [Opción A: Despliegue en VPS con Docker (Recomendado)](#opción-a-vps-con-docker)
2. [Opción B: Despliegue en Plesk](#opción-b-despliegue-en-plesk)
3. [Opción C: Servicios Cloud Gratuitos](#opción-c-servicios-cloud-gratuitos)
4. [Configuración de Raspberry Pi](#configuración-de-raspberry-pi)
5. [Configuración Post-Instalación](#configuración-post-instalación)

---

## OPCIÓN A: VPS CON DOCKER (Recomendado)
**Costo: $5-6/mes | Complejidad: Fácil | Tiempo: 15 minutos**

### Paso 1: Contratar un VPS
Opciones económicas:
- **DigitalOcean**: $6/mes (usa código EMERGENT para $200 gratis)
- **Vultr**: $5/mes
- **Hetzner**: €4.5/mes (más barato en Europa)
- **Contabo**: $5/mes

Requisitos mínimos:
- 1 CPU
- 1GB RAM
- 20GB SSD
- Ubuntu 22.04

### Paso 2: Conectar al VPS
```bash
ssh root@TU_IP_DEL_VPS
```

### Paso 3: Instalar Docker (copiar y pegar todo)
```bash
# Actualizar sistema
apt update && apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Instalar Docker Compose
apt install docker-compose -y

# Verificar instalación
docker --version
docker-compose --version
```

### Paso 4: Crear estructura del proyecto
```bash
# Crear directorio
mkdir -p /opt/gymaccess
cd /opt/gymaccess

# Crear archivo docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  mongodb:
    image: mongo:6
    container_name: gymaccess-mongo
    restart: always
    volumes:
      - mongodb_data:/data/db
    environment:
      MONGO_INITDB_DATABASE: gymaccess

  backend:
    image: python:3.11-slim
    container_name: gymaccess-backend
    restart: always
    working_dir: /app
    volumes:
      - ./backend:/app
    ports:
      - "8001:8001"
    environment:
      - MONGO_URL=mongodb://mongodb:27017
      - DB_NAME=gymaccess
      - JWT_SECRET=tu_clave_secreta_muy_larga_aqui_cambiar
      - QR_SECRET=tu_clave_qr_secreta_cambiar
      - STRIPE_API_KEY=sk_test_tu_clave_stripe
    depends_on:
      - mongodb
    command: >
      bash -c "pip install -r requirements.txt && 
               uvicorn server:app --host 0.0.0.0 --port 8001"

  frontend:
    image: node:18-alpine
    container_name: gymaccess-frontend
    restart: always
    working_dir: /app
    volumes:
      - ./frontend:/app
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_BACKEND_URL=https://api.tudominio.com
    command: >
      sh -c "yarn install && yarn build && 
             npx serve -s build -l 3000"

  nginx:
    image: nginx:alpine
    container_name: gymaccess-nginx
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./certbot/conf:/etc/letsencrypt
      - ./certbot/www:/var/www/certbot
    depends_on:
      - backend
      - frontend

volumes:
  mongodb_data:
EOF
```

### Paso 5: Crear configuración de Nginx
```bash
cat > nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Frontend
    server {
        listen 80;
        server_name tudominio.com www.tudominio.com;
        
        location / {
            proxy_pass http://frontend:3000;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_cache_bypass $http_upgrade;
        }
    }

    # API Backend
    server {
        listen 80;
        server_name api.tudominio.com;
        
        location / {
            proxy_pass http://backend:8001;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_cache_bypass $http_upgrade;
        }
    }
}
EOF
```

### Paso 6: Subir código al servidor
Desde tu computadora local:
```bash
# Descargar código de Emergent (botón "Download Code")
# Descomprimir y subir via SCP o SFTP

scp -r ./backend root@TU_IP:/opt/gymaccess/
scp -r ./frontend root@TU_IP:/opt/gymaccess/
```

### Paso 7: Iniciar servicios
```bash
cd /opt/gymaccess
docker-compose up -d

# Ver logs
docker-compose logs -f

# Verificar que todo está corriendo
docker-compose ps
```

### Paso 8: Configurar dominio
1. En tu proveedor de dominio, crear registros DNS:
   - `tudominio.com` → IP del VPS
   - `api.tudominio.com` → IP del VPS

### Paso 9: Instalar SSL (HTTPS)
```bash
# Instalar certbot
apt install certbot python3-certbot-nginx -y

# Obtener certificado
certbot --nginx -d tudominio.com -d api.tudominio.com

# Auto-renovación
certbot renew --dry-run
```

---

## OPCIÓN B: DESPLIEGUE EN PLESK
**Tu servidor Plesk no tiene Python, así que usaremos Docker**

### Paso 1: Habilitar Docker en Plesk
1. Entra al panel de Plesk
2. Ve a **Extensions** → **Catalog**
3. Busca **Docker** e instálalo
4. Ve a **Tools & Settings** → **Docker**

### Paso 2: Instalar MongoDB
1. En Docker, busca la imagen `mongo:6`
2. Click en **Run**
3. Configurar:
   - Puerto: 27017
   - Volume: `/var/lib/docker/mongo:/data/db`
4. Click **OK**

### Paso 3: Crear subdominios
1. Ve a **Websites & Domains**
2. Crea subdominio: `api.tudominio.com`
3. Crea subdominio: `app.tudominio.com`

### Paso 4: Opción alternativa - Node.js para Frontend
Si Plesk tiene Node.js:
1. Sube la carpeta `frontend` al subdominio `app.tudominio.com`
2. En **Node.js**, configura:
   - Document root: `/frontend`
   - Application startup file: `node_modules/.bin/serve`
   - Arguments: `-s build -l 3000`

### Paso 5: Backend con Docker
1. Crea imagen personalizada con Dockerfile
2. O usa servicio externo para el backend (ver Opción C)

**RECOMENDACIÓN**: Si tu Plesk no tiene Docker, usa la Opción C para el backend y solo el frontend en Plesk.

---

## OPCIÓN C: SERVICIOS CLOUD GRATUITOS
**Costo: $0 | Ideal para empezar**

### Backend en Railway.app (Gratis)
1. Ve a https://railway.app
2. Click **Start a New Project**
3. Selecciona **Deploy from GitHub repo**
4. Conecta tu repositorio con el código del backend
5. Agrega variables de entorno:
   ```
   MONGO_URL=mongodb+srv://...
   DB_NAME=gymaccess
   JWT_SECRET=tu_clave_secreta
   QR_SECRET=tu_clave_qr
   STRIPE_API_KEY=sk_test_...
   ```
6. Railway te dará una URL como: `gymaccess-backend.up.railway.app`

### Base de datos en MongoDB Atlas (Gratis)
1. Ve a https://cloud.mongodb.com
2. Crea cuenta gratuita
3. Create **New Cluster** (gratis hasta 512MB)
4. En **Database Access**, crea usuario
5. En **Network Access**, añade `0.0.0.0/0`
6. Click **Connect** → **Connect your application**
7. Copia la URL: `mongodb+srv://usuario:password@cluster.mongodb.net/gymaccess`

### Frontend en Vercel (Gratis)
1. Ve a https://vercel.com
2. Click **New Project**
3. Importa tu repositorio
4. Configura:
   - Framework: Create React App
   - Root Directory: `frontend`
   - Environment Variables:
     ```
     REACT_APP_BACKEND_URL=https://gymaccess-backend.up.railway.app
     ```
5. Click **Deploy**
6. Vercel te dará: `tuapp.vercel.app`

### Dominio personalizado (Opcional)
En Vercel/Railway, puedes agregar tu dominio personalizado gratis.

---

## CONFIGURACIÓN DE RASPBERRY PI

### Materiales necesarios
| Item | Precio | Dónde comprar |
|------|--------|---------------|
| Raspberry Pi 3B+ o 4 | Ya tienes | - |
| MicroSD 16GB+ | ~$8 | Amazon |
| Módulo 2 Relés 5V | ~$4 | Amazon, AliExpress |
| Lector QR USB | ~$20 | Amazon (buscar "barcode scanner USB") |
| Cables Dupont hembra-hembra | ~$3 | Amazon |
| Fuente 5V 3A | ~$10 | Amazon |

### Diagrama de conexión
```
╔═══════════════════════════════════════════════════════════════╗
║                     RASPBERRY PI 3B+                          ║
║  ┌─────────────────────────────────────────────────────────┐  ║
║  │                      GPIO HEADER                         │  ║
║  │  (lado izquierdo, pines impares)                        │  ║
║  │                                                          │  ║
║  │  Pin 1  (3.3V)  ○ ○  Pin 2  (5V) ────────┐              │  ║
║  │  Pin 3  (GPIO2) ○ ○  Pin 4  (5V)         │              │  ║
║  │  Pin 5  (GPIO3) ○ ○  Pin 6  (GND) ───────┼──┐           │  ║
║  │  Pin 7  (GPIO4) ○ ○  Pin 8               │  │           │  ║
║  │  Pin 9  (GND)   ○ ○  Pin 10              │  │           │  ║
║  │  Pin 11 (GPIO17)○ ○  Pin 12          ────┼──┼───┐       │  ║
║  │  Pin 13 (GPIO27)○ ○  Pin 14          ────┼──┼───┼──┐    │  ║
║  │  ...                                     │  │   │  │    │  ║
║  └─────────────────────────────────────────────────────────┘  ║
║         │                                   │  │   │  │       ║
║         │    USB                            │  │   │  │       ║
║         │    ┌──────┐                       │  │   │  │       ║
║         └────┤LECTOR│                       │  │   │  │       ║
║              │  QR  │                       │  │   │  │       ║
║              └──────┘                       │  │   │  │       ║
║                                             │  │   │  │       ║
╚═════════════════════════════════════════════╪══╪═══╪══╪═══════╝
                                              │  │   │  │
                    ┌─────────────────────────┘  │   │  │
                    │  ┌────────────────────────┘   │  │
                    │  │  ┌────────────────────────┘  │
                    │  │  │  ┌───────────────────────┘
                    │  │  │  │
                    ▼  ▼  ▼  ▼
              ╔═══════════════════════╗
              ║   MÓDULO 2 RELÉS      ║
              ║  ┌─────────────────┐  ║
              ║  │ VCC ←───────────┼──┤ (5V del Pi)
              ║  │ GND ←───────────┼──┤ (GND del Pi)
              ║  │ IN1 ←───────────┼──┤ (GPIO17 - Pin 11)
              ║  │ IN2 ←───────────┼──┤ (GPIO27 - Pin 13)
              ║  └────────┬────────┘  ║
              ║           │           ║
              ║     ┌─────┴─────┐     ║
              ║     │           │     ║
              ║   ┌─┴─┐       ┌─┴─┐   ║
              ║   │RE1│       │RE2│   ║
              ║   │   │       │   │   ║
              ║   │COM│       │COM│   ║
              ║   │NO │       │NO │   ║
              ║   │NC │       │NC │   ║
              ║   └─┬─┘       └─┬─┘   ║
              ║     │           │     ║
              ╚═════╪═══════════╪═════╝
                    │           │
                    ▼           ▼
              ┌─────────┐ ┌─────────┐
              │ TORNO   │ │ TORNO   │
              │ ENTRADA │ │ SALIDA  │
              │         │ │         │
              │ (Usa NO │ │ (Usa NO │
              │  y COM) │ │  y COM) │
              └─────────┘ └─────────┘
```

### Conexiones paso a paso

#### 1. Conectar el módulo de relés
```
RASPBERRY PI          MÓDULO RELÉ
═══════════════       ═══════════
Pin 2  (5V)    ────── VCC
Pin 6  (GND)   ────── GND
Pin 11 (GPIO17)────── IN1 (Relé Entrada)
Pin 13 (GPIO27)────── IN2 (Relé Salida)
```

#### 2. Conectar los tornos al relé
- Usa los terminales **NO** (Normally Open) y **COM** (Common)
- NO se cierra cuando el relé se activa
- Conecta estos al botón de apertura del torno

### Instalación del software

#### Paso 1: Instalar Raspberry Pi OS
1. Descarga **Raspberry Pi Imager** de: https://www.raspberrypi.com/software/
2. Inserta la MicroSD en tu computadora
3. En Imager:
   - Sistema: **Raspberry Pi OS Lite (64-bit)**
   - Almacenamiento: Tu MicroSD
   - Click en el engranaje ⚙️ para configurar:
     - Hostname: `gymaccess`
     - Enable SSH: ✓
     - Username: `pi`
     - Password: `tu_contraseña`
     - WiFi: (opcional, mejor usar cable)
4. Click **Write**

#### Paso 2: Primer arranque
1. Inserta la MicroSD en la Raspberry
2. Conecta el cable de red
3. Conecta la alimentación
4. Espera 2 minutos

#### Paso 3: Conectar por SSH
Desde tu computadora:
```bash
# En Windows: usa PuTTY o PowerShell
# En Mac/Linux: usa Terminal

ssh pi@gymaccess.local
# o usa la IP: ssh pi@192.168.1.XXX
```

#### Paso 4: Instalar dependencias
```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Python y pip
sudo apt install python3-pip python3-venv -y

# Instalar librería GPIO
sudo apt install python3-rpi.gpio -y

# Crear entorno virtual
python3 -m venv ~/gymaccess-env
source ~/gymaccess-env/bin/activate

# Instalar dependencias Python
pip install requests python-dotenv
```

#### Paso 5: Crear el script de control
```bash
# Crear directorio
mkdir -p ~/gymaccess
cd ~/gymaccess

# Crear archivo de configuración
cat > .env << 'EOF'
GYMACCESS_SERVER_URL=https://api.tudominio.com
GYMACCESS_GYM_TOKEN=TU_TOKEN_DEL_GYM
GYMACCESS_DEVICE_ID=TU_DEVICE_ID
GYMACCESS_QR_MODE=usb
EOF

# Crear script principal
cat > access_control.py << 'SCRIPT'
#!/usr/bin/env python3
"""
GymAccess - Control de Acceso con Raspberry Pi
"""

import os
import sys
import time
import logging
import threading
from datetime import datetime
from dotenv import load_dotenv

# Cargar configuración
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/gymaccess.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Importar GPIO
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    logger.warning("GPIO no disponible - modo simulación")
    GPIO_AVAILABLE = False

import requests

# Configuración
SERVER_URL = os.environ.get('GYMACCESS_SERVER_URL', 'https://api.tudominio.com')
GYM_TOKEN = os.environ.get('GYMACCESS_GYM_TOKEN', '')
DEVICE_ID = os.environ.get('GYMACCESS_DEVICE_ID', '')
QR_MODE = os.environ.get('GYMACCESS_QR_MODE', 'usb')

# Pines GPIO
RELAY_ENTRADA = 17
RELAY_SALIDA = 27
TIEMPO_APERTURA = 3

class AccessController:
    def __init__(self):
        self.running = True
        self.direccion = 'entrada'  # Por defecto entrada
        
        # Inicializar GPIO
        if GPIO_AVAILABLE:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            GPIO.setup(RELAY_ENTRADA, GPIO.OUT, initial=GPIO.HIGH)
            GPIO.setup(RELAY_SALIDA, GPIO.OUT, initial=GPIO.HIGH)
            logger.info("GPIO inicializado")
        
        # Iniciar ping thread
        self.ping_thread = threading.Thread(target=self._ping_loop, daemon=True)
        self.ping_thread.start()
    
    def _ping_loop(self):
        """Envía ping cada 60 segundos"""
        while self.running:
            try:
                requests.post(
                    f"{SERVER_URL}/api/devices/{DEVICE_ID}/ping",
                    params={"gym_token": GYM_TOKEN},
                    timeout=5
                )
            except:
                pass
            time.sleep(60)
    
    def abrir_torno(self, direccion):
        """Abre el torno por 3 segundos"""
        pin = RELAY_ENTRADA if direccion == 'entrada' else RELAY_SALIDA
        nombre = "ENTRADA" if direccion == 'entrada' else "SALIDA"
        
        logger.info(f"Abriendo torno {nombre}")
        
        if GPIO_AVAILABLE:
            GPIO.output(pin, GPIO.LOW)
            time.sleep(TIEMPO_APERTURA)
            GPIO.output(pin, GPIO.HIGH)
        else:
            time.sleep(TIEMPO_APERTURA)
        
        logger.info(f"Torno {nombre} cerrado")
    
    def validar_qr(self, qr_code):
        """Valida el QR con el servidor"""
        try:
            response = requests.post(
                f"{SERVER_URL}/api/access/validate",
                json={
                    "qr_code": qr_code,
                    "gym_token": GYM_TOKEN,
                    "direction": self.direccion
                },
                timeout=10
            )
            return response.json()
        except Exception as e:
            logger.error(f"Error: {e}")
            return {"valid": False, "reason": "Error de conexión"}
    
    def procesar_qr(self, qr_code):
        """Procesa un QR escaneado"""
        if not qr_code:
            return
        
        logger.info(f"QR escaneado: {qr_code[:20]}...")
        resultado = self.validar_qr(qr_code)
        
        if resultado.get('valid'):
            # Verificar si es invitado
            if resultado.get('is_guest'):
                nombre = resultado.get('guest_name', 'Invitado')
                invitado_de = resultado.get('invited_by', '')
                print(f"\n✅ INVITADO: {nombre}")
                print(f"   Invitado de: {invitado_de}\n")
            else:
                nombre = resultado.get('member_name', 'Socio')
                print(f"\n✅ BIENVENIDO: {nombre}\n")
            
            self.abrir_torno(resultado.get('direction', self.direccion))
        else:
            razon = resultado.get('reason', 'Desconocido')
            logger.warning(f"❌ DENEGADO: {razon}")
            print(f"\n❌ ACCESO DENEGADO: {razon}\n")
    
    def run(self):
        """Loop principal"""
        print("\n" + "="*50)
        print("   GYMACCESS - SISTEMA DE CONTROL DE ACCESO")
        print("="*50)
        print(f"   Servidor: {SERVER_URL}")
        print(f"   Modo: {QR_MODE}")
        print("="*50)
        print("   Esperando códigos QR...")
        print("="*50 + "\n")
        
        try:
            while self.running:
                # Leer QR desde scanner USB
                qr_code = input().strip()
                if qr_code:
                    self.procesar_qr(qr_code)
        except KeyboardInterrupt:
            print("\nCerrando...")
        finally:
            if GPIO_AVAILABLE:
                GPIO.cleanup()

if __name__ == '__main__':
    if not GYM_TOKEN:
        print("❌ Error: Configura GYM_TOKEN en .env")
        print("   Obtén el token en: Panel Admin → Dispositivos")
        sys.exit(1)
    
    controller = AccessController()
    controller.run()
SCRIPT

# Dar permisos de ejecución
chmod +x access_control.py
```

#### Paso 6: Configurar el token del gimnasio
1. Ve al panel de admin: `https://tudominio.com/admin`
2. Login como administrador
3. Ve a **Dispositivos** → **Agregar Dispositivo**
4. Copia el **Token de API** del gimnasio
5. Edita el archivo `.env`:
```bash
nano ~/gymaccess/.env
```
6. Pega tu token y guarda (Ctrl+X, Y, Enter)

#### Paso 7: Probar el sistema
```bash
cd ~/gymaccess
source ~/gymaccess-env/bin/activate
python3 access_control.py
```

Ahora escanea un QR desde la app de un socio. Deberías ver:
```
✅ BIENVENIDO: Juan Pérez
```

#### Paso 8: Ejecutar automáticamente al iniciar
```bash
# Crear servicio systemd
sudo tee /etc/systemd/system/gymaccess.service << 'EOF'
[Unit]
Description=GymAccess Control System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/gymaccess
Environment=PATH=/home/pi/gymaccess-env/bin
ExecStart=/home/pi/gymaccess-env/bin/python3 /home/pi/gymaccess/access_control.py
StandardInput=tty
TTYPath=/dev/tty1
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Habilitar servicio
sudo systemctl daemon-reload
sudo systemctl enable gymaccess
sudo systemctl start gymaccess

# Ver estado
sudo systemctl status gymaccess

# Ver logs
sudo journalctl -u gymaccess -f
```

#### Paso 9: Configurar lector QR USB
La mayoría de lectores QR USB funcionan como teclado. Solo conéctalos y funcionan.

**Lectores recomendados:**
- Tera 2D Barcode Scanner (~$25)
- Eyoyo EY-001 (~$20)
- NetumScan L8 (~$30)

**Configurar el lector:**
1. Conecta el lector USB
2. Escanea el código de configuración "USB HID" (viene en el manual)
3. Escanea "Add Enter Suffix" para que envíe Enter después de cada código

---

## CONFIGURACIÓN POST-INSTALACIÓN

### 1. Crear primer gimnasio
```bash
# Usando la API
curl -X POST "https://api.tudominio.com/api/gyms" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TU_TOKEN" \
  -d '{
    "name": "Mi Gimnasio",
    "address": "Calle Principal 123",
    "email": "info@migimnasio.com",
    "primary_color": "#E1FF01"
  }'
```

O simplemente:
1. Ve a `https://tudominio.com/admin`
2. Login con: `admin@gymaccess.com` / `admin123`
3. Ve a **Gimnasios** → **Nuevo Gimnasio**

### 2. Crear administrador del gimnasio
En **Personal** → **Agregar Usuario**:
- Rol: Administrador
- Esto les dará acceso completo a SU gimnasio

### 3. Crear planes de membresía
En **Planes** → **Nuevo Plan**:
- Plan Mensual: $30, 30 días
- Plan Trimestral: $80, 90 días
- Plan Anual: $300, 365 días

### 4. Registrar la Raspberry Pi
En **Dispositivos** → **Agregar Dispositivo**:
- Nombre: "Entrada Principal"
- Copia el token y ponlo en la Raspberry

### 5. Probar todo el flujo
1. Crear un socio de prueba
2. Asignarle membresía
3. Darle permiso de invitados
4. Probar login en la app
5. Probar el QR en la Raspberry

---

## SOLUCIÓN DE PROBLEMAS

### El QR no se valida
- Verifica que el token del gym sea correcto
- Verifica que la membresía esté activa
- Revisa los logs: `sudo journalctl -u gymaccess -f`

### La Raspberry no conecta
- Verifica conexión a internet: `ping google.com`
- Verifica la URL del servidor en `.env`
- Prueba la API manualmente: `curl https://api.tudominio.com/api/health`

### El relé no activa
- Verifica las conexiones GPIO
- Prueba manual: 
```python
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)
GPIO.output(17, GPIO.LOW)  # Activa
time.sleep(1)
GPIO.output(17, GPIO.HIGH) # Desactiva
```

### El torno no abre
- Verifica que uses terminales NO y COM del relé
- Verifica el voltaje del torno (algunos necesitan 12V o 24V)
- Puede necesitar un relé de mayor amperaje

---

## CONTACTO Y SOPORTE

¿Necesitas ayuda? 
- Documentación: Este archivo
- Código fuente: Descargado de Emergent
