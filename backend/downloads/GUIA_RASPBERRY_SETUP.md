# GUIA COMPLETA: Configurar Raspberry Pi para Control de Acceso GymAccess

## Requisitos de Hardware

- Raspberry Pi 3B+ o superior
- Fuente de alimentación 5V/3A
- MicroSD 16GB+ con Raspberry Pi OS
- 2 lectores QR USB (MEGAHUNT o similar HID)
- Modulo de 2 reles (5V)
- Cables dupont hembra-hembra
- Conexion a internet (WiFi o Ethernet)

## Conexion de Hardware

### Reles GPIO (BCM):
```
Rele ENTRADA -> GPIO 12 (pin fisico 32)
Rele SALIDA  -> GPIO 16 (pin fisico 36)
GND          -> GND (pin fisico 6, 9, 14, 20, 25, 30, 34 o 39)
VCC          -> 5V (pin fisico 2 o 4)
```

### Lectores QR USB:
- Conectar cada lector a un puerto USB diferente del Pi
- No importa cual puerto, la calibracion los asigna

---

## Paso 1: Preparar el Raspberry Pi

### 1.1 Instalar Raspberry Pi OS
1. Descarga Raspberry Pi Imager: https://www.raspberrypi.com/software/
2. Graba "Raspberry Pi OS Lite (64-bit)" en la MicroSD
3. En la configuracion del Imager:
   - Activa SSH
   - Configura WiFi (SSID y contraseña)
   - Usuario: `pi`, contraseña: la que elijas
4. Inserta la MicroSD en el Pi y enciendelo

### 1.2 Conectar por SSH
```bash
ssh pi@<IP_DEL_PI>
```
(Busca la IP en tu router o usa `ping raspberrypi.local`)

### 1.3 Actualizar el sistema
```bash
sudo apt update && sudo apt upgrade -y
```

---

## Paso 2: Instalar dependencias

```bash
sudo pip3 install --break-system-packages evdev python-dotenv requests RPi.GPIO
```

---

## Paso 3: Crear la carpeta del proyecto

```bash
mkdir -p /home/pi/gymaccess
cd /home/pi/gymaccess
```

---

## Paso 4: Descargar el script de control de acceso

```bash
wget -O access_control.py "https://stripe-gym-payments.preview.emergentagent.com/api/download/raspberry-py"
```

**NOTA**: Si este link ya no esta disponible, copia el archivo `raspberry_access_control.py` del repositorio de GitHub.

---

## Paso 5: Obtener credenciales del gym

### 5.1 Registrar el gym (si no existe)
1. Entra como **Super Admin** en `app.ingresoqr.com/admin`
2. Ve a **Gimnasios** > **Nuevo Gimnasio**
3. Crea el gym con nombre, email y contraseña del admin

### 5.2 Registrar un dispositivo
1. Como **Super Admin**, ve a **Dispositivos**
2. Clic en **Nuevo Dispositivo**
3. Selecciona el gym, ponle un nombre (ej: "Raspberry Pi Gym 2")
4. Copia el **Device ID** (algo como `71ee011c-a2ee-49d6-b0f4-1942846a81f8`)

### 5.3 Obtener el token del gym
1. Ve a **Gimnasios** y selecciona el gym
2. Copia el **API Token** (algo como `9dTgxGwJIGvHNEJxzb0sCGMHlfGIsQ3Fk_oakaUYLo8`)

---

## Paso 6: Crear archivo de configuracion

```bash
nano /home/pi/gymaccess/.env
```

Contenido:
```
GYMACCESS_SERVER_URL=https://c.ingresoqr.com
GYMACCESS_GYM_TOKEN=PEGA_EL_API_TOKEN_DEL_GYM_AQUI
GYMACCESS_DEVICE_ID=PEGA_EL_DEVICE_ID_AQUI
GYMACCESS_QR_MODE=usb
```

Guarda con `Ctrl+O`, sal con `Ctrl+X`.

---

## Paso 7: Crear el servicio systemd

```bash
sudo nano /etc/systemd/system/gymaccess.service
```

