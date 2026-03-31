"""Script para probar el balanceo anual completo"""

import argparse

from app import create_app
from models import Guardia, Persona, HistoricoAcumulado, db
from services import generar_guardias_mes
from services.consultas import contar_guardias_mes

parser = argparse.ArgumentParser(description='Test de balanceo anual de guardias')
parser.add_argument('--anio', type=int, default=2026, help='Año a generar (default: 2026)')
parser.add_argument('--no-reset', action='store_true', help='No resetear la base de datos (mantener años anteriores)')
args = parser.parse_args()

app = create_app()

with app.app_context():
    print("=" * 80)
    print(f"PRUEBA DE BALANCEO ANUAL - {args.anio}")
    print("=" * 80)
    
    if not args.no_reset:
        # Resetear todo primero
        print("\n1. Reseteando base de datos...")
        Guardia.query.delete()
        HistoricoAcumulado.query.delete()
        for p in Persona.query.filter_by(activo=True).all():
            p.acumulado = 0
        db.session.commit()
        print("   DB reseteada correctamente\n")
    else:
        print("\n1. Manteniendo datos anteriores (no reset)\n")
    
    personas = Persona.query.filter_by(activo=True).all()
    
    # Generar todos los meses del año
    meses_nombres = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
        7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }
    
    for mes in range(1, 13):
        print(f"\n{'='*80}")
        print(f"GENERANDO {meses_nombres[mes].upper()} {args.anio}")
        print(f"{'='*80}")
        generar_guardias_mes(mes, args.anio)
    
    # Resumen final del año
    print("\n\n" + "=" * 80)
    print(f"RESUMEN ANUAL {args.anio}")
    print("=" * 80)
    print(f"{'Persona':<25}", end="")
    for mes in range(1, 13):
        print(f"{meses_nombres[mes][:3]:>4}", end="")
    print(f"{' TOTAL':>6}")
    print("-" * 80)
    
    for p in sorted(personas, key=lambda x: sum(contar_guardias_mes(x.id, m, args.anio) for m in range(1, 13))):
        total = sum(contar_guardias_mes(p.id, mes, args.anio) for mes in range(1, 13))
        print(f"{p.nombre:<25}", end="")
        for mes in range(1, 13):
            guardias = contar_guardias_mes(p.id, mes, args.anio)
            print(f"{guardias:>4}", end="")
        print(f"{total:>6}")
    
    print("=" * 80)
    print("\n✓ Todos los meses generados con balanceo anual")
