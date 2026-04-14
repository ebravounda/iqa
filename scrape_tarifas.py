#!/usr/bin/env python3
"""
Scrape tarifas from IsMyGym and output JSON for import
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

# Get tarifa list
resp = session.get(f"{BASE_URL}/admin/tarifa_listado.php?r=1", verify=False)
tarifa_ids = re.findall(r'tarifa_formulario\.php\?id=(\d+)', resp.text)
tarifa_ids = list(set(tarifa_ids))
print(f"Found {len(tarifa_ids)} tarifas")

plans = []
for tid in tarifa_ids:
    resp = session.get(f"{BASE_URL}/admin/tarifa_formulario.php?id={tid}", verify=False)
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    def get_field(name):
        inp = soup.find('input', {'name': name})
        if inp: return inp.get('value', '').strip()
        return ''
    
    def get_select(name):
        sel = soup.find('select', {'name': name})
        if sel:
            opt = sel.find('option', selected=True)
            if opt: return opt.text.strip()
        return ''
    
    name = get_field('Categoria')
    description = get_field('FranjaHoraria') or ''
    inscripcion = get_field('Inscripcion')
    cuota = get_field('Cuota') or get_field('ImporteCuota')
    tipo_cuota = get_select('TipoCuota')
    forma_pago = get_select('FormaPago')
    
    # Clean price
    price_str = cuota.replace('€', '').replace(',', '.').strip()
    try:
        price = float(price_str)
    except:
        price = 0.0
    
    plan = {
        "ismygym_id": tid,
        "name": name,
        "description": description,
        "price": price,
        "inscripcion": inscripcion,
        "tipo_cuota": tipo_cuota,
        "forma_pago": forma_pago,
    }
    plans.append(plan)
    print(f"  {name} | {cuota} | {tipo_cuota}")
    time.sleep(0.3)

# Save JSON
output = {"plans": plans}
with open('/app/tarifas_lafabrika.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\n{'='*50}")
print(f"TOTAL: {len(plans)} tarifas extraidas")
print(f"Guardado en: /app/tarifas_lafabrika.json")
print(f"{'='*50}")
