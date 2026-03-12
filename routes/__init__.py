"""
Paquete de rutas API
"""
from .main_routes import main_bp
from .personas_routes import personas_bp
from .guardias_routes import guardias_bp
from .novedades_routes import novedades_bp
from .export_routes import export_bp

__all__ = ['main_bp', 'personas_bp', 'guardias_bp', 'novedades_bp', 'export_bp']
