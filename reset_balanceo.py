"""Script para verificar y resetear acumulados"""

from app import create_app
from models import Guardia, Persona, HistoricoAcumulado
from services.consultas import contar_guardias_mes

app = create_app()

with app.app_context():
    print("=== ESTADO ACTUAL DE ACUMULADOS ===\n")
    
    personas = Persona.query.filter_by(activo=True).all()
    
    print(f"{'Persona':<25} {'Acumulado DB':<15}")
    print("-" * 45)
    for p in personas:
        print(f"{p.nombre:<25} {p.acumulado:<15}")
    
    print("\n=== Guardias por mes ===")
    for mes in [1, 2]:
        print(f"\nMes {mes}:")
        for p in personas:
            guardias = contar_guardias_mes(p.id, mes, 2026)
            if guardias > 0:
                print(f"  {p.nombre}: {guardias}")
    
    print("\n\n=== OPCIONES ===")
    print("1. Resetear todos los acumulados a 0")
    print("2. Eliminar guardias de Febrero y recalcular")
    print("3. Salir")
    
    opcion = input("\nSelecciona una opción (1-3): ")
    
    if opcion == "1":
        confirm = input("¿Seguro que quieres resetear TODOS los acumulados? (s/n): ")
        if confirm.lower() == 's':
            for p in personas:
                p.acumulado = 0
            HistoricoAcumulado.query.delete()
            from models import db
            db.session.commit()
            print("✓ Acumulados reseteados a cero")
        else:
            print("Operación cancelada")
    
    elif opcion == "2":
        from datetime import datetime
        confirm = input("¿Seguro que quieres eliminar Febrero 2026? (s/n): ")
        if confirm.lower() == 's':
            inicio = datetime(2026, 2, 1)
            fin = datetime(2026, 2, 28)
            
            # Eliminar guardias de febrero
            Guardia.query.filter(
                Guardia.fecha >= inicio.date(),
                Guardia.fecha <= fin.date()
            ).delete()
            
            # Resetear acumulados
            for p in personas:
                p.acumulado = 0
            HistoricoAcumulado.query.delete()
            
            from models import db
            db.session.commit()
            print("✓ Febrero eliminado y acumulados reseteados")
            print("Ahora puedes volver a generar Febrero desde la aplicación")
        else:
            print("Operación cancelada")
    
    print("\nFin del script")
