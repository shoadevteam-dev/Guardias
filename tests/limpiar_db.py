"""Script para limpiar toda la DB menos las personas"""

from app import create_app
from models import Guardia, Novedad, HistoricoAcumulado, db

app = create_app()

with app.app_context():
    print("=== LIMPIANDO BASE DE DATOS ===")
    print("Eliminando guardias, novedades y acumulados históricos...")
    print("(Las personas se mantienen)")
    
    # Eliminar todo
    guardias_eliminadas = Guardia.query.delete()
    novedades_eliminadas = Novedad.query.delete()
    historico_eliminado = HistoricoAcumulado.query.delete()
    
    # Resetear acumulados de personas
    from models import Persona
    personas = Persona.query.filter_by(activo=True).all()
    for p in personas:
        p.acumulado = 0
    
    db.session.commit()
    
    print(f"\n✓ Guardias eliminadas: {guardias_eliminadas}")
    print(f"✓ Novedades eliminadas: {novedades_eliminadas}")
    print(f"✓ Histórico acumulados eliminado: {historico_eliminado}")
    print(f"✓ Acumulados de personas reseteados: {len(personas)}")
    print("\n=== DB LISTA ===")
    print("Ahora puedes generar los meses del año en orden")
    print("El sistema hará balanceo rotativo mes a mes")
