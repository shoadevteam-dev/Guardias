"""
Servicio de inicialización de datos
"""
from models import db, Persona


PERSONAS_DEFAULT = [
    {'nombre': 'P.Ramirez T.', 'grado': None},
    {'nombre': 'A.Fortunato B.', 'grado': 'SIPAT'},      # SIPAT - no día por medio
    {'nombre': 'E.Campillay G.', 'grado': 'SIPAT'},       # SIPAT - no día por medio
    {'nombre': 'I.Rivas D.', 'grado': 'SIPAT'},           # SIPAT - no día por medio
    {'nombre': 'V.Rojas M.', 'grado': None},
    {'nombre': 'G.San Martin R.', 'grado': None},
    {'nombre': 'L.Henriquez C.', 'grado': None},
    {'nombre': 'M.Havliczek M.', 'grado': None},
    {'nombre': 'L.Zamorano G.', 'grado': None},
    {'nombre': 'M.Rojas S.', 'grado': None},
    {'nombre': 'A.Terraza G.', 'grado': None},
    {'nombre': 'A.Rios A.', 'grado': None}
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
