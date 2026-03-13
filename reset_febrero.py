"""Script para eliminar Febrero y resetear acumulados"""

from app import create_app
from models import Guardia, Persona, HistoricoAcumulado, db
from datetime import datetime

app = create_app()

with app.app_context():
    print("=== Eliminando guardias de Febrero 2026 ===")
    
    inicio = datetime(2026, 2, 1)
    fin = datetime(2026, 2, 28)
    
    # Eliminar guardias de febrero
    guardias_eliminadas = Guardia.query.filter(
        Guardia.fecha >= inicio.date(),
        Guardia.fecha <= fin.date()
    ).delete()
    
    print(f"Guardias de Febrero eliminadas: {guardias_eliminadas}")
    
    # Resetear acumulados
    personas = Persona.query.filter_by(activo=True).all()
    for p in personas:
        p.acumulado = 0
    
    HistoricoAcumulado.query.delete()
    
    db.session.commit()
    print("Acumulados reseteados a cero")
    print("\n=== LISTO ===")
    print("Ahora puedes generar Febrero desde la aplicación")
    print("El nuevo algoritmo balanceará automáticamente:")
    print("- Quienes hicieron 3 guardias en Enero tendrán MENOS prioridad")
    print("- Quienes hicieron 2 guardias en Enero tendrán MÁS prioridad")
