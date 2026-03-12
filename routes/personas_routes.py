"""
Rutas API para Personas
"""
from flask import Blueprint, request, jsonify
from models.models import Persona, Guardia, Novedad, HistoricoAcumulado, db

personas_bp = Blueprint('personas', __name__, url_prefix='/api/personas')


@personas_bp.route('', methods=['GET'])
def get_personas():
    """Obtiene todas las personas"""
    personas = Persona.query.all()
    return jsonify([{
        'id': p.id,
        'nombre': p.nombre,
        'activo': p.activo,
        'acumulado': p.acumulado
    } for p in personas])


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
