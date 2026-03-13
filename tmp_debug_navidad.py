from app import create_app
from services.consultas import obtener_personas_disponibles, contar_guardias_mes
from models import Persona
from datetime import date

app = create_app()

with app.app_context():
    personas = Persona.query.filter_by(activo=True).all()
    anio = 2026

    def es_candidato(p):
        fechas = [date(anio, 12, 24), date(anio, 12, 25), date(anio, 12, 31)]
        for f in fechas:
            if p not in obtener_personas_disponibles(f):
                return False
        return True

    candidatos = [p for p in personas if es_candidato(p)]
    print('Candidatos navidad:', [p.nombre for p in candidatos])
    if candidatos:
        best = min(candidatos, key=lambda p: sum(contar_guardias_mes(p.id, m, anio) for m in range(1, 12)))
        print('Best candidate:', best.nombre)
