from app import create_app

app = create_app()
with app.app_context():
    with app.test_client() as client:
        r = client.post('/api/guardias/generar', json={'mes': 1, 'anio': 2026})
        print('generar', r.status_code, r.get_json())
        r2 = client.get('/api/personas?mes=1&anio=2026')
        print('personas', r2.status_code)
        for p in r2.get_json():
            if 'PAC ' in p['nombre'] and ('FORTUNATO' in p['nombre'] or 'CAMPILLAY' in p['nombre'] or 'RIVAS' in p['nombre']):
                print(p)
        r3 = client.get('/api/guardias/1/2026')
        print('guardias', r3.status_code, 'count', len(r3.get_json()))
        for y in r3.get_json()[:10]:
            print(y)
