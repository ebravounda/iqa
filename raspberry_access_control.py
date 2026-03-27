#!/usr/bin/env python3
import os
import sys
import time
import logging
import threading
import subprocess
from dotenv import load_dotenv
load_dotenv()

import evdev
from evdev import ecodes

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/gymaccess.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    logger.warning("RPi.GPIO no disponible - modo simulacion")
    GPIO_AVAILABLE = False

import requests

SERVER_URL = os.environ.get('GYMACCESS_SERVER_URL', 'https://c.ingresoqr.com')
GYM_TOKEN = os.environ.get('GYMACCESS_GYM_TOKEN', 'TU_TOKEN_AQUI')
DEVICE_ID = os.environ.get('GYMACCESS_DEVICE_ID', 'TU_DEVICE_ID')
RELAY_ENTRADA = 12
RELAY_SALIDA = 16
TIEMPO_APERTURA = 3
PING_INTERVAL = 60
HEARTBEAT_INTERVAL = 60

KEYS = {
    ecodes.KEY_0: '0', ecodes.KEY_1: '1', ecodes.KEY_2: '2',
    ecodes.KEY_3: '3', ecodes.KEY_4: '4', ecodes.KEY_5: '5',
    ecodes.KEY_6: '6', ecodes.KEY_7: '7', ecodes.KEY_8: '8',
    ecodes.KEY_9: '9', ecodes.KEY_A: 'a', ecodes.KEY_B: 'b',
    ecodes.KEY_C: 'c', ecodes.KEY_D: 'd', ecodes.KEY_E: 'e',
    ecodes.KEY_F: 'f', ecodes.KEY_G: 'g', ecodes.KEY_H: 'h',
    ecodes.KEY_I: 'i', ecodes.KEY_J: 'j', ecodes.KEY_K: 'k',
    ecodes.KEY_L: 'l', ecodes.KEY_M: 'm', ecodes.KEY_N: 'n',
    ecodes.KEY_O: 'o', ecodes.KEY_P: 'p', ecodes.KEY_Q: 'q',
    ecodes.KEY_R: 'r', ecodes.KEY_S: 's', ecodes.KEY_T: 't',
    ecodes.KEY_U: 'u', ecodes.KEY_V: 'v', ecodes.KEY_W: 'w',
    ecodes.KEY_X: 'x', ecodes.KEY_Y: 'y', ecodes.KEY_Z: 'z',
    ecodes.KEY_MINUS: '-', ecodes.KEY_EQUAL: '=',
    ecodes.KEY_SEMICOLON: ';', ecodes.KEY_APOSTROPHE: "'",
    ecodes.KEY_COMMA: ',', ecodes.KEY_DOT: '.', ecodes.KEY_SLASH: '/',
    ecodes.KEY_BACKSLASH: '\\', ecodes.KEY_SPACE: ' ',
    ecodes.KEY_LEFTBRACE: '[', ecodes.KEY_RIGHTBRACE: ']',
}

SHIFT_KEYS = {
    ecodes.KEY_MINUS: '_', ecodes.KEY_EQUAL: '+',
    ecodes.KEY_1: '!', ecodes.KEY_2: '@', ecodes.KEY_3: '#',
    ecodes.KEY_4: '$', ecodes.KEY_5: '%', ecodes.KEY_6: '^',
    ecodes.KEY_7: '&', ecodes.KEY_8: '*', ecodes.KEY_9: '(',
    ecodes.KEY_0: ')',
}


def get_system_info():
    info = {}
    try:
        temp = subprocess.check_output(["vcgencmd", "measure_temp"]).decode()
        info["cpu_temp"] = float(temp.replace("temp=", "").replace("'C\n", ""))
    except:
        info["cpu_temp"] = None
    try:
        load = os.getloadavg()
        info["cpu_usage"] = round(load[0] * 100 / os.cpu_count(), 1)
    except:
        info["cpu_usage"] = None
    try:
        mem = subprocess.check_output(["free", "-m"]).decode().split("\n")[1].split()
        info["memory_usage"] = round(int(mem[2]) / int(mem[1]) * 100, 1)
    except:
        info["memory_usage"] = None
    try:
        uptime_sec = float(open("/proc/uptime").read().split()[0])
        info["uptime"] = int(uptime_sec)
    except:
        info["uptime"] = None
    try:
        ip = subprocess.check_output(["hostname", "-I"]).decode().strip().split()[0]
        info["local_ip"] = ip
    except:
        info["local_ip"] = None
    try:
        ext_ip = subprocess.check_output(
            ["curl", "-s", "--max-time", "5", "https://api.ipify.org"]
        ).decode().strip()
        info["ip_address"] = ext_ip
    except:
        info["ip_address"] = None
    return info


