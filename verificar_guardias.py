"""Script para verificar guardias en la DB"""

from app import create_app
from models import Guardia, Persona
from datetime import datetime, timedelta

app = create_app()

with app.app_context():
    # Verificar mes actual
    mes = 3  # Marzo
    anio = 2026
    
    inicio_mes = datetime(anio, mes, 1)
    if mes == 12:
        fin_mes = datetime(anio + 1, 1, 1) - timedelta(days=1)
    else:
        fin_mes = datetime(anio, mes + 1, 1) - timedelta(days=1)
    
    print(f"Buscando guardias desde {inicio_mes.date()} hasta {fin_mes.date()}")
    
    guardias = Guardia.query.filter(
        Guardia.fecha >= inicio_mes.date(),
        Guardia.fecha <= fin_mes.date()
    ).all()
    
    print(f"Guardias encontradas: {len(guardias)}")
    
    for g in guardias[:5]:  # Mostrar primeras 5
        persona = Persona.query.get(g.persona_id)
        print(f"  {g.fecha} - {persona.nombre if persona else 'N/A'}")
    
    # Total de guardias en DB
    total = Guardia.query.count()
    print(f"\nTotal guardias en DB: {total}")
    
    # Personas
    personas = Persona.query.count()
    print(f"Personas en DB: {personas}")
