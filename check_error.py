from app import create_app

try:
    app = create_app()
    print("App creada correctamente")
    with app.app_context():
        from models import Persona
        print(f"Personas en DB: {Persona.query.count()}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
