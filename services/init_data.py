"""
Servicio de inicialización de datos
"""
from models import db, Persona


PERSONAS_DEFAULT = [
    {'nombre': 'P.ramirez', 'grado': None},
    {'nombre': 'A.Fortunato', 'grado': 'SIPAT'},      # SIPAT - no día por medio
    {'nombre': 'E.Campillay', 'grado': 'SIPAT'},       # SIPAT - no día por medio
    {'nombre': 'I.Rivas', 'grado': 'SIPAT'},           # SIPAT - no día por medio
    {'nombre': 'V.Rojas', 'grado': None},
    {'nombre': 'G.San Martin', 'grado': None},
    {'nombre': 'L.Henriquez', 'grado': None},
    {'nombre': 'M.Havliczek', 'grado': None},
    {'nombre': 'L.Zamorano', 'grado': None},
    {'nombre': 'M.Rojas', 'grado': None},
    {'nombre': 'A.Terraza', 'grado': None},
    {'nombre': 'A.Rios', 'grado': None}
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
    try:
        if Persona.query.count() == 0:
            for persona_data in PERSONAS_DEFAULT:
                db.session.add(Persona(nombre=persona_data['nombre'], grado=persona_data['grado']))
            db.session.commit()
            print("Base de datos inicializada con personas por defecto")
    except Exception:
        # Si hay error (ej. columna grado no existe), ignorar
        # Esto permite migraciones manuales
        pass
