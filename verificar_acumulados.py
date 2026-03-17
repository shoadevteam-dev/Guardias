"""
Script para verificar y recalcular acumulados
"""
import sys
sys.path.insert(0, '.')

from app import create_app
from models import db, Persona, Guardia
from services.consultas import contar_guardias_mes, obtener_rango_mes
from datetime import datetime

app = create_app()

with app.app_context():
    # Verificar mes actual
    mes = 3
    anio = 2026
    
    print(f"=== Verificación de acumulados para {mes}/{anio} ===\n")
    
    inicio_mes, fin_mes = obtener_rango_mes(mes, anio)
    
    # Contar guardias reales por persona
    print("Guardias reales en base de datos:")
    print(f"{'Persona':<25} {'Guardias Actuales':<20}")
    print("-" * 50)
    
    personas = Persona.query.filter_by(activo=True).all()
    total_guardias = 0
    
    for p in personas:
        guardias = Guardia.query.filter(
            Guardia.persona_id == p.id,
            Guardia.fecha >= inicio_mes.date(),
            Guardia.fecha <= fin_mes.date()
        ).count()
        total_guardias += guardias
        print(f"{p.nombre:<25} {guardias:<20}")
    
    print("-" * 50)
    print(f"Total: {total_guardias} guardias")
    print(f"Promedio: {total_guardias/len(personas):.2f}\n")
    
    # Ver acumulados actuales
    print("Acumulados actuales en DB:")
    print(f"{'Persona':<25} {'Acumulado':<10}")
    print("-" * 40)
    for p in personas:
        print(f"{p.nombre:<25} {p.acumulado or 0:<10}")
    print()
    
    # Forzar recálculo
    from services.guardias_service import calcular_acumulados
    
    print("=== Recalculando acumulados ===\n")
    calcular_acumulados(mes, anio)
    
    # Verificar resultado
    print("\nAcumulados después del recálculo:")
    print(f"{'Persona':<25} {'Acumulado':<10}")
    print("-" * 40)
    personas_actualizadas = Persona.query.filter_by(activo=True).all()
    for p in personas_actualizadas:
        print(f"{p.nombre:<25} {p.acumulado or 0:<10}")
    
    db.session.commit()
    print("\n✓ Cambios guardados en la base de datos")
