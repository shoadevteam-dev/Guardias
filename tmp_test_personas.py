from app import create_app

app = create_app()
with app.app_context():
    with app.test_client() as client:
        r = client.get('/api/personas?mes=1&anio=2026')
        print('status', r.status_code)
        data = r.get_json()
        for p in data:
            if 'PAC ' in p['nombre']:
                print(p['nombre'], 'guardias', p['guardias'], 'retenes', p['retenes'])