Contenido:
```ini
[Unit]
Description=GymAccess Control
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/pi/gymaccess
ExecStart=/usr/bin/python3 /home/pi/gymaccess/access_control.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Guarda y activa:
```bash
sudo systemctl daemon-reload
sudo systemctl enable gymaccess
```

---

## Paso 8: Crear archivo de log

```bash
sudo touch /var/log/gymaccess.log
sudo chmod 666 /var/log/gymaccess.log
```

---

## Paso 9: Calibrar los lectores QR

Conecta ambos lectores USB al Pi, luego:

```bash
cd /home/pi/gymaccess
sudo systemctl stop gymaccess
sudo python3 access_control.py --calibrar
```

1. El script detectara los 2 lectores
2. Te pedira: **"Escanea un QR en el lector de ENTRADA"**
3. Escanea cualquier QR en el lector que esta en la puerta de ENTRADA
4. El script asigna automaticamente el otro como SALIDA
5. La configuracion se guarda en `scanner_map.json`

---

## Paso 10: Iniciar el servicio

```bash
sudo systemctl start gymaccess
```

### Verificar que funciona:
```bash
sudo systemctl status gymaccess
```

Debe mostrar `active (running)`.

### Ver logs en tiempo real:
```bash
sudo journalctl -u gymaccess -f
```

---

## Paso 11: Probar el acceso

1. Registra un **socio** en el gym desde el panel admin
2. Crea un **plan** y asignale una **membresia activa** al socio
3. El socio abre `app.ingresoqr.com/app` en su celular
4. Ingresa su **codigo de socio** para ver el QR
5. Escanea el QR en el lector de **ENTRADA** -> el torno debe abrir
6. Escanea el QR en el lector de **SALIDA** -> el torno debe abrir

---

## Solucion de problemas

### El servicio no arranca
```bash
sudo journalctl -u gymaccess -n 30 --no-pager
```

### No detecta lectores QR
```bash
sudo python3 -c "import evdev; [print(f'{d.path}: {d.name}') for d in [evdev.InputDevice(p) for p in evdev.list_devices()]]"
```

### Error "Invalid gym token"
- Verifica que el `GYMACCESS_GYM_TOKEN` en `.env` sea el correcto
- El token se obtiene desde el panel de Super Admin > Gimnasios

### Error "QR expired"
- El socio debe abrir la app y generar un QR nuevo
- El QR es valido por 5 minutos

### Error "Invalid signature"
- Asegurate que el frontend del gym apunte a `c.ingresoqr.com`

### Los reles no abren
1. Ejecuta el test de GPIO:
```bash
sudo python3 -c "
import RPi.GPIO as GPIO; import time
GPIO.setmode(GPIO.BCM)
GPIO.setup(12, GPIO.OUT, initial=GPIO.HIGH)
GPIO.setup(16, GPIO.OUT, initial=GPIO.HIGH)
print('Activando pin 12 (entrada)...')
GPIO.output(12, GPIO.LOW); time.sleep(2); GPIO.output(12, GPIO.HIGH)
print('Activando pin 16 (salida)...')
GPIO.output(16, GPIO.LOW); time.sleep(2); GPIO.output(16, GPIO.HIGH)
GPIO.cleanup()
print('Listo!')
"
```
2. Si un pin no activa el rele, verifica el cableado

### Recalibrar lectores
```bash
sudo systemctl stop gymaccess
sudo python3 /home/pi/gymaccess/access_control.py --calibrar
sudo systemctl start gymaccess
```

---

## Resumen de archivos en el Pi

```
/home/pi/gymaccess/
├── access_control.py     # Script principal
├── .env                  # Configuracion (token, device ID)
├── scanner_map.json      # Mapeo de lectores (creado por calibracion)

/etc/systemd/system/
├── gymaccess.service     # Servicio systemd

/var/log/
├── gymaccess.log         # Logs de acceso
```

## Pines GPIO utilizados

| Pin BCM | Pin Fisico | Funcion        |
|---------|------------|----------------|
| 12      | 32         | Rele ENTRADA   |
| 16      | 36         | Rele SALIDA    |
| GND     | 6          | Tierra comun   |
| 5V      | 2          | Alimentacion   |
