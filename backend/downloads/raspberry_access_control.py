#!/usr/bin/env python3
"""
GymAccess - Raspberry Pi Access Control Script
==============================================

Este script controla el acceso al gimnasio mediante:
- Lectura de códigos QR
- Validación contra el servidor
- Control de relés para abrir tornos

Requisitos de Hardware:
- Raspberry Pi 3B+ o superior
- Módulo de 2 relés (5V)
- Lector de códigos QR USB (o cámara con pyzbar)

Conexiones GPIO:
- GPIO 17 -> IN1 del relé (Entrada)
- GPIO 27 -> IN2 del relé (Salida)
- GND -> GND del relé
- 5V -> VCC del relé

Instalación:
1. sudo apt-get update
2. sudo apt-get install python3-pip python3-rpi.gpio
3. pip3 install requests python-dotenv
4. Si usas cámara: pip3 install opencv-python pyzbar

Uso:
1. Configura las variables de entorno o edita este archivo
2. Ejecuta: python3 raspberry_access_control.py
3. Para ejecutar al inicio: agregar a /etc/rc.local o crear servicio systemd
"""

import os
import sys
import time
import json
import logging
import threading
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

# Cargar archivo .env automáticamente
try:
    from dotenv import load_dotenv
    # Busca .env en la misma carpeta que este script
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"Archivo .env cargado desde: {env_path}")
    else:
        print(f"AVISO: No se encontró .env en {env_path}")
except ImportError:
    print("python-dotenv no instalado. Ejecuta: pip3 install python-dotenv")

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

# Intentar importar GPIO (solo funciona en Raspberry Pi)
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    logger.warning("RPi.GPIO no disponible - modo simulación activado")
    GPIO_AVAILABLE = False

try:
    import requests
except ImportError:
    logger.error("requests no instalado. Ejecuta: pip3 install requests")
    sys.exit(1)

# ============================================================
# CONFIGURACIÓN - EDITA ESTOS VALORES
# ============================================================

# URL del servidor GymAccess (cambiar por tu URL real)
SERVER_URL = os.environ.get('GYMACCESS_SERVER_URL', 'https://tu-servidor.com')

# Token de API del gimnasio (obtener del panel de admin)
GYM_TOKEN = os.environ.get('GYMACCESS_GYM_TOKEN', 'TU_TOKEN_AQUI')

# ID del dispositivo (obtener del panel de admin)
DEVICE_ID = os.environ.get('GYMACCESS_DEVICE_ID', 'TU_DEVICE_ID')

# Configuración de GPIO
RELAY_ENTRADA = 17  # GPIO para relé de entrada
RELAY_SALIDA = 27   # GPIO para relé de salida

# Tiempo que el torno permanece abierto (segundos)
TIEMPO_APERTURA = 3

# Intervalo de ping al servidor (segundos)
PING_INTERVAL = 60

# Modo de lectura QR: 'usb' o 'camera'
QR_MODE = os.environ.get('GYMACCESS_QR_MODE', 'usb')

# ============================================================
# CLASES Y FUNCIONES
# ============================================================

class GPIOController:
    """Controla los pines GPIO para los relés"""
    
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
        else:
            logger.info("Modo simulación - GPIO no disponible")
    
    def abrir_torno(self, direccion: str):
        """Abre el torno de entrada o salida"""
        pin = RELAY_ENTRADA if direccion == 'entrada' else RELAY_SALIDA
        nombre = "ENTRADA" if direccion == 'entrada' else "SALIDA"
        
        logger.info(f"Abriendo torno {nombre}...")
        
        if self.initialized:
            GPIO.output(pin, GPIO.LOW)  # Activa relé (normalmente activo en bajo)
            time.sleep(TIEMPO_APERTURA)
            GPIO.output(pin, GPIO.HIGH)  # Desactiva relé
        else:
            logger.info(f"[SIMULACIÓN] Torno {nombre} abierto por {TIEMPO_APERTURA}s")
            time.sleep(TIEMPO_APERTURA)
        
        logger.info(f"Torno {nombre} cerrado")
    
    def cleanup(self):
        """Limpia los pines GPIO"""
        if self.initialized:
            GPIO.cleanup()
            logger.info("GPIO limpiado")


