"""
Rutas API para Guardias
"""
from flask import Blueprint, request, jsonify
from datetime import timedelta
from services import (
    generar_guardias_mes,
    reasignar_guardia,
    reasignar_guardia_random,
    asignar_guardia_manual,
    obtener_guardias_mes,
    obtener_persona_por_id,
    resetear_acumulados
)
from services.guardias_service import calcular_retenes_por_mes
from services.consultas import obtener_rango_mes, obtener_personas_disponibles, formatear_nombre
from models.models import Persona, Guardia

guardias_bp = Blueprint('guardias', __name__, url_prefix='/api/guardias')


@guardias_bp.route('/generar', methods=['POST'])
def generar_guardias():
    """Genera las guardias para un mes específico"""
    data = request.json
    if not data or 'mes' not in data or 'anio' not in data:
        return jsonify({'error': 'Mes y año requeridos'}), 400

    mes, anio = int(data['mes']), int(data['anio'])
    if mes < 1 or mes > 12:
        return jsonify({'error': 'Mes inválido'}), 400

    exito = generar_guardias_mes(mes, anio)
    if exito:
        return jsonify({'message': f'Guardias generadas para {mes}/{anio}'})
    else:
        return jsonify({'error': 'No hay personas activas'}), 400


@guardias_bp.route('/<mes>/<anio>', methods=['GET'])
def get_guardias_mes(mes, anio):
    """Obtiene las guardias de un mes con información de retén"""
    inicio_mes, fin_mes = obtener_rango_mes(int(mes), int(anio))
    guardias = obtener_guardias_mes(int(mes), int(anio))

    print(f"API /api/guardias/{mes}/{anio}: {len(guardias)} guardias encontradas")

    # Mapeo de días de la semana: 0=Lunes, 1=Martes, ..., 6=Domingo
    nombres_dias = {
        0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves',
        4: 'Viernes', 5: 'Sábado', 6: 'Domingo'
    }

    # Contador para rotación de retén
    personas_activas = Persona.query.filter_by(activo=True).all()
    reten_contador = {p.id: 0 for p in personas_activas}

    # Diccionario para tracking de retén por persona (para evitar consecutivos)
    # Clave: (persona_id, fecha), Valor: True si fue retén esa fecha
    reten_fechas_dict = {}

    # Tracking adicional para SIPAT: si un SIPAT fue retén ayer, ningún SIPAT puede ser retén hoy
    sipat_reten_fechas = set()  # Fechas donde un SIPAT fue retén
    
    # Tracking de fechas donde los SIPAT tienen guardia (para evitar que sean retenes el día anterior)
    sipat_guardia_fechas = {}  # {persona_id: set(fechas)}
    for g in guardias:
        persona = obtener_persona_por_id(g.persona_id)
        if persona and persona.grado and 'SIPAT' in persona.grado.upper():
            if g.persona_id not in sipat_guardia_fechas:
                sipat_guardia_fechas[g.persona_id] = set()
            sipat_guardia_fechas[g.persona_id].add(g.fecha)
    
    # Crear un set de todas las fechas donde cualquier SIPAT tiene guardia
    todas_sipat_guardia_fechas = set()
    for fechas in sipat_guardia_fechas.values():
        todas_sipat_guardia_fechas.update(fechas)

    reten_por_fecha, reten_contador = calcular_retenes_por_mes(int(mes), int(anio))

    resultado = []
    for g in guardias:
        persona = obtener_persona_por_id(g.persona_id)
        persona_original = obtener_persona_por_id(g.persona_original_id) if g.persona_original_id else None

        reten_persona_id = reten_por_fecha.get(g.fecha)
        if reten_persona_id:
            persona_reten = obtener_persona_por_id(reten_persona_id)
            reten_nombre = persona_reten.nombre if persona_reten else 'SIN RETÉN'
        else:
            reten_nombre = 'SIN RETÉN'

        resultado.append({
            'id': g.id,
            'fecha': g.fecha.strftime('%Y-%m-%d'),
            'fecha_display': g.fecha.strftime('%d/%m/%Y'),
            'dia_semana': nombres_dias[g.fecha.weekday()],
            'persona_id': g.persona_id,
            'persona_nombre': 'PAC ' + formatear_nombre(persona.nombre) if persona else 'N/A',
            'reten_nombre': 'SIN RETÉN' if reten_nombre.upper().startswith('SIN RET') else 'PAC ' + formatear_nombre(reten_nombre),
            'tipo': g.tipo,
            'es_suplencia': g.es_suplencia,
            'persona_original_nombre': formatear_nombre(persona_original.nombre) if persona_original else None,
            'reten_contador': reten_contador
        })

    return jsonify(resultado)


@guardias_bp.route('/reasignar', methods=['POST'])
def reasignar():
    """Reasigna una guardia manualmente"""
    data = request.json
    if not data or 'fecha' not in data or 'persona_id' not in data:
        return jsonify({'error': 'Fecha y persona_id requeridos'}), 400

    exito, mensaje = reasignar_guardia(
        data['fecha'],
        int(data['persona_id']),
        data.get('motivo', '')
    )

    if exito:
        return jsonify({'message': mensaje})
    else:
        return jsonify({'error': mensaje}), 400


@guardias_bp.route('/reasignar-random', methods=['POST'])
def reasignar_random():
    """Reasigna una guardia aleatoriamente"""
    data = request.json
    if not data or 'fecha' not in data:
        return jsonify({'error': 'Fecha requerida'}), 400

    exito, mensaje, anterior, nuevo = reasignar_guardia_random(data['fecha'])

    if exito:
        return jsonify({
            'message': mensaje,
            'persona_anterior': anterior,
            'persona_nueva': nuevo
        })
    else:
        return jsonify({'error': mensaje}), 400


@guardias_bp.route('/asignar', methods=['POST'])
def asignar_manual():
    """Asigna manualmente una guardia en una fecha específica"""
    data = request.json
    if not data or 'fecha' not in data or 'persona_id' not in data:
        return jsonify({'error': 'Fecha y persona_id requeridos'}), 400

    exito, mensaje = asignar_guardia_manual(data['fecha'], int(data['persona_id']))

    if exito:
        return jsonify({'message': mensaje})
    else:
        return jsonify({'error': mensaje}), 400


@guardias_bp.route('/<mes>/<anio>/eliminar', methods=['POST'])
def eliminar_calendario(mes, anio):
    """Elimina todas las guardias y acumulados de un mes específico"""
    from models.models import Guardia, HistoricoAcumulado, db
    from services.consultas import obtener_rango_mes
    from services.guardias_service import eliminar_acumulados_mes

    inicio_mes, fin_mes = obtener_rango_mes(int(mes), int(anio))

    # 1. Primero restar acumulados de las personas (antes de borrar el histórico)
    eliminar_acumulados_mes(int(mes), int(anio))

    # 2. Eliminar guardias del mes
    guardias_eliminadas = Guardia.query.filter(
        Guardia.fecha >= inicio_mes.date(),
        Guardia.fecha <= fin_mes.date()
    ).delete()

    # 3. Eliminar registros históricos del mes
    HistoricoAcumulado.query.filter_by(mes=int(mes), anio=int(anio)).delete()

    db.session.commit()

    return jsonify({
        'message': f'Se eliminaron {guardias_eliminadas} guardias y acumulados del mes {mes}/{anio}'
    })


@guardias_bp.route('/resetear-acumulados', methods=['POST'])
def resetear_todos_acumulados():
    """Resetea todos los acumulados a cero"""
    resetear_acumulados()
    return jsonify({'message': 'Acumulados reseteados a cero'})
