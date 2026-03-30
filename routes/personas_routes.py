"""
Rutas API para Personas
"""
from flask import Blueprint, request, jsonify
from models.models import Persona, Guardia, Novedad, HistoricoAcumulado, db
from services.consultas import formatear_nombre, contar_guardias_mes
from services.guardias_service import calcular_retenes_por_mes

personas_bp = Blueprint('personas', __name__, url_prefix='/api/personas')


@personas_bp.route('', methods=['GET'])
def get_personas():
    """Obtiene todas las personas"""
    personas = Persona.query.all()

    mes = request.args.get('mes', type=int)
    anio = request.args.get('anio', type=int)

    guardias_por_persona = {}
    retenes_por_persona = {}

    if mes and anio:
        for p in personas:
            guardias_por_persona[p.id] = contar_guardias_mes(p.id, mes, anio)
        _, retenes_por_persona = calcular_retenes_por_mes(mes, anio)

    resultado = []
    for p in personas:
        guardias = guardias_por_persona.get(p.id, 0)
        retenes = retenes_por_persona.get(p.id, 0)

        resultado.append({
            'id': p.id,
            'nombre': 'PAC ' + formatear_nombre(p.nombre),
            'activo': p.activo,
            'acumulado': p.acumulado,
            'guardias': guardias,
            'retenes': retenes
        })

    return jsonify(resultado)


@personas_bp.route('', methods=['POST'])
def add_persona():
    """Agrega una nueva persona"""
    data = request.json
    if not data or 'nombre' not in data:
        return jsonify({'error': 'Nombre requerido'}), 400

    persona = Persona(nombre=data['nombre'].strip())
    db.session.add(persona)
    db.session.commit()

    return jsonify({
        'id': persona.id,
        'nombre': persona.nombre,
        'activo': persona.activo,
        'acumulado': persona.acumulado
    })


@personas_bp.route('/<int:id>', methods=['PUT'])
def update_persona(id):
    """Actualiza una persona"""
    persona = Persona.query.get_or_404(id)
    data = request.json

    if 'nombre' in data:
        persona.nombre = data['nombre'].strip()
    if 'activo' in data:
        persona.activo = data['activo']
    if 'acumulado' in data:
        persona.acumulado = data['acumulado']

    db.session.commit()
    return jsonify({
        'id': persona.id,
        'nombre': persona.nombre,
        'activo': persona.activo,
        'acumulado': persona.acumulado
    })


@personas_bp.route('/<int:id>/toggle-activo', methods=['POST'])
def toggle_activo(id):
    """Cambia el estado activo/inactivo de una persona"""
    persona = Persona.query.get_or_404(id)
    persona.activo = not persona.activo
    db.session.commit()

    return jsonify({
        'id': persona.id,
        'nombre': persona.nombre,
        'activo': persona.activo
    })
