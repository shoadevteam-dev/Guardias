"""Debug script para verificacion SIPAT retenes"""
from app import create_app
from models import Guardia, Persona
from services.consultas import obtener_rango_mes, obtener_personas_disponibles
from services.guardias_service import generar_guardias_mes
from datetime import timedelta

app = create_app()
with app.app_context():
    print('Generando enero 2026...')
    generar_guardias_mes(1, 2026)
    
    mes, anio = 1, 2026
    inicio_mes, fin_mes = obtener_rango_mes(mes, anio)
    guardias = Guardia.query.filter(
        Guardia.fecha >= inicio_mes.date(), 
        Guardia.fecha <= fin_mes.date()
    ).order_by(Guardia.fecha).all()
    
    personas_activas = Persona.query.filter_by(activo=True).all()
    reten_contador = {p.id: 0 for p in personas_activas}
    reten_fechas_dict = {}
    sipat_reten_fechas = set()
    
    sipats = Persona.query.filter(Persona.grado.like('%SIPAT%')).all()
    sipat_ids = [p.id for p in sipats]
    sipat_nombres = {p.id: p.nombre for p in sipats}
    print(f'SIPAT IDs: {sipat_ids}')
    print(f'SIPAT Nombres: {sipat_nombres}')
    
    sipat_guardia_fechas = {}
    for g in guardias:
        if g.persona_id in sipat_ids:
            if g.persona_id not in sipat_guardia_fechas:
                sipat_guardia_fechas[g.persona_id] = set()
            sipat_guardia_fechas[g.persona_id].add(g.fecha)
    
    print('\n=== ENERO 2026 - DEBUG ===')
    
    for g in guardias[:10]:  # Solo primeros 10 dias
        persona = Persona.query.get(g.persona_id)
        disponibles = obtener_personas_disponibles(g.fecha, exclude_id=g.persona_id)
        reten_nombre = 'SIN RETEN'
        
        if disponibles:
            dia_anterior = g.fecha - timedelta(days=1)
            dia_siguiente = g.fecha + timedelta(days=1)
            dia_hace_2 = g.fecha - timedelta(days=2)
            
            es_guardia_sipat = persona.grado and 'SIPAT' in persona.grado.upper()
            hubo_sipat_reten_ayer = dia_anterior in sipat_reten_fechas
            hubo_sipat_reten_hace_2 = dia_hace_2 in sipat_reten_fechas
            
            print(f'\n{g.fecha} ({persona.nombre}):')
            print(f'  sipat_reten_fechas: {sipat_reten_fechas}')
            print(f'  dia_anterior={dia_anterior}, hubo_sipat_reten_ayer={hubo_sipat_reten_ayer}')
            print(f'  dia_hace_2={dia_hace_2}, hubo_sipat_reten_hace_2={hubo_sipat_reten_hace_2}')
            
            candidatos = []
            razones_filtro = {}
            
            for p in disponibles:
                fue_reten_anterior = reten_fechas_dict.get((p.id, dia_anterior), False)
                fue_reten_siguiente = reten_fechas_dict.get((p.id, dia_siguiente), False)
                
                es_reten_sipat = p.id in sipat_ids
                
                razon = None
                
                if es_guardia_sipat and es_reten_sipat:
                    razon = 'guardia_es_sipat'
                elif hubo_sipat_reten_ayer and es_reten_sipat:
                    razon = 'sipat_reten_ayer'
                elif hubo_sipat_reten_hace_2 and es_reten_sipat:
                    razon = 'sipat_reten_hace_2'
                elif p.id in sipat_guardia_fechas and dia_siguiente in sipat_guardia_fechas.get(p.id, set()):
                    razon = 'sipat_guardia_manana'
                elif p.id in sipat_guardia_fechas and dia_anterior in sipat_guardia_fechas.get(p.id, set()):
                    razon = 'sipat_guardia_ayer'
                elif fue_reten_anterior or fue_reten_siguiente:
                    razon = 'reten_consecutivo'
                
                if razon:
                    if razon not in razones_filtro:
                        razones_filtro[razon] = []
                    razones_filtro[razon].append(p.nombre)
                else:
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
            
            print(f'  Filtros aplicados: {razones_filtro}')
            print(f'  Candidatos: {[p.nombre for p in candidatos]}')
            print(f'  => RETEN: {reten_nombre} {"[SIPAT]" if es_reten_sipat else ""}')
