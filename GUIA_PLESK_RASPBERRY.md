# GUÍA: Montar GymAccess desde el Panel de Plesk (sin SSH)

## REQUISITOS PREVIOS
- Docker instalado en Plesk (ya lo tienes)
- Dominios creados: `app.ingresoqr.com` y `c.ingresoqr.com`
- Código descargado de Emergent (botón "Download Code")

---

## PASO 1: MONGODB EN DOCKER

1. En Plesk → **Docker**
2. Busca imagen: `mongo`
3. Selecciona versión: **`7`**
4. Click **Run**
5. En configuración:
   - Puerto: `27017` → `27017`
   - Reinicio automático: **Always**
6. Click **OK**
7. Espera que el estado sea **Running** (verde)

---

## PASO 2: FRONTEND → app.ingresoqr.com

### 2.1 Crear dominio (si no existe)
1. Plesk → **Websites & Domains** → **Add Domain/Subdomain**
2. Nombre: `app.ingresoqr.com`

### 2.2 Subir archivos
1. Click en **app.ingresoqr.com** → **File Manager**
2. Entra a la carpeta **`httpdocs`**
3. **BORRA** todo lo que haya dentro (index.html por defecto, etc.)
4. Del ZIP descargado de Emergent, abre la carpeta: `frontend/build/`
5. Sube **TODO** lo que hay dentro de `build/`:
   - `index.html` ← archivo principal
   - `manifest.json`
   - `asset-manifest.json`
   - Carpeta `static/` (con todo su contenido: css/, js/, media/)

Resultado final en Plesk File Manager:
```
httpdocs/
  ├── index.html
  ├── manifest.json
  ├── asset-manifest.json
  └── static/
      ├── css/
      │   └── main.417966fc.css
      ├── js/
      │   └── main.4cbde5c9.js
      └── media/
          └── (archivos de fuentes .woff)
```

### 2.3 Configurar Apache para React Router
1. Click en **app.ingresoqr.com** → **Apache & nginx Settings**
2. En el campo **"Additional directives for HTTP"** Y **"Additional directives for HTTPS"**, pega:
```
<IfModule mod_rewrite.c>
    RewriteEngine On
    RewriteBase /
    RewriteRule ^index\.html$ - [L]
    RewriteCond %{REQUEST_FILENAME} !-f
    RewriteCond %{REQUEST_FILENAME} !-d
    RewriteRule . /index.html [L]
</IfModule>
```
3. Click **OK** o **Apply**

### 2.4 SSL (HTTPS)
1. Click en **app.ingresoqr.com** → **SSL/TLS Certificates**
2. Click **Let's Encrypt**
3. Genera certificado gratuito
4. Activa **"Redirect HTTP to HTTPS"**

---

## PASO 3: BACKEND → c.ingresoqr.com

Como no usaremos SSH, montaremos el backend con Docker en Plesk.

### Opción A: Usar Docker para el Backend (Recomendado)

**Necesitas acceder al Terminal de Plesk** (NO es SSH externo, es desde el propio panel):

1. Plesk → **Tools & Settings** → **SSH Terminal** (viene integrado en Plesk)
   - O alternativamente: **Extensions** → busca **"Terminal"** → instálalo si no lo tienes

2. En el Terminal de Plesk, ejecuta estos comandos uno por uno:

```bash
# Crear directorio
mkdir -p /opt/gymaccess/backend
```

3. Ahora ve a **File Manager** de Plesk (la raíz del servidor, no la de un dominio):
   - Navega a `/opt/gymaccess/backend/`
   - Sube estos 3 archivos del ZIP descargado:
     - `backend/server.py`
     - `backend/requirements-prod.txt` (renómbralo a `requirements.txt` después de subirlo)
     - `backend/Dockerfile`

4. Vuelve al **Terminal de Plesk** y ejecuta:

```bash
# Crear archivo de configuración
cat > /opt/gymaccess/backend/.env << 'ENDOFFILE'
MONGO_URL=mongodb://172.17.0.1:27017
DB_NAME=gymaccess
JWT_SECRET=CambiaEstoPorUnaClaveMuyLargaYSegura2024XYZ
QR_SECRET=OtraClaveDiferenteParaElQR2024ABC
CORS_ORIGINS=https://app.ingresoqr.com
ENDOFFILE
```

**IMPORTANTE**: Cambia `JWT_SECRET` y `QR_SECRET` por claves propias largas y aleatorias.

