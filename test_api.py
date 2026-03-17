import urllib.request
import json

print("Conectando a http://127.0.0.1:5050/api/guardias/1/2026...")
try:
    r = urllib.request.urlopen('http://127.0.0.1:5050/api/guardias/1/2026', timeout=30)
    print(f"Status: {r.status}")
    data = json.loads(r.read())
    print(f"Guardias encontradas: {len(data)}")
    print('\n=== ENERO 2026 - PRIMEROS 10 ===')
    for g in data[:10]:
        print(f"{g['fecha_display']} {g['persona_nombre']:<20} {g['reten_nombre']:<20}")
    
    print('\n=== VERIFICANDO SIPAT RETENES ===')
    sipat_retenes = []
    for g in data:
        reten = g['reten_nombre']
        if reten in ['A.Fortunato', 'E.Campillay', 'I.Rivas']:
            sipat_retenes.append((g['fecha_display'], reten))
            print(f"{g['fecha_display']} - {reten} [SIPAT]")
    
    print(f'\nTotal retenes SIPAT: {len(sipat_retenes)}')
except Exception as e:
    print(f'Error: {type(e).__name__}: {e}')