class QRReader:
    """Lee códigos QR desde escáner USB o cámara"""
    
    def __init__(self, mode: str = 'usb'):
        self.mode = mode
        self.camera = None
        
        if mode == 'camera':
            try:
                import cv2
                from pyzbar import pyzbar
                self.cv2 = cv2
                self.pyzbar = pyzbar
                self.camera = cv2.VideoCapture(0)
                logger.info("Cámara inicializada para lectura QR")
            except ImportError:
                logger.warning("opencv/pyzbar no disponible, usando modo USB")
                self.mode = 'usb'
    
    def leer_qr_usb(self) -> Optional[str]:
        """Lee QR desde escáner USB (actúa como teclado)"""
        try:
            # El escáner USB envía el código como entrada de teclado
            codigo = input()
            return codigo.strip() if codigo else None
        except EOFError:
            return None
        except KeyboardInterrupt:
            raise
    
    def leer_qr_camera(self) -> Optional[str]:
        """Lee QR desde cámara"""
        if not self.camera or not self.camera.isOpened():
            return None
        
        ret, frame = self.camera.read()
        if not ret:
            return None
        
        # Decodificar QR
        decoded = self.pyzbar.decode(frame)
        for obj in decoded:
            return obj.data.decode('utf-8')
        
        return None
    
    def leer(self) -> Optional[str]:
        """Lee un código QR"""
        if self.mode == 'camera':
            return self.leer_qr_camera()
        return self.leer_qr_usb()
    
    def cleanup(self):
        """Libera recursos"""
        if self.camera:
            self.camera.release()


