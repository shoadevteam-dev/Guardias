import urllib.request
import json

try:
    r = urllib.request.urlopen('http://127.0.0.1:5050/', timeout=10)
    print(f'Root: {r.status}')
except Exception as e:
    print(f'Root Error: {e}')

try:
    r = urllib.request.urlopen('http://127.0.0.1:5050/api/guardias/1/2026', timeout=30)
    data = json.loads(r.read())
    print(f'API OK: {len(data)} guardias')
    print('\n=== PRIMEROS 5 ===')
    for g in data[:5]:
        print(f"{g['fecha_display']} {g['persona_nombre']:<20} {g['reten_nombre']:<20}")
    
    print('\n=== RETENES SIPAT ===')
    for g in data:
        if g['reten_nombre'] in ['A.Fortunato', 'E.Campillay', 'I.Rivas']:
            print(f"{g['fecha_display']} {g['reten_nombre']}")
except Exception as e:
    print(f'API Error: {e}')
