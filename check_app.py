from app import create_app
from models import Guardia, Persona

app = create_app()
print('App creada')

with app.app_context():
    print('En contexto')
    guardias = Guardia.query.count()
    print(f'Guardias: {guardias}')
    
    personas = Persona.query.filter(Persona.grado.like('%SIPAT%')).all()
    print(f'SIPAT: {[p.nombre for p in personas]}')
