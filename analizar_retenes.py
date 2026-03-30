import urllib.request
import json
from datetime import timedelta
from collections import Counter

r = urllib.request.urlopen('http://127.0.0.1:5050/api/guardias/1/2026', timeout=30)
data = json.loads(r.read())

print('=== ANALIZANDO RETENES SIPAT ===')
sipat_nombres = {'A.FORTUNATO', 'E.CAMPILLAY', 'I.RIVAS'}
sipat_retenes = []
retenes_por_persona = Counter()
total_retenes = 0

for g in data:
    reten_nombre = g.get('reten_nombre', '').strip().upper()
    if reten_nombre and reten_nombre != 'SIN RETÉN':
        total_retenes += 1
        retenes_por_persona[reten_nombre] += 1

    if reten_nombre in sipat_nombres:
        sipat_retenes.append(g['fecha_display'])
        print(f"{g['fecha_display']} - {reten_nombre}")

print(f'\nTotal retenes: {total_retenes}')
print(f'Total retenes SIPAT: {len(sipat_retenes)}')
print('Reten por persona:')
for persona, count in retenes_por_persona.items():
    print(f'  {persona}: {count}')

# Verificar separación entre retenes
print('\n=== VERIFICANDO SEPARACIÓN ===')
from datetime import datetime
fechas = [datetime.strptime(f, '%d/%m/%Y').date() for f in sipat_retenes]
for i in range(len(fechas) - 1):
    diff = (fechas[i+1] - fechas[i]).days
    status = 'OK' if diff >= 3 else 'MAL'
    print(f'{fechas[i]} -> {fechas[i+1]}: {diff} días [{status}]')
