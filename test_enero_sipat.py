"""Script para verificar guardias y retenes de marzo 2026 - Caso SIPAT consecutivos"""
from app import create_app
from models import Guardia, Persona
from services.consultas import obtener_rango_mes, obtener_personas_disponibles
from services.guardias_service import generar_guardias_mes
from datetime import timedelta

app = create_app()
with app.app_context():
    # Generar marzo 2026
    print("Generando marzo 2026...")
    generar_guardias_mes(3, 2026)
    
    mes, anio = 3, 2026
    inicio_mes, fin_mes = obtener_rango_mes(mes, anio)
    guardias = Guardia.query.filter(
        Guardia.fecha >= inicio_mes.date(), 
        Guardia.fecha <= fin_mes.date()
    ).order_by(Guardia.fecha).all()
    
    personas_activas = Persona.query.filter_by(activo=True).all()
    reten_contador = {p.id: 0 for p in personas_activas}
    reten_fechas_dict = {}
    sipat_reten_fechas = set()
    
    print('\n=== MARZO 2026 - GUARDIAS Y RETENES ===')
    print('Fecha        Dia          Guardia              Retén                SIPAT?')
    print('-' * 90)
    
    violaciones = []
    retenes_sipat_consecutivos = []
    
    for g in guardias:
        persona = Persona.query.get(g.persona_id)
        disponibles = obtener_personas_disponibles(g.fecha, exclude_id=g.persona_id)
        reten_nombre = 'SIN RETÉN'
        es_guardia_sipat = persona.grado and 'SIPAT' in persona.grado.upper() if persona.grado else False
        
        if disponibles:
            dia_anterior = g.fecha - timedelta(days=1)
            dia_siguiente = g.fecha + timedelta(days=1)
            
            candidatos = []
            for p in disponibles:
                fue_reten_anterior = reten_fechas_dict.get((p.id, dia_anterior), False)
                fue_reten_siguiente = reten_fechas_dict.get((p.id, dia_siguiente), False)
                
                es_reten_sipat = p.grado and 'SIPAT' in p.grado.upper() if p.grado else False
                
                # Si la guardia es de un SIPAT, el retén no puede ser otro SIPAT
                if es_guardia_sipat and es_reten_sipat:
                    continue
                
                # Si un SIPAT fue retén ayer, ningún SIPAT puede ser retén hoy
                hubo_sipat_reten_ayer = dia_anterior in sipat_reten_fechas
                if hubo_sipat_reten_ayer and es_reten_sipat:
                    continue
                
                if not fue_reten_anterior and not fue_reten_siguiente:
                    candidatos.append(p)
            
            if not candidatos:
                candidatos = disponibles
            
            candidatos.sort(key=lambda p: reten_contador.get(p.id, 0))
            persona_reten = candidatos[0]
            reten_nombre = persona_reten.nombre
            es_reten_sipat = persona_reten.grado and 'SIPAT' in persona_reten.grado.upper() if persona_reten.grado else False
            
            reten_fechas_dict[(persona_reten.id, g.fecha)] = True
            reten_contador[persona_reten.id] = reten_contador.get(persona_reten.id, 0) + 1
            
            # Registrar si un SIPAT fue retén hoy
            if es_reten_sipat:
                sipat_reten_fechas.add(g.fecha)
            
            # Marcar violaciones
            marca = ''
            if es_guardia_sipat and es_reten_sipat:
                marca = '*** VIOLACION: SIPAT con retén SIPAT ***'
                violaciones.append((g.fecha, persona.nombre, reten_nombre, 'SIPAT-SIPAT'))
            
            dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
            reten_sipat_marker = ' [SIPAT]' if es_reten_sipat else ''
            print(f'{str(g.fecha):<12} {dias[g.fecha.weekday()]:<10} {persona.nombre:<20} {reten_nombre:<20} G:{es_guardia_sipat}, R:{es_reten_sipat}{reten_sipat_marker} {marca}')
        else:
            print(f'{str(g.fecha):<12} {persona.nombre:<20} {reten_nombre}')
    
    # Verificar retenes SIPAT consecutivos
    print('\n=== VERIFICANDO RETENES SIPAT CONSECUTIVOS ===')
    sipat_retenes_ordenados = sorted(list(sipat_reten_fechas))
    for i in range(len(sipat_retenes_ordenados) - 1):
        diff = (sipat_retenes_ordenados[i+1] - sipat_retenes_ordenados[i]).days
        if diff == 1:
            retenes_sipat_consecutivos.append((sipat_retenes_ordenados[i], sipat_retenes_ordenados[i+1]))
    
    print('\n' + '=' * 90)
    if violaciones:
        print(f'VIOLACIONES ENCONTRADAS: {len(violaciones)}')
        for v in violaciones:
            print(f'  {v[0]}: Guardia {v[1]} -> Retén {v[2]} ({v[3]})')
    else:
        print('✓ NO HAY VIOLACIONES: Ningún SIPAT tiene retén SIPAT')
    
    if retenes_sipat_consecutivos:
        print(f'⚠ RETENES SIPAT CONSECUTIVOS: {len(retenes_sipat_consecutivos)} casos')
        for r in retenes_sipat_consecutivos:
            print(f'  {r[0]} -> {r[1]}')
    else:
        print('✓ NO HAY RETENES SIPAT CONSECUTIVOS')
