"""Script de prueba para verificar que la aplicación funciona"""

print("=" * 50)
print("Probando importación de módulos...")
print("=" * 50)

try:
    from models import db, Persona, Guardia, Novedad, HistoricoAcumulado
    print("✓ Models importados correctamente")
except Exception as e:
    print(f"✗ Error en models: {e}")

try:
    from services import (
        obtener_personas_disponibles,
        contar_guardias_mes,
        generar_guardias_mes,
        exportar_guardias_excel
    )
    print("✓ Servicios importados correctamente")
except Exception as e:
    print(f"✗ Error en services: {e}")

try:
    from routes import personas_bp, guardias_bp, novedades_bp, export_bp
    print("✓ Rutas importadas correctamente")
except Exception as e:
    print(f"✗ Error en routes: {e}")

try:
    from app import create_app
    app = create_app()
    print("✓ Aplicación creada exitosamente")
    print(f"  - Base de datos: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print(f"  - Blueprints registrados: {len(app.blueprints)}")
except Exception as e:
    print(f"✗ Error al crear app: {e}")
    import traceback
    traceback.print_exc()

print("=" * 50)
print("Prueba completada")
print("=" * 50)