5. Construir y ejecutar el contenedor Docker:

```bash
cd /opt/gymaccess/backend
docker build -t gymaccess-api .
docker run -d \
  --name gymaccess-api \
  --restart always \
  -p 8001:8001 \
  --env-file .env \
  -e MONGO_URL=mongodb://172.17.0.1:27017 \
  gymaccess-api
```

6. Verificar que funciona:
```bash
curl http://localhost:8001/api/health
```
Debe responder: `{"status":"healthy"}`

### 3.2 Configurar dominio c.ingresoqr.com

1. Plesk → **Websites & Domains** → Crea subdominio **`c.ingresoqr.com`**
2. Click en **c.ingresoqr.com** → **Apache & nginx Settings**
3. Busca la sección **nginx**
4. En **"Additional nginx directives"**, pega:

```nginx
location / {
    proxy_pass http://127.0.0.1:8001;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_cache_bypass $http_upgrade;
    proxy_read_timeout 90;
}
```

5. Click **OK**

### 3.3 SSL para la API
1. Click en **c.ingresoqr.com** → **SSL/TLS Certificates**
2. Click **Let's Encrypt**
3. Genera certificado
4. Activa **"Redirect HTTP to HTTPS"**

### 3.4 Verificar
Abre en el navegador: `https://c.ingresoqr.com/api/health`
Debe mostrar: `{"status":"healthy"}`

---

## PASO 4: CREAR TU CUENTA SUPER ADMIN

Desde el Terminal de Plesk (o desde tu navegador):

```bash
curl -X POST "https://c.ingresoqr.com/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"TU_EMAIL","password":"TU_PASSWORD","name":"Tu Nombre","role":"super_admin"}'
```

O simplemente abre: `https://app.ingresoqr.com`
Ve a Panel de Administración y la primera vez puedes registrarte.

---

## PASO 5: PROBAR TODO

1. Abre `https://app.ingresoqr.com` → debe verse la página principal
2. Click "Panel de Administración" → login
3. Crea un gimnasio
4. Crea planes de membresía
5. Crea socios
6. Un socio entra en `https://app.ingresoqr.com/app/login` con su código

---

## PASO 6: RASPBERRY PI 3B+ (Ya tienes los relés instalados)

### 6.1 Materiales que necesitas además de los relés:
- **Lector QR USB** (~20€ en Amazon, busca "lector código barras 2D USB")
  - Recomendados: Tera 2D, Eyoyo EY-001, NetumScan L8
- **Cable Ethernet** (para conectar la Raspberry a internet por cable)
- **Tarjeta MicroSD 16GB+** con Raspberry Pi OS instalado

### 6.2 Instalar Raspberry Pi OS
1. En tu PC, descarga **Raspberry Pi Imager**: https://www.raspberrypi.com/software/
2. Inserta la MicroSD en tu PC
3. Abre Imager:
   - Dispositivo: Raspberry Pi 3
   - Sistema: **Raspberry Pi OS Lite (64-bit)** (sin escritorio, solo terminal)
   - Almacenamiento: tu MicroSD
4. Click en el **engranaje** (⚙) para configurar:
   - Hostname: `gymaccess`
   - **Activar SSH**: ✅
   - Usuario: `pi`
   - Contraseña: `la_que_quieras`
   - WiFi: (opcional, mejor cable ethernet)
5. Click **Write** y espera

### 6.3 Primer arranque
1. Saca la MicroSD del PC
2. Insértala en la Raspberry Pi
3. Conecta cable ethernet al router
4. Conecta la alimentación (5V)
5. Espera 2 minutos

### 6.4 Conectar a la Raspberry
Desde tu PC, abre **CMD** (Windows) o **Terminal** (Mac):
```bash
ssh pi@gymaccess.local
```
Si no funciona con el nombre, busca la IP de la Raspberry en tu router y usa:
```bash
ssh pi@192.168.1.XXX
```
Escribe la contraseña que pusiste.

### 6.5 Instalar software en la Raspberry
Copia y pega estos comandos UNO A UNO:

```bash
sudo apt update && sudo apt upgrade -y
```

```bash
sudo apt install -y python3-pip python3-venv python3-rpi.gpio
```

```bash
python3 -m venv ~/gymaccess-env
```

```bash
source ~/gymaccess-env/bin/activate
```

```bash
pip install requests python-dotenv
```

