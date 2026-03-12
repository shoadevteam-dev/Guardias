"""
Rutas API para Guardias
"""
from flask import Blueprint, request, jsonify
from services import (
    generar_guardias_mes,
    reasignar_guardia,
    reasignar_guardia_random,
    asignar_guardia_manual,
    obtener_guardias_mes,
    obtener_persona_por_id
)
from services.consultas import obtener_rango_mes

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
    """Obtiene las guardias de un mes"""
    inicio_mes, fin_mes = obtener_rango_mes(int(mes), int(anio))
    guardias = obtener_guardias_mes(int(mes), int(anio))

    print(f"API /api/guardias/{mes}/{anio}: {len(guardias)} guardias encontradas")

    resultado = []
    for g in guardias:
        persona = obtener_persona_por_id(g.persona_id)
        persona_original = obtener_persona_por_id(g.persona_original_id) if g.persona_original_id else None
        resultado.append({
            'id': g.id,
            'fecha': g.fecha.strftime('%Y-%m-%d'),
            'fecha_display': g.fecha.strftime('%d/%m/%Y'),
            'dia_semana': g.fecha.strftime('%A'),
            'persona_id': g.persona_id,
            'persona_nombre': persona.nombre if persona else 'N/A',
            'tipo': g.tipo,
            'es_suplencia': g.es_suplencia,
            'persona_original_nombre': persona_original.nombre if persona_original else None
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
