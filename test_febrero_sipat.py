"""Script para debuggear retenes SIPAT en febrero 2026"""
from app import create_app
from models import Guardia, Persona
from services.consultas import obtener_rango_mes, obtener_personas_disponibles
from services.guardias_service import generar_guardias_mes
from datetime import timedelta

app = create_app()
with app.app_context():
    # Generar febrero 2026
    print('Generando febrero 2026...')
    generar_guardias_mes(2, 2026)
    
    mes, anio = 2, 2026
    inicio_mes, fin_mes = obtener_rango_mes(mes, anio)
    guardias = Guardia.query.filter(
        Guardia.fecha >= inicio_mes.date(), 
        Guardia.fecha <= fin_mes.date()
    ).order_by(Guardia.fecha).all()
    
    personas_activas = Persona.query.filter_by(activo=True).all()
    reten_contador = {p.id: 0 for p in personas_activas}
    reten_fechas_dict = {}
    sipat_reten_fechas = set()
    
    # Obtener lista de SIPAT
    sipats = Persona.query.filter(Persona.grado.like('%SIPAT%')).all()
    sipat_ids = [p.id for p in sipats]
    print(f'SIPAT IDs: {sipat_ids}')
    print(f'SIPAT nombres: {[p.nombre for p in sipats]}\n')
    
    # Tracking de fechas donde los SIPAT tienen guardia
    sipat_guardia_fechas = {}
    for g in guardias:
        if g.persona_id in sipat_ids:
            if g.persona_id not in sipat_guardia_fechas:
                sipat_guardia_fechas[g.persona_id] = set()
            sipat_guardia_fechas[g.persona_id].add(g.fecha)
    
    print('=== FEBRERO 2026 - GUARDIAS Y RETENES ===')
    print('Fecha        Dia          Guardia              Retén                Es SIPAT?')
    print('-' * 90)
    
    violaciones = []
    
    for g in guardias:
        persona = Persona.query.get(g.persona_id)
        disponibles = obtener_personas_disponibles(g.fecha, exclude_id=g.persona_id)
        reten_nombre = 'SIN RETÉN'
        
        if disponibles:
            dia_anterior = g.fecha - timedelta(days=1)
            dia_siguiente = g.fecha + timedelta(days=1)
            
            es_guardia_sipat = persona.grado and 'SIPAT' in persona.grado.upper()
            hubo_sipat_reten_ayer = dia_anterior in sipat_reten_fechas
            
            candidatos = []
            for p in disponibles:
                fue_reten_anterior = reten_fechas_dict.get((p.id, dia_anterior), False)
                fue_reten_siguiente = reten_fechas_dict.get((p.id, dia_siguiente), False)
                
                es_reten_sipat = p.id in sipat_ids
                
                # Filtro 1: Si la guardia es de un SIPAT, el retén no puede ser otro SIPAT
                if es_guardia_sipat and es_reten_sipat:
                    continue
                
                # Filtro 2: Si un SIPAT fue retén ayer, ningún SIPAT puede ser retén hoy
                if hubo_sipat_reten_ayer and es_reten_sipat:
                    continue
                
                # Filtro 3: Si este SIPAT tiene guardia mañana, no puede ser retén hoy
                if p.id in sipat_guardia_fechas and dia_siguiente in sipat_guardia_fechas[p.id]:
                    continue
                
                # Filtro 4: Si este SIPAT tuvo guardia ayer, no puede ser retén hoy
                if p.id in sipat_guardia_fechas and dia_anterior in sipat_guardia_fechas[p.id]:
                    continue
                
                # Filtro 5: No fue retén ni antes ni después
                if not fue_reten_anterior and not fue_reten_siguiente:
                    candidatos.append(p)
            
            if not candidatos:
                candidatos = disponibles
            
            candidatos.sort(key=lambda p: reten_contador.get(p.id, 0))
            persona_reten = candidatos[0]
            reten_nombre = persona_reten.nombre
            es_reten_sipat = persona_reten.id in sipat_ids
            
            reten_fechas_dict[(persona_reten.id, g.fecha)] = True
            reten_contador[persona_reten.id] = reten_contador.get(persona_reten.id, 0) + 1
            
            if es_reten_sipat:
                sipat_reten_fechas.add(g.fecha)
            
            dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
            marca_sipat = ' [SIPAT]' if es_reten_sipat else ''
            print(f'{str(g.fecha):<12} {dias[g.fecha.weekday()]:<10} {persona.nombre:<20} {reten_nombre:<20} {marca_sipat}')
    
    print('\n=== VERIFICANDO RETENES SIPAT CONSECUTIVOS ===')
    sipat_retenes_ordenados = sorted(list(sipat_reten_fechas))
    print(f'Fechas con retén SIPAT: {sipat_retenes_ordenados}')
    
    for i in range(len(sipat_retenes_ordenados) - 1):
        diff = (sipat_retenes_ordenados[i+1] - sipat_retenes_ordenados[i]).days
        if diff == 1:
            violaciones.append((sipat_retenes_ordenados[i], sipat_retenes_ordenados[i+1]))
    
    print()
    if violaciones:
        print(f'⚠ RETENES SIPAT CONSECUTIVOS: {len(violaciones)} casos')
        for v in violaciones:
            print(f'  {v[0]} -> {v[1]}')
    else:
        print('✓ NO HAY RETENES SIPAT CONSECUTIVOS')
