#!/usr/bin/env python3
"""
Scrape expiration dates from IsMyGym cuotas (using regex for tbody)
"""
import requests
from bs4 import BeautifulSoup
import re
import json
import time
import urllib3
urllib3.disable_warnings()

BASE_URL = "https://lafabrika.ismygym.com"
session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'})

# Login
session.get(f"{BASE_URL}/admin/socio_listado.php?r=1", verify=False)
session.post(f"{BASE_URL}/usuarios/registro.php", data={
    'user': 'edu', 'pass': 'Edu@123456', 'recordar': 'recordar'
}, verify=False, allow_redirects=True)
print("Login OK")

# Get all member IDs
print("Recopilando IDs...")
all_ids = []
page = 0
while True:
    resp = session.get(f"{BASE_URL}/admin/socio_listado.php?invitado=false&pag={page}", verify=False)
    edit_links = re.findall(r'socio_formulario\.php\?id=(\d+)', resp.text)
    page_ids = list(set(edit_links))
    if not page_ids:
        break
    all_ids.extend(page_ids)
    page += 1
    time.sleep(0.3)

unique_ids = list(dict.fromkeys(all_ids))
print(f"Total IDs: {len(unique_ids)}")

results = {}
total = len(unique_ids)

for i, mid in enumerate(unique_ids):
    try:
        # Get member basic info
        resp = session.get(f"{BASE_URL}/admin/socio_formulario.php?id={mid}", verify=False)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        nombre_input = soup.find('input', {'name': 'Nombre'})
        apellidos_input = soup.find('input', {'name': 'Apellidos'})
        codigo_input = soup.find('input', {'name': 'CodigoReserva'})
        email_input = soup.find('input', {'name': 'Email'})
        
        nombre = ((nombre_input.get('value', '') if nombre_input else '') + ' ' + 
                  (apellidos_input.get('value', '') if apellidos_input else '')).strip()
        codigo = codigo_input.get('value', '') if codigo_input else ''
        email = email_input.get('value', '') if email_input else ''
        
        # Get cuotas tab
        resp2 = session.get(f"{BASE_URL}/admin/socio_formulario.php?id={mid}&pestana=cuotas", verify=False)
        
        # Parse tbody with regex
        fecha_hasta = ''
        tarifa_tipo = ''
        importe = ''
        
        tbody_match = re.search(r'<tbody>(.*?)</tbody>', resp2.text, re.DOTALL)
        if tbody_match:
            trs = re.findall(r'<tr[^>]*>(.*?)</tr>', tbody_match.group(1), re.DOTALL)
            if trs:
                # First row is the most recent cuota
                tds = re.findall(r'<td[^>]*>(.*?)</td>', trs[0], re.DOTALL)
                clean = [re.sub(r'<[^>]+>', '', td).strip() for td in tds]
                # Headers: Tipo, FechaAlta, FechaPago, Desde, Hasta, C.Prom, Importe, FormaPago, EstadoPago, CodigoPago
                if len(clean) >= 7:
                    tarifa_tipo = clean[0]  # Tipo
                    fecha_hasta = clean[4]  # Hasta
                    importe = clean[6]      # Importe
        
        results[mid] = {
            'nombre': nombre,
            'codigo': codigo,
            'email': email,
            'fecha_hasta': fecha_hasta,
            'tarifa_tipo': tarifa_tipo,
            'importe': importe,
        }
        
        if (i + 1) % 20 == 0 or i == 0:
            print(f"  Progreso: {i+1}/{total} ({((i+1)/total*100):.1f}%) - {nombre}: hasta {fecha_hasta}")
        
        time.sleep(0.3)
        
    except Exception as e:
        print(f"  ERROR {mid}: {e}")

# Save
with open('/app/vencimientos_lafabrika.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

con_fecha = sum(1 for r in results.values() if r['fecha_hasta'])
sin_fecha = sum(1 for r in results.values() if not r['fecha_hasta'])
print(f"\n{'='*50}")
print(f"TOTAL: {len(results)} socios")
print(f"Con fecha vencimiento: {con_fecha}")
print(f"Sin cuota activa: {sin_fecha}")
print(f"Guardado en: /app/vencimientos_lafabrika.json")
print(f"{'='*50}")