class GPIOController:
    def __init__(self):
        self.initialized = False
        if GPIO_AVAILABLE:
            try:
                GPIO.setmode(GPIO.BCM)
                GPIO.setwarnings(False)
                GPIO.setup(RELAY_ENTRADA, GPIO.OUT, initial=GPIO.HIGH)
                GPIO.setup(RELAY_SALIDA, GPIO.OUT, initial=GPIO.HIGH)
                self.initialized = True
                logger.info("GPIO inicializado correctamente")
            except Exception as e:
                logger.error(f"Error inicializando GPIO: {e}")

    def abrir_torno(self, direccion):
        pin = RELAY_ENTRADA if direccion == 'entrada' else RELAY_SALIDA
        nombre = "ENTRADA" if direccion == 'entrada' else "SALIDA"
        logger.info(f"Abriendo torno {nombre}...")
        if self.initialized:
            GPIO.output(pin, GPIO.LOW)
            time.sleep(TIEMPO_APERTURA)
            GPIO.output(pin, GPIO.HIGH)
        else:
            logger.info(f"[SIMULACION] Torno {nombre} abierto por {TIEMPO_APERTURA}s")
            time.sleep(TIEMPO_APERTURA)
        logger.info(f"Torno {nombre} cerrado")

    def cleanup(self):
        if self.initialized:
            GPIO.cleanup()


