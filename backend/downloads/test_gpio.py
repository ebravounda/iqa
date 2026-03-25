#!/usr/bin/env python3
"""Script para probar cada GPIO pin individualmente y encontrar los reles"""
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Pines a probar
pines = [11, 16, 17, 27, 5, 6, 13, 19, 26]

for pin in pines:
    GPIO.setup(pin, GPIO.OUT, initial=GPIO.HIGH)

print("=" * 40)
print("  PRUEBA DE RELES GPIO")
print("=" * 40)
print()

for pin in pines:
    input(f"Presiona ENTER para activar PIN {pin}...")
    print(f"  -> Activando pin {pin} (LOW)...")
    GPIO.output(pin, GPIO.LOW)
    time.sleep(2)
    GPIO.output(pin, GPIO.HIGH)
    print(f"  -> Pin {pin} desactivado")
    rele = input(f"  Se abrio algun rele? (entrada/salida/ninguno/ambos): ").strip().lower()
    if rele in ('entrada', 'salida', 'ambos'):
        print(f"  *** PIN {pin} = {rele.upper()} ***")
    print()

GPIO.cleanup()
print("Prueba completada!")
