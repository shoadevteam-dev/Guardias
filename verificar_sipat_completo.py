import urllib.request
import json
from datetime import datetime

r = urllib.request.urlopen('http://127.0.0.1:5050/api/guardias/1/2026', timeout=30)
data = json.loads(r.read())

print('=== ENERO 2026 - GUARDIAS Y RETENES SIPAT ===')
sipat_nombres = ['A.Fortunato', 'E.Campillay', 'I.Rivas']

for g in data:
    es_guardia_sipat = g['persona_nombre'] in sipat_nombres
    es_reten_sipat = g['reten_nombre'] in sipat_nombres
    
    if es_guardia_sipat or es_reten_sipat:
        marca_g = ' [GUARDIA SIPAT]' if es_guardia_sipat else ''
        marca_r = ' [RETEN SIPAT]' if es_reten_sipat else ''
        print(f"{g['fecha_display']} {g['persona_nombre']:<20} {g['reten_nombre']:<20}{marca_g}{marca_r}")

print('\n=== RESUMEN ===')
guardias_sipat = [g for g in data if g['persona_nombre'] in sipat_nombres]
retenes_sipat = [g for g in data if g['reten_nombre'] in sipat_nombres]
print(f'Guardias SIPAT: {len(guardias_sipat)}')
print(f'Retenes SIPAT: {len(retenes_sipat)}')

# Verificar cercanía entre guardias y retenes de SIPAT
print('\n=== VERIFICANDO CERCANÍA GUARDIA-RETÉN ===')
fechas_guardias = [datetime.strptime(g['fecha_display'], '%d/%m/%Y').date() for g in guardias_sipat]
fechas_retenes = [datetime.strptime(g['fecha_display'], '%d/%m/%Y').date() for g in retenes_sipat]

violaciones = []
for fg in fechas_guardias:
    for fr in fechas_retenes:
        diff = abs((fg - fr).days)
        if diff == 1:  # Guardia y retén a 1 día de distancia
            violaciones.append((fg, fr, diff))

if violaciones:
    print(f'⚠ VIOLACIONES: {len(violaciones)} casos de guardia/retén a 1 día')
    for v in violaciones[:10]:
        print(f'  Guardia: {v[0]}, Retén: {v[1]} (diff={v[2]} días)')
else:
    print('✓ NO HAY guardia/retén de SIPAT a 1 día de distancia')
