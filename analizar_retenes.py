import urllib.request
import json
from datetime import timedelta

r = urllib.request.urlopen('http://127.0.0.1:5050/api/guardias/1/2026', timeout=30)
data = json.loads(r.read())

print('=== ANALIZANDO RETENES SIPAT ===')
sipat_nombres = ['A.Fortunato', 'E.Campillay', 'I.Rivas']
sipat_retenes = []

for g in data:
    if g['reten_nombre'] in sipat_nombres:
        sipat_retenes.append(g['fecha_display'])
        print(f"{g['fecha_display']} - {g['reten_nombre']}")

print(f'\nTotal retenes SIPAT: {len(sipat_retenes)}')

# Verificar separación entre retenes
print('\n=== VERIFICANDO SEPARACIÓN ===')
from datetime import datetime
fechas = [datetime.strptime(f, '%d/%m/%Y').date() for f in sipat_retenes]
for i in range(len(fechas) - 1):
    diff = (fechas[i+1] - fechas[i]).days
    status = 'OK' if diff >= 3 else 'MAL'
    print(f'{fechas[i]} -> {fechas[i+1]}: {diff} días [{status}]')
