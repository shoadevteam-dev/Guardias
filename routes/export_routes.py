"""
Rutas API para Exportación y Acumulados
"""
from flask import Blueprint, send_file, jsonify
from services import exportar_guardias_excel
from services.consultas import obtener_personas_activas, formatear_nombre

export_bp = Blueprint('export', __name__, url_prefix='/api')


@export_bp.route('/exportar/<mes>/<anio>', methods=['GET'])
def exportar_excel(mes, anio):
    """Exporta las guardias a Excel"""
    buffer = exportar_guardias_excel(int(mes), int(anio))
    return send_file(
        buffer,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'guardias_{mes}_{anio}.xlsx'
    )


@export_bp.route('/acumulados', methods=['GET'])
def get_acumulados():
    """Obtiene los acumulados actuales"""
    personas = obtener_personas_activas()
    return jsonify([{
        'id': p.id,
        'nombre': formatear_nombre(p.nombre),
        'acumulado': p.acumulado
    } for p in personas])
