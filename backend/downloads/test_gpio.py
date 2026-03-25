#!/usr/bin/env python3
"""Script para probar pines GPIO"""
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

pines = [11, 12, 16]

for pin in pines:
    GPIO.setup(pin, GPIO.OUT, initial=GPIO.HIGH)

print("PRUEBA DE RELES GPIO")
print()

for pin in pines:
    input(f"Presiona ENTER para activar PIN {pin}...")
    print(f"  Activando pin {pin}...")
    GPIO.output(pin, GPIO.LOW)
    time.sleep(2)
    GPIO.output(pin, GPIO.HIGH)
    print(f"  Pin {pin} desactivado")
    rele = input(f"  Se abrio algun rele? (entrada/salida/ninguno/ambos): ").strip()
    print()

GPIO.cleanup()
print("Listo!")
