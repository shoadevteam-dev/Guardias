"""
Sistema de Gestión de Guardias
Aplicación Flask modular para administración de turnos de guardia

Estructura:
├── app.py                 - Punto de entrada principal
├── config.py              - Configuración de la aplicación
├── models/                - Modelos de base de datos
├── services/              - Lógica de negocio
├── routes/                - Rutas API
├── static/                - Archivos estáticos (CSS, JS, imágenes)
└── templates/             - Plantillas HTML
"""

from flask import Flask
from config import config
from models import db
from routes import (
    personas_bp,
    guardias_bp,
    novedades_bp,
    export_bp,
    main_bp
)
from services import init_database


def create_app(config_name: str = 'default') -> Flask:
    """
    Factory de aplicación
    
    Args:
        config_name: Nombre de la configuración a usar
        
    Returns:
        Aplicación Flask configurada
    """
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Inicializar extensiones
    db.init_app(app)

    # Registrar blueprints
    _register_blueprints(app)

    # Inicializar base de datos
    init_database(app)

    return app


def _register_blueprints(app: Flask) -> None:
    """Registra todos los blueprints de la aplicación"""
    app.register_blueprint(main_bp)
    app.register_blueprint(personas_bp)
    app.register_blueprint(guardias_bp)
    app.register_blueprint(novedades_bp)
    app.register_blueprint(export_bp)


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5050)
