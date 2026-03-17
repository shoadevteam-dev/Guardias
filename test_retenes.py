"""Script para debuggear el problema de los retenes"""

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
    
    # Simular la lógica de retenes
    reten_contador = {p.id: 0 for p in personas_activas}
    reten_fechas_dict = {}
    
    print('\n=== RETENES MARZO 2026 ===')
    print(f'{"Fecha":<12} {"Dia":<10} {"Guardia":<20} {"Retén":<20}')
    print('-' * 70)
    
    retenes_por_persona = {}
    
    for g in guardias:
        disponibles = obtener_personas_disponibles(g.fecha, exclude_id=g.persona_id)
        
        if disponibles:
            dia_anterior = g.fecha - timedelta(days=1)
            
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
            
            if persona_reten.id not in retenes_por_persona:
                retenes_por_persona[persona_reten.id] = []
            retenes_por_persona[persona_reten.id].append(g.fecha)
            
            persona = Persona.query.get(g.persona_id)
            print(f'{g.fecha.strftime("%d/%m/%Y"):<12} {g.fecha.strftime("%A"):<10} {persona.nombre:<20} {persona_reten.nombre:<20}')
        else:
            persona = Persona.query.get(g.persona_id)
            print(f'{g.fecha.strftime("%d/%m/%Y"):<12} {g.fecha.strftime("%A"):<10} {persona.nombre:<20} {"SIN RETÉN":<20}')
    
    # Verificar consecutivos
    print('\n\n=== VERIFICANDO DIAS CONSECUTIVOS ===')
    problema_encontrado = False
    
    for persona_id, fechas in retenes_por_persona.items():
        persona = Persona.query.get(persona_id)
        fechas_ordenadas = sorted(fechas)
        
        for i in range(len(fechas_ordenadas) - 1):
            diff = (fechas_ordenadas[i+1] - fechas_ordenadas[i]).days
            if diff == 1:
                print(f'PROBLEMA: {persona.nombre} tuvo retén consecutivo:')
                print(f'  - {fechas_ordenadas[i].strftime("%d/%m/%Y")} y {fechas_ordenadas[i+1].strftime("%d/%m/%Y")}')
                problema_encontrado = True
    
    if not problema_encontrado:
        print('No se encontraron retenes consecutivos.')
    
    # Mostrar resumen de retenes por persona
    print('\n\n=== RESUMEN DE RETENES POR PERSONA ===')
    for p in personas_activas:
        count = len(retenes_por_persona.get(p.id, []))
        if count > 0:
            print(f'{p.nombre}: {count} retenes')
