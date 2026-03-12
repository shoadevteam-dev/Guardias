"""
Sistema de Gestión de Guardias
Aplicación Flask modular para administración de turnos de guardia

Estructura:
├── app.py                 - Punto de entrada principal
├── models/                - Modelos de base de datos
├── services/              - Lógica de negocio
├── routes/                - Rutas API
├── static/                - Archivos estáticos (CSS, JS, imágenes)
└── templates/             - Plantillas HTML
"""

from flask import Flask, render_template
from models import db, Persona
from routes import personas_bp, guardias_bp, novedades_bp, export_bp


def create_app():
    """Factory de aplicación"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///guardias.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'guardias-secret-key-2026'

    # Inicializar extensiones
    db.init_app(app)

    # Registrar blueprints
    app.register_blueprint(personas_bp)
    app.register_blueprint(guardias_bp)
    app.register_blueprint(novedades_bp)
    app.register_blueprint(export_bp)

    # Rutas principales
    @app.route('/')
    def index():
        """Página principal"""
        personas = Persona.query.filter_by(activo=True).all()
        return render_template('index.html', personas=personas)

    # Inicializar base de datos
    with app.app_context():
        db.create_all()
        if Persona.query.count() == 0:
            _init_default_personas()

    return app


def _init_default_personas():
    """Inicializa personas por defecto"""
    personas_default = [
        'P.ramirez', 'A.Fortunato', 'E.Campillay', 'I.Rivas',
        'V.Rojas', 'G.San Martin', 'L.Henriquez', 'M.Havliczek',
        'L.Zamorano', 'M.Rojas', 'A.Terraza', 'A.Rios'
    ]

    for nombre in personas_default:
        db.session.add(Persona(nombre=nombre))

    db.session.commit()
    print("Base de datos inicializada con personas por defecto")


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5050)
