"""Script para verificar el problema de las fechas"""

from app import create_app
from models import Persona, Guardia, db
from services import generar_guardias_mes
from services.consultas import obtener_guardias_mes, obtener_personas_disponibles
from datetime import timedelta

app = create_app()

with app.app_context():
    # Generar marzo 2026
    print("Generando guardias para marzo 2026...")
    generar_guardias_mes(3, 2026)
    
    guardias = obtener_guardias_mes(3, 2026)
    personas_activas = Persona.query.filter_by(activo=True).all()
    
    # Simular la lógica de retenes EXACTAMENTE como en la API
    reten_contador = {p.id: 0 for p in personas_activas}
    reten_fechas_dict = {}
    
    print('\n=== VERIFICACION DE FECHAS ===')
    print(f'{"Fecha":<12} {"weekday()":<10} {"strftime":<15} {"Guardia":<20} {"Retén":<20}')
    print('-' * 80)
    
    for g in guardias:
        disponibles = obtener_personas_disponibles(g.fecha, exclude_id=g.persona_id)
        
        dia_anterior = g.fecha - timedelta(days=1)
        
        if disponibles:
            candidatos = []
            for p in disponibles:
                fue_reten_anterior = reten_fechas_dict.get((p.id, dia_anterior), False)
                if not fue_reten_anterior:
                    candidatos.append(p)
            
            if not candidatos:
                candidatos = disponibles
            
            candidatos.sort(key=lambda p: reten_contador.get(p.id, 0))
            persona_reten = candidatos[0]
            
            reten_fechas_dict[(persona_reten.id, g.fecha)] = True
            reten_contador[persona_reten.id] = reten_contador.get(persona_reten.id, 0) + 1
            
            persona = Persona.query.get(g.persona_id)
            
            # Mostrar información de fecha
            print(f'{str(g.fecha):<12} {g.fecha.weekday():<10} {g.fecha.strftime("%A"):<15} {persona.nombre:<20} {persona_reten.nombre:<20}')
        else:
            persona = Persona.query.get(g.persona_id)
            print(f'{str(g.fecha):<12} {g.fecha.weekday():<10} {g.fecha.strftime("%A"):<15} {persona.nombre:<20} SIN RETÉN')
    
    # Ahora verificar qué pasa con la API
    print('\n\n=== SIMULANDO API RESPONSE ===')
    print(f'{"fecha (API)":<15} {"weekday()":<10} {"strftime":<15} {"dia_semana (calc)":<15}')
    print('-' * 60)
    
    for g in guardias[:5]:  # Solo primeros 5 días
        # Esto es lo que hace la API
        nombres_dias = {
            0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves',
            4: 'Viernes', 5: 'Sábado', 6: 'Domingo'
        }
        dia_semana = nombres_dias[g.fecha.weekday()]
        
        # Esto es lo que hace JS
        js_weekday = g.fecha.weekday()  # Python: 0=Lunes
        # Pero en JS: new Date().getDay() devuelve 0=Domingo
        
        print(f'{str(g.fecha):<15} {g.fecha.weekday():<10} {g.fecha.strftime("%A"):<15} {dia_semana:<15}')
