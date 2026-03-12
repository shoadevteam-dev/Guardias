"""
Rutas principales (páginas web)
"""
from flask import Blueprint, render_template
from models import Persona

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Página principal"""
    personas = Persona.query.filter_by(activo=True).all()
    return render_template('index.html', personas=personas)
