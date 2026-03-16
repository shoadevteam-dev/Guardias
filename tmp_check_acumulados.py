from app import create_app
from models import Persona
from services.consultas import contar_guardias_mes

app = create_app()

with app.app_context():
    mes = 1
    anio = 2026
    personas = Persona.query.filter_by(activo=True).all()
    total = sum(contar_guardias_mes(p.id, mes, anio) for p in personas)
    prom = total / len(personas)
    print('prom', prom)
    for p in personas:
        g = contar_guardias_mes(p.id, mes, anio)
        diff = round(prom - g)
        print(p.nombre, 'guardias', g, 'diff', diff, 'acum', p.acumulado)