class GymAccessClient:
    """Cliente para comunicarse con el servidor GymAccess"""
    
    def __init__(self, server_url: str, gym_token: str, device_id: str):
        self.server_url = server_url.rstrip('/')
        self.gym_token = gym_token
        self.device_id = device_id
        self.api_url = f"{self.server_url}/api"
    
    def validar_qr(self, qr_code: str, direccion: str) -> Dict[str, Any]:
        """Valida un código QR con el servidor"""
        try:
            # Limpiar datos del escáner (quitar whitespace, newlines, etc.)
            qr_code_clean = qr_code.strip().replace('\n', '').replace('\r', '').replace('\x00', '')
            if qr_code_clean != qr_code:
                logger.info(f"QR limpiado: {len(qr_code)} -> {len(qr_code_clean)} chars")
            
            response = requests.post(
                f"{self.api_url}/access/validate",
                json={
                    "qr_code": qr_code_clean,
                    "gym_token": self.gym_token,
                    "direction": direccion
                },
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error del servidor: {response.status_code}")
                return {"valid": False, "reason": "Error de servidor"}
                
        except requests.exceptions.Timeout:
            logger.error("Timeout conectando al servidor")
            return {"valid": False, "reason": "Timeout"}
        except requests.exceptions.ConnectionError:
            logger.error("No se puede conectar al servidor")
            return {"valid": False, "reason": "Sin conexión"}
        except Exception as e:
            logger.error(f"Error validando QR: {e}")
            return {"valid": False, "reason": str(e)}
    
    def ping(self) -> bool:
        """Envía ping al servidor para indicar que el dispositivo está online"""
        try:
            response = requests.post(
                f"{self.api_url}/devices/{self.device_id}/ping",
                params={"gym_token": self.gym_token},
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Error en ping: {e}")
            return False


class AccessController:
    """Controlador principal del sistema de acceso"""
    
    def __init__(self):
        self.gpio = GPIOController()
        self.qr_reader = QRReader(QR_MODE)
        self.client = GymAccessClient(SERVER_URL, GYM_TOKEN, DEVICE_ID)
        self.running = True
        self.direccion_actual = 'entrada'  # Alternar entre entrada/salida si es necesario
        
        # Iniciar thread de ping
        self.ping_thread = threading.Thread(target=self._ping_loop, daemon=True)
        self.ping_thread.start()
    
    def _ping_loop(self):
        """Loop que envía pings periódicos al servidor"""
        while self.running:
            if self.client.ping():
                logger.debug("Ping exitoso")
            else:
                logger.warning("Ping fallido")
            time.sleep(PING_INTERVAL)
    
    def procesar_qr(self, qr_code: str) -> bool:
        """Procesa un código QR escaneado"""
        if not qr_code:
            return False
        
        logger.info(f"QR escaneado: {qr_code[:20]}...")
        
        # Validar con el servidor
        resultado = self.client.validar_qr(qr_code, self.direccion_actual)
        
        if resultado.get('valid'):
            nombre = resultado.get('member_name', 'Socio')
            direccion = resultado.get('direction', self.direccion_actual)
            
            logger.info(f"✅ ACCESO PERMITIDO: {nombre} ({direccion})")
            print(f"\n✅ Bienvenido, {nombre}!\n")
            
            # Abrir torno
            self.gpio.abrir_torno(direccion)
            return True
        else:
            razon = resultado.get('reason', 'Desconocido')
            logger.warning(f"❌ ACCESO DENEGADO: {razon}")
            print(f"\n❌ Acceso denegado: {razon}\n")
            return False
    
    def run(self):
        """Loop principal"""
        logger.info("="*50)
        logger.info("GymAccess - Sistema de Control de Acceso")
        logger.info("="*50)
        logger.info(f"Servidor: {SERVER_URL}")
        logger.info(f"Modo QR: {QR_MODE}")
        logger.info(f"GPIO Entrada: {RELAY_ENTRADA}")
        logger.info(f"GPIO Salida: {RELAY_SALIDA}")
        logger.info("="*50)
        logger.info("Esperando códigos QR...")
        print("\n" + "="*40)
        print("   SISTEMA DE ACCESO ACTIVO")
        print("   Escanea tu código QR")
        print("="*40 + "\n")
        
        try:
            while self.running:
                if QR_MODE == 'camera':
                    # Modo cámara: lectura continua
                    qr_code = self.qr_reader.leer()
                    if qr_code:
                        self.procesar_qr(qr_code)
                        time.sleep(2)  # Evitar lecturas múltiples del mismo QR
                    time.sleep(0.1)
                else:
                    # Modo USB: esperar input
                    qr_code = self.qr_reader.leer()
                    if qr_code:
                        self.procesar_qr(qr_code)
        
        except KeyboardInterrupt:
            logger.info("Interrupción de teclado - cerrando...")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Limpia recursos"""
        self.running = False
        self.gpio.cleanup()
        self.qr_reader.cleanup()
        logger.info("Sistema cerrado correctamente")


# ============================================================
# PUNTO DE ENTRADA
# ============================================================

def main():
    # Verificar configuración
    if GYM_TOKEN == 'TU_TOKEN_AQUI':
        logger.error("⚠️  Configura GYM_TOKEN antes de ejecutar")
        logger.error("   Obtén el token en: Panel Admin -> Dispositivos")
        sys.exit(1)
    
    if DEVICE_ID == 'TU_DEVICE_ID':
        logger.error("⚠️  Configura DEVICE_ID antes de ejecutar")
        logger.error("   Registra el dispositivo en: Panel Admin -> Dispositivos")
        sys.exit(1)
    
    # Iniciar controlador
    controller = AccessController()
    controller.run()


if __name__ == '__main__':
    main()


# ============================================================
# INSTRUCCIONES DE INSTALACIÓN COMO SERVICIO
# ============================================================
"""
Para ejecutar automáticamente al iniciar la Raspberry Pi:

1. Crear archivo de servicio:
   sudo nano /etc/systemd/system/gymaccess.service

2. Contenido del archivo:
   
   [Unit]
   Description=GymAccess Control System
   After=network.target

   [Service]
   ExecStart=/usr/bin/python3 /home/pi/raspberry_access_control.py
   WorkingDirectory=/home/pi
   StandardInput=tty
   TTYPath=/dev/tty1
   TTYReset=yes
   TTYVHangup=yes
   User=root
   Restart=always
   RestartSec=10
   Environment=GYMACCESS_SERVER_URL=https://tu-servidor.com
   Environment=GYMACCESS_GYM_TOKEN=tu_token_aqui
   Environment=GYMACCESS_DEVICE_ID=tu_device_id

   [Install]
   WantedBy=multi-user.target

3. Habilitar e iniciar servicio:
   sudo systemctl daemon-reload
   sudo systemctl enable gymaccess
   sudo systemctl start gymaccess

4. Ver logs:
   sudo journalctl -u gymaccess -f
"""
