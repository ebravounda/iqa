#!/usr/bin/env python3
import os
import sys
import time
import logging
import threading
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

SERVER_URL = os.environ.get('GYMACCESS_SERVER_URL', 'https://gymapi.ticketpro.es')
GYM_TOKEN = os.environ.get('GYMACCESS_GYM_TOKEN', 'TU_TOKEN_AQUI')
DEVICE_ID = os.environ.get('GYMACCESS_DEVICE_ID', 'TU_DEVICE_ID')
SWAP_SCANNERS = os.environ.get('GYMACCESS_SWAP_SCANNERS', 'false').lower() == 'true'
RELAY_ENTRADA = 11
RELAY_SALIDA = 16
TIEMPO_APERTURA = 3
PING_INTERVAL = 60

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
            # Limpiar datos del escaner
            qr_code_clean = qr_code.strip().replace('\n', '').replace('\r', '').replace('\x00', '')
            if qr_code_clean != qr_code:
                logger.info(f"QR limpiado: {len(qr_code)} -> {len(qr_code_clean)} chars")

            response = requests.post(
                f"{self.api_url}/access/validate",
                json={
                    "qr_code": qr_code_clean,
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


def find_scanners():
    scanners = []
    for path in evdev.list_devices():
        dev = evdev.InputDevice(path)
        if 'MEGAHUNT' in dev.name.upper() or 'HID' in dev.name.upper():
            if 'Keyboard' in dev.name:
                scanners.append(dev)
                logger.info(f"Lector encontrado: {dev.path} - {dev.name}")
    return scanners


def read_scanner(device, direccion, gpio, client):
    logger.info(f"Escuchando {direccion}: {device.path}")
    buffer = ""
    shift_pressed = False

    try:
        device.grab()
    except:
        logger.warning(f"No se pudo tomar control exclusivo de {device.path}")

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
                logger.info(f"[{direccion.upper()}] QR: {code[:20]}...")

                resultado = client.validar_qr(code, direccion)
                if resultado.get('valid'):
                    nombre = resultado.get('member_name', 'Socio')
                    logger.info(f"ACCESO PERMITIDO: {nombre} ({direccion})")
                    print(f"\nBienvenido, {nombre}! [{direccion.upper()}]\n")
                    threading.Thread(target=gpio.abrir_torno, args=(direccion,)).start()
                else:
                    razon = resultado.get('reason', 'Desconocido')
                    logger.warning(f"ACCESO DENEGADO: {razon} ({direccion})")
                    print(f"\nAcceso denegado: {razon} [{direccion.upper()}]\n")
        else:
            if shift_pressed and key_event.scancode in SHIFT_KEYS:
                buffer += SHIFT_KEYS[key_event.scancode]
            elif key_event.scancode in KEYS:
                char = KEYS[key_event.scancode]
                if shift_pressed and char.isalpha():
                    char = char.upper()
                buffer += char


def ping_loop(client):
    while True:
        client.ping()
        time.sleep(PING_INTERVAL)


def main():
    if GYM_TOKEN == 'TU_TOKEN_AQUI':
        logger.error("Configura GYM_TOKEN en .env")
        sys.exit(1)
    if DEVICE_ID == 'TU_DEVICE_ID':
        logger.error("Configura DEVICE_ID en .env")
        sys.exit(1)

    gpio = GPIOController()
    client = GymAccessClient()
    scanners = find_scanners()

    if len(scanners) == 0:
        logger.error("No se encontraron lectores QR USB")
        sys.exit(1)

    print("\n" + "=" * 40)
    print("   SISTEMA DE ACCESO ACTIVO")
    print(f"   {len(scanners)} lector(es) detectados")
    print("   Escanea tu codigo QR")
    print("=" * 40 + "\n")

    threading.Thread(target=ping_loop, args=(client,), daemon=True).start()

    threads = []
    if SWAP_SCANNERS:
        dir_first = 'salida'
        dir_second = 'entrada'
        logger.info("Lectores INTERCAMBIADOS por config SWAP_SCANNERS=true")
    else:
        dir_first = 'entrada'
        dir_second = 'salida'
    
    if len(scanners) >= 1:
        t1 = threading.Thread(target=read_scanner, args=(scanners[0], dir_first, gpio, client), daemon=True)
        t1.start()
        threads.append(t1)
    if len(scanners) >= 2:
        t2 = threading.Thread(target=read_scanner, args=(scanners[1], dir_second, gpio, client), daemon=True)
        t2.start()
        threads.append(t2)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Cerrando sistema...")
        gpio.cleanup()

if __name__ == '__main__':
    main()
