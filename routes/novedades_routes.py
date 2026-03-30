"""
Rutas API para Novedades
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from models.models import Novedad, Persona, db
from services.consultas import obtener_persona_por_id, formatear_nombre

novedades_bp = Blueprint('novedades', __name__, url_prefix='/api/novedades')


@novedades_bp.route('', methods=['GET'])
def get_novedades():
    """Obtiene todas las novedades"""
    novedades = Novedad.query.all()
    resultado = []
    for n in novedades:
        persona = obtener_persona_por_id(n.persona_id)
        resultado.append({
            'id': n.id,
            'persona_id': n.persona_id,
            'persona_nombre': formatear_nombre(persona.nombre) if persona else 'N/A',
            'fecha_inicio': n.fecha_inicio.strftime('%Y-%m-%d'),
            'fecha_fin': n.fecha_fin.strftime('%Y-%m-%d'),
            'tipo': n.tipo,
            'descripcion': n.descripcion
        })
    return jsonify(resultado)


@novedades_bp.route('', methods=['POST'])
def add_novedad():
    """Agrega una nueva novedad"""
    data = request.json
    if not data or 'persona_id' not in data or 'fecha_inicio' not in data or 'fecha_fin' not in data:
        return jsonify({'error': 'Datos incompletos'}), 400

    novedad = Novedad(
        persona_id=int(data['persona_id']),
        fecha_inicio=datetime.strptime(data['fecha_inicio'], '%Y-%m-%d').date(),
        fecha_fin=datetime.strptime(data['fecha_fin'], '%Y-%m-%d').date(),
        tipo=data['tipo'],
        descripcion=data.get('descripcion', '')
    )

    db.session.add(novedad)
    db.session.commit()

    return jsonify({
        'id': novedad.id,
        'persona_id': novedad.persona_id,
        'fecha_inicio': novedad.fecha_inicio.strftime('%Y-%m-%d'),
        'fecha_fin': novedad.fecha_fin.strftime('%Y-%m-%d'),
        'tipo': novedad.tipo,
        'descripcion': novedad.descripcion
    })


@novedades_bp.route('/<int:id>', methods=['DELETE'])
def delete_novedad(id):
    """Elimina una novedad"""
    novedad = Novedad.query.get_or_404(id)
    db.session.delete(novedad)
    db.session.commit()
    return jsonify({'message': 'Novedad eliminada'})