class GymAccessClient:
    def __init__(self):
        self.api_url = f"{SERVER_URL.rstrip('/')}/api"

    def validar_qr(self, qr_code, direccion):
        try:
            response = requests.post(
                f"{self.api_url}/access/validate",
                json={
                    "qr_code": qr_code,
                    "gym_token": GYM_TOKEN,
                    "direction": direccion
                },
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            else:
                return {"valid": False, "reason": f"Error {response.status_code}"}
        except requests.exceptions.Timeout:
            return {"valid": False, "reason": "Timeout"}
        except requests.exceptions.ConnectionError:
            return {"valid": False, "reason": "Sin conexion"}
        except Exception as e:
            return {"valid": False, "reason": str(e)}

    def ping(self):
        try:
            response = requests.post(
                f"{self.api_url}/devices/{DEVICE_ID}/ping",
                params={"gym_token": GYM_TOKEN},
                timeout=5
            )
            return response.status_code == 200
        except:
            return False

    def heartbeat(self):
        try:
            info = get_system_info()
            info["gym_token"] = GYM_TOKEN
            info["software_version"] = "2.0"
            response = requests.post(
                f"{self.api_url}/devices/{DEVICE_ID}/heartbeat",
                json=info,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                cmd = data.get("command")
                if cmd:
                    logger.info(f"[HEARTBEAT] Comando recibido: {cmd}")
                    self.execute_command(cmd)
                return True
            else:
                logger.warning(f"[HEARTBEAT] Error: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"[HEARTBEAT] Error: {e}")
            return False

    def execute_command(self, command):
        try:
            if command == "reboot":
                logger.info("[CMD] Reiniciando dispositivo...")
                os.system("sudo reboot")
            elif command == "restart_service":
                logger.info("[CMD] Reiniciando servicio gymaccess...")
                os.system("sudo systemctl restart gymaccess.service")
            elif command == "update":
                logger.info("[CMD] Actualizando software...")
                os.system("cd /home/pi/gymaccess && git pull")
                os.system("sudo systemctl restart gymaccess.service")
            else:
                logger.warning(f"[CMD] Comando desconocido: {command}")
        except Exception as e:
            logger.error(f"[CMD] Error ejecutando comando: {e}")


def find_scanners():
    scanners = []
    for path in sorted(evdev.list_devices()):
        dev = evdev.InputDevice(path)
        name_upper = dev.name.upper()
        if 'MEGAHUNT' in name_upper or ('HID' in name_upper and 'Keyboard' in dev.name):
            scanners.append(dev)
            logger.info(f"Lector encontrado: {dev.path} - {dev.name}")
    if len(scanners) < 2:
        # Segundo intento: buscar cualquier dispositivo HID que no sea HDMI
        for path in sorted(evdev.list_devices()):
            dev = evdev.InputDevice(path)
            if dev not in scanners and 'hdmi' not in dev.name.lower() and hasattr(dev, 'capabilities'):
                caps = dev.capabilities(verbose=True)
                has_keys = any('EV_KEY' in str(k) for k in caps.keys())
                if has_keys and 'Keyboard' in dev.name:
                    scanners.append(dev)
                    logger.info(f"Lector adicional encontrado: {dev.path} - {dev.name}")
    return scanners


def read_scanner(device, direccion, gpio, client):
    logger.info(f"[{direccion.upper()}] Escuchando en: {device.path} ({device.name})")
    buffer = ""
    shift_pressed = False

    try:
        device.grab()
        logger.info(f"[{direccion.upper()}] Control exclusivo OK: {device.path}")
    except Exception as e:
        logger.warning(f"[{direccion.upper()}] No se pudo tomar control exclusivo de {device.path}: {e}")

    try:
        for event in device.read_loop():
            if event.type != ecodes.EV_KEY:
                continue

            key_event = evdev.categorize(event)

            if key_event.keycode in ('KEY_LEFTSHIFT', 'KEY_RIGHTSHIFT'):
                shift_pressed = (key_event.keystate == 1)
                continue

            if key_event.keystate != 1:
                continue

            if key_event.scancode == ecodes.KEY_ENTER:
                if buffer:
                    code = buffer.strip()
                    buffer = ""
                    logger.info(f"[{direccion.upper()}] QR leido: {code[:20]}...")

                    resultado = client.validar_qr(code, direccion)
                    if resultado.get('valid'):
                        nombre = resultado.get('member_name', 'Socio')
                        logger.info(f"[{direccion.upper()}] ACCESO PERMITIDO: {nombre}")
                        print(f"\nBienvenido, {nombre}! [{direccion.upper()}]\n")
                        threading.Thread(target=gpio.abrir_torno, args=(direccion,)).start()
                    else:
                        razon = resultado.get('reason', 'Desconocido')
                        logger.warning(f"[{direccion.upper()}] ACCESO DENEGADO: {razon}")
                        print(f"\nAcceso denegado: {razon} [{direccion.upper()}]\n")
            else:
                if shift_pressed and key_event.scancode in SHIFT_KEYS:
                    buffer += SHIFT_KEYS[key_event.scancode]
                elif key_event.scancode in KEYS:
                    char = KEYS[key_event.scancode]
                    if shift_pressed and char.isalpha():
                        char = char.upper()
                    buffer += char
    except OSError as e:
        logger.error(f"[{direccion.upper()}] Lector desconectado o error: {e}")
        logger.error(f"[{direccion.upper()}] Hilo terminado para {device.path}")
    except Exception as e:
        logger.error(f"[{direccion.upper()}] Error inesperado: {e}")
        logger.error(f"[{direccion.upper()}] Hilo terminado para {device.path}")


def heartbeat_loop(client):
    while True:
        ok = client.heartbeat()
        if ok:
            logger.info("[HEARTBEAT] OK - estado enviado al servidor")
        time.sleep(HEARTBEAT_INTERVAL)


def main():
    if GYM_TOKEN == 'TU_TOKEN_AQUI':
        logger.error("Configura GYMACCESS_GYM_TOKEN en .env")
        sys.exit(1)
    if DEVICE_ID == 'TU_DEVICE_ID':
        logger.error("Configura GYMACCESS_DEVICE_ID en .env")
        sys.exit(1)

    gpio = GPIOController()
    client = GymAccessClient()
    scanners = find_scanners()

    if len(scanners) == 0:
        logger.error("No se encontraron lectores QR USB")
        sys.exit(1)

    print("\n" + "=" * 50)
    print("   INGRESOQR - SISTEMA DE ACCESO v2.1")
    print(f"   {len(scanners)} lector(es) detectados")
    print(f"   Servidor: {SERVER_URL}")
    print(f"   Device ID: {DEVICE_ID}")
    print("-" * 50)
    for i, s in enumerate(scanners):
        rol = "ENTRADA" if i == 0 else "SALIDA"
        print(f"   {rol}: {s.path} ({s.name})")
    print("-" * 50)
    print("   Escanea tu codigo QR para entrar o salir")
    print("=" * 50 + "\n")

    # Heartbeat: reporta estado cada 60 segundos
    threading.Thread(target=heartbeat_loop, args=(client,), daemon=True).start()
    logger.info("Heartbeat iniciado - reportando cada 60 segundos")

    threads = []
    if len(scanners) >= 1:
        t1 = threading.Thread(target=read_scanner, args=(scanners[0], 'entrada', gpio, client))
        t1.daemon = True
        t1.start()
        threads.append(t1)
        logger.info(f"Hilo ENTRADA iniciado: {scanners[0].path}")
    if len(scanners) >= 2:
        t2 = threading.Thread(target=read_scanner, args=(scanners[1], 'salida', gpio, client))
        t2.daemon = True
        t2.start()
        threads.append(t2)
        logger.info(f"Hilo SALIDA iniciado: {scanners[1].path}")

    try:
        while True:
            # Verificar que los hilos sigan vivos
            for i, t in enumerate(threads):
                if not t.is_alive():
                    rol = "ENTRADA" if i == 0 else "SALIDA"
                    logger.error(f"ALERTA: Hilo {rol} se detuvo! Revisa el lector USB.")
            time.sleep(5)
    except KeyboardInterrupt:
        logger.info("Cerrando sistema...")
        gpio.cleanup()

if __name__ == '__main__':
    main()
