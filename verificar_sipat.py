"""
Script para verificar que personas SIPAT no tengan turnos día por medio

Verifica que Campillay, Fortunato y Rivas no tengan guardias separadas
por un día de por medio (ej: guardia día 1, no día 2, guardia día 3).
"""

from app import create_app
from models import Guardia, Persona, db
from datetime import timedelta

PERSONAS_SIPAT = ['A.Fortunato', 'E.Campillay', 'I.Rivas']


def verificar_restriccion_sipat(mes=None, anio=2026):
    """Verifica que las personas SIPAT no tengan turnos día por medio"""
    app = create_app()
    
    with app.app_context():
        print("=== Verificación de restricción SIPAT (no día por medio) ===\n")
        
        # Verificar que las personas tienen grado SIPAT
        print("1. Verificando grado SIPAT de personas:")
        for nombre in PERSONAS_SIPAT:
            persona = Persona.query.filter_by(nombre=nombre).first()
            if persona:
                grado_info = persona.grado if persona.grado else "Sin grado"
                print(f"   {nombre}: {grado_info}")
            else:
                print(f"   {nombre}: NO ENCONTRADA")
        
        print("\n2. Verificando turnos día por medio:")
        
        # Obtener todas las personas SIPAT
        personas_sipat = Persona.query.filter(Persona.nombre.in_(PERSONAS_SIPAT)).all()
        
        # Obtener guardias para cada persona
        guardias_por_persona = {}
        for persona in personas_sipat:
            query = Guardia.query.filter_by(persona_id=persona.id)
            
            if mes:
                from datetime import date
                inicio_mes = date(anio, mes, 1)
                if mes == 12:
                    fin_mes = date(anio + 1, 1, 1) - timedelta(days=1)
                else:
                    fin_mes = date(anio, mes + 1, 1) - timedelta(days=1)
                query = query.filter(
                    Guardia.fecha >= inicio_mes,
                    Guardia.fecha <= fin_mes
                )
            
            guardias = query.order_by(Guardia.fecha).all()
            guardias_por_persona[persona.nombre] = [g.fecha for g in guardias]
        
        # Verificar día por medio para cada persona
        total_violaciones = 0
        for nombre, fechas in guardias_por_persona.items():
            fechas_ordenadas = sorted(fechas)
            violaciones = []
            
            for i in range(len(fechas_ordenadas) - 2):
                fecha_actual = fechas_ordenadas[i]
                fecha_siguiente = fechas_ordenadas[i + 1]
                fecha_tercera = fechas_ordenadas[i + 2]
                
                # Verificar si hay exactamente 2 días de diferencia (día por medio)
                diff = (fecha_tercera - fecha_actual).days
                if diff == 2:
                    violaciones.append((fecha_actual, fecha_siguiente, fecha_tercera))
            
            if violaciones:
                print(f"\n   ⚠ {nombre}: {len(violaciones)} violación(es) encontrada(s)")
                for v in violaciones[:5]:  # Mostrar solo las primeras 5
                    print(f"      {v[0]} -> {v[1]} -> {v[2]} (día por medio)")
                total_violaciones += len(violaciones)
            else:
                print(f"   ✓ {nombre}: Sin violaciones")
        
        print(f"\n{'='*60}")
        if total_violaciones == 0:
            print("✓ RESTRICCIÓN SIPAT CUMPLIDA: No hay turnos día por medio")
        else:
            print(f"⚠ RESTRICCIÓN SIPAT VIOLADA: {total_violaciones} casos encontrados")
        print(f"{'='*60}")
        
        return total_violaciones == 0


if __name__ == '__main__':
    verificar_restriccion_sipat()
