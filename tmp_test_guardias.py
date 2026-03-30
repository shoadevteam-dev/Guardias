from app import create_app

app = create_app()
with app.app_context():
    with app.test_client() as client:
        res = client.get('/api/guardias/1/2026')
        print('status', res.status_code)
        if res.status_code == 200:
            data = res.get_json()
            print('rows', len(data))
            for row in data[:5]:
                print(row['fecha_display'], row['persona_nombre'], row['reten_nombre'])
