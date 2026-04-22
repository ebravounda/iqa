#!/usr/bin/env python3
import os
import sys
import time
import json
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

SERVER_URL = os.environ.get('GYMACCESS_SERVER_URL', 'https://c.ingresoqr.com')
GYM_TOKEN = os.environ.get('GYMACCESS_GYM_TOKEN', 'TU_TOKEN_AQUI')
DEVICE_ID = os.environ.get('GYMACCESS_DEVICE_ID', 'TU_DEVICE_ID')
RELAY_ENTRADA = int(os.environ.get('GYMACCESS_RELAY_ENTRADA', '12'))
RELAY_SALIDA = int(os.environ.get('GYMACCESS_RELAY_SALIDA', '16'))
TIEMPO_APERTURA = 3
PING_INTERVAL = 60
SCANNER_MAP_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scanner_map.json')

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
                logger.info(f"GPIO inicializado - ENTRADA: pin {RELAY_ENTRADA}, SALIDA: pin {RELAY_SALIDA}")
            except Exception as e:
                logger.error(f"Error inicializando GPIO: {e}")

    def abrir_torno(self, direccion):
        pin = RELAY_ENTRADA if direccion == 'entrada' else RELAY_SALIDA
        nombre = direccion.upper()
        logger.info(f"Abriendo torno {nombre} - GPIO pin {pin}")
        if self.initialized:
            GPIO.output(pin, GPIO.LOW)
            time.sleep(TIEMPO_APERTURA)
            GPIO.output(pin, GPIO.HIGH)
            logger.info(f"Torno {nombre} cerrado")
        else:
            logger.info(f"[SIMULACION] Torno {nombre} pin {pin} abierto por {TIEMPO_APERTURA}s")
            time.sleep(TIEMPO_APERTURA)

    def cleanup(self):
        if self.initialized:
            GPIO.cleanup()


class GymAccessClient:
    def __init__(self):
        self.api_url = f"{SERVER_URL.rstrip('/')}/api"

    def validar_qr(self, qr_code, direccion):
        try:
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
                logger.info(f"Lector encontrado: {dev.path} - {dev.name} (phys: {dev.phys})")
    return scanners


def load_scanner_map():
    """Load saved scanner-to-direction mapping"""
    if os.path.exists(SCANNER_MAP_FILE):
        try:
            with open(SCANNER_MAP_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return None


def save_scanner_map(mapping):
    """Save scanner-to-direction mapping"""
    with open(SCANNER_MAP_FILE, 'w') as f:
        json.dump(mapping, f, indent=2)
    logger.info(f"Mapa de lectores guardado en {SCANNER_MAP_FILE}")


def assign_scanners(scanners):
    """Assign scanners to directions using saved physical USB mapping"""
    scanner_map = load_scanner_map()
    
    if scanner_map:
        # Try to match by physical USB path
        entrada_dev = None
        salida_dev = None
        
        for scanner in scanners:
            phys = scanner.phys
            if phys == scanner_map.get("entrada_phys"):
                entrada_dev = scanner
                logger.info(f"ENTRADA asignado por USB: {scanner.path} (phys: {phys})")
            elif phys == scanner_map.get("salida_phys"):
                salida_dev = scanner
                logger.info(f"SALIDA asignado por USB: {scanner.path} (phys: {phys})")
        
        if entrada_dev and salida_dev:
            return entrada_dev, salida_dev
        else:
            logger.warning("No se encontro mapeo USB guardado, usando calibracion...")
    
    # No saved mapping - use default order and save
    if len(scanners) >= 2:
        mapping = {
            "entrada_phys": scanners[0].phys,
            "entrada_path": scanners[0].path,
            "salida_phys": scanners[1].phys,
            "salida_path": scanners[1].path,
        }
        save_scanner_map(mapping)
        logger.info(f"Mapa inicial creado: ENTRADA={scanners[0].path}, SALIDA={scanners[1].path}")
        return scanners[0], scanners[1]
    elif len(scanners) == 1:
        return scanners[0], None
    return None, None


def calibrate(scanners):
    """Interactive calibration - assigns scanners to directions"""
    print("\n" + "=" * 50)
    print("   CALIBRACION DE LECTORES")
    print("=" * 50)
    print(f"\nSe encontraron {len(scanners)} lectores:")
    for i, s in enumerate(scanners):
        print(f"  {i+1}. {s.path} - {s.name} (phys: {s.phys})")
    
    print("\nEscanea un QR en el lector de ENTRADA...")
    
    # Wait for a scan on any reader
    import select
    devices = {s.fd: s for s in scanners}
    
    while True:
        r, w, x = select.select(devices.keys(), [], [], 10)
        if not r:
            print("Timeout. Intentando de nuevo...")
            continue
        for fd in r:
            dev = devices[fd]
            for event in dev.read():
                if event.type == ecodes.EV_KEY:
                    key_event = evdev.categorize(event)
                    if key_event.keystate == 1 and key_event.scancode == ecodes.KEY_ENTER:
                        entrada_dev = dev
                        salida_dev = [s for s in scanners if s != dev][0] if len(scanners) > 1 else None
                        
                        mapping = {
                            "entrada_phys": entrada_dev.phys,
                            "entrada_path": entrada_dev.path,
                        }
                        if salida_dev:
                            mapping["salida_phys"] = salida_dev.phys
                            mapping["salida_path"] = salida_dev.path
                        
                        save_scanner_map(mapping)
                        print(f"\n ENTRADA = {entrada_dev.path} (phys: {entrada_dev.phys})")
                        if salida_dev:
                            print(f" SALIDA  = {salida_dev.path} (phys: {salida_dev.phys})")
                        print("\nCalibracion completada! Reinicia el servicio:")
                        print("  sudo systemctl restart gymaccess")
                        return


def read_scanner(device, direccion, gpio, client):
    logger.info(f"Escuchando {direccion}: {device.path} (phys: {device.phys})")
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
                    real_dir = resultado.get('direction', direccion)
                    logger.info(f"ACCESO PERMITIDO: {nombre} ({real_dir})")
                    print(f"\nBienvenido, {nombre}! [{real_dir.upper()}]\n")
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

    # Calibration mode
    if '--calibrar' in sys.argv or '--calibrate' in sys.argv:
        calibrate(scanners)
        return

    # Assign scanners using saved mapping
    entrada_dev, salida_dev = assign_scanners(scanners)

    print("\n" + "=" * 40)
    print("   SISTEMA DE ACCESO ACTIVO")
    print(f"   {len(scanners)} lector(es) detectados")
    if entrada_dev:
        print(f"   ENTRADA: {entrada_dev.path}")
    if salida_dev:
        print(f"   SALIDA:  {salida_dev.path}")
    print("   Escanea tu codigo QR")
    print("=" * 40 + "\n")

    threading.Thread(target=ping_loop, args=(client,), daemon=True).start()

    threads = []
    if entrada_dev:
        t1 = threading.Thread(target=read_scanner, args=(entrada_dev, 'entrada', gpio, client), daemon=True)
        t1.start()
        threads.append(t1)
    if salida_dev:
        t2 = threading.Thread(target=read_scanner, args=(salida_dev, 'salida', gpio, client), daemon=True)
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
