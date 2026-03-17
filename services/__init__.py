"""
Paquete de servicios
"""
from .consultas import (
    obtener_personas_disponibles,
    contar_guardias_mes,
    tiene_guardia_anterior,
    obtener_rango_mes,
    obtener_guardias_mes,
    obtener_persona_por_id,
    obtener_todas_las_personas,
    obtener_personas_activas
)
from .guardias_service import (
    generar_guardias_mes,
    calcular_acumulados,
    reasignar_guardia,
    reasignar_guardia_random,
    asignar_guardia_manual,
    resetear_acumulados,
    eliminar_acumulados_mes
)
from .excel_service import exportar_guardias_excel
from .init_data import init_database, PERSONAS_DEFAULT

__all__ = [
    # Consultas
    'obtener_personas_disponibles',
    'contar_guardias_mes',
    'tiene_guardia_anterior',
    'obtener_rango_mes',
    'obtener_guardias_mes',
    'obtener_persona_por_id',
    'obtener_todas_las_personas',
    'obtener_personas_activas',
    # Negocio
    'generar_guardias_mes',
    'calcular_acumulados',
    'reasignar_guardia',
    'reasignar_guardia_random',
    'asignar_guardia_manual',
    'resetear_acumulados',
    'eliminar_acumulados_mes',
    # Excel
    'exportar_guardias_excel',
    # Inicialización
    'init_database',
    'PERSONAS_DEFAULT'
]