### 6.6 Crear los archivos del script
```bash
mkdir -p ~/gymaccess && cd ~/gymaccess
```

Crear el archivo de configuración:
```bash
nano .env
```
Pega esto (cambia los valores):
```
GYMACCESS_SERVER_URL=https://c.ingresoqr.com
GYMACCESS_GYM_TOKEN=PEGA_AQUI_EL_TOKEN
GYMACCESS_DEVICE_ID=PEGA_AQUI_EL_DEVICE_ID
GYMACCESS_QR_MODE=usb
```
Guarda: Ctrl+X → Y → Enter

Ahora crea el script principal:
```bash
nano access_control.py
```
Pega todo el contenido del archivo `raspberry_access_control.py` que descargaste de Emergent.
Guarda: Ctrl+X → Y → Enter

### 6.7 Obtener Token y Device ID
1. Abre `https://app.ingresoqr.com/admin`
2. Login como admin
3. Ve a **Dispositivos** → **Agregar Dispositivo**
4. Nombre: "Entrada Principal"
5. Copia el **Token del Gym** y el **ID del dispositivo**
6. Edita el `.env` de la Raspberry:
```bash
cd ~/gymaccess && nano .env
```
Pega los valores copiados y guarda.

### 6.8 Verificar conexiones de los relés
```
RASPBERRY PI 3B+          MÓDULO 2 RELÉS
═══════════════════        ═══════════════
Pin 2  (5V)         ─────→ VCC
Pin 6  (GND)        ─────→ GND
Pin 11 (GPIO17)     ─────→ IN1 (Torno ENTRADA)
Pin 13 (GPIO27)     ─────→ IN2 (Torno SALIDA)

RELÉ 1 (Entrada) → Terminales NO y COM → Botón apertura Torno Entrada
RELÉ 2 (Salida)  → Terminales NO y COM → Botón apertura Torno Salida
```

### 6.9 Probar el sistema
```bash
cd ~/gymaccess
source ~/gymaccess-env/bin/activate
python3 access_control.py
```

Debe mostrar:
```
==================================================
   GYMACCESS - SISTEMA DE CONTROL DE ACCESO
==================================================
   Servidor: https://c.ingresoqr.com
   Modo: usb
==================================================
   Esperando códigos QR...
==================================================
```

Conecta el lector QR USB a la Raspberry. Escanea el QR de un socio desde su móvil.
Debe mostrar: `✅ Bienvenido, [Nombre del socio]!` y el relé debe activarse 3 segundos.

### 6.10 Hacer que arranque solo al encender
```bash
sudo tee /etc/systemd/system/gymaccess.service << 'EOF'
[Unit]
Description=GymAccess Control
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/gymaccess
Environment=PATH=/home/pi/gymaccess-env/bin
ExecStart=/home/pi/gymaccess-env/bin/python3 /home/pi/gymaccess/access_control.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable gymaccess
sudo systemctl start gymaccess
```

Para ver si está funcionando:
```bash
sudo systemctl status gymaccess
```

Para ver los logs en tiempo real:
```bash
sudo journalctl -u gymaccess -f
```

### 6.11 Configurar el Lector QR USB
- Solo conéctalo al USB de la Raspberry
- La mayoría funcionan automáticamente como teclado
- Si el lector trae manual, escanea el código de configuración "USB HID Mode"
- Escanea también "Add Enter/CR Suffix" (para que envíe Enter después de cada lectura)

---

## SOLUCIÓN DE PROBLEMAS

### El frontend muestra página en blanco
→ Verifica que `index.html` está directamente en `httpdocs/` (no en `httpdocs/build/`)
→ Verifica las reglas de reescritura Apache

### La API no responde
→ En Terminal de Plesk: `docker ps` para ver si el contenedor está corriendo
→ `docker logs gymaccess-api` para ver errores

### El QR no valida en la Raspberry
→ Verifica el token del gym en `.env`
→ Verifica que la API es accesible: `curl https://c.ingresoqr.com/api/health`
→ Ver logs: `sudo journalctl -u gymaccess -f`

### El relé no activa
→ Prueba manual en Python:
```python
import RPi.GPIO as GPIO
import time
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)
GPIO.output(17, GPIO.LOW)   # Activa relé
time.sleep(2)
GPIO.output(17, GPIO.HIGH)  # Desactiva relé
GPIO.cleanup()
```
