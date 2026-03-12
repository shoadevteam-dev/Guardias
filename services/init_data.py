"""
Servicio de inicialización de datos
"""
from models import db, Persona


PERSONAS_DEFAULT = [
    'P.ramirez', 'A.Fortunato', 'E.Campillay', 'I.Rivas',
    'V.Rojas', 'G.San Martin', 'L.Henriquez', 'M.Havliczek',
    'L.Zamorano', 'M.Rojas', 'A.Terraza', 'A.Rios'
]


def init_database(app):
    """
    Inicializa la base de datos creando tablas y datos por defecto
    
    Args:
        app: Aplicación Flask
    """
    with app.app_context():
        db.create_all()
        _init_default_personas()


def _init_default_personas():
    """Inicializa personas por defecto si no existen"""
    if Persona.query.count() == 0:
        for nombre in PERSONAS_DEFAULT:
            db.session.add(Persona(nombre=nombre))
        db.session.commit()
        print("Base de datos inicializada con personas por defecto")
