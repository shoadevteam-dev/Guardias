"""
Servicios de consulta - Operaciones de lectura
"""
from datetime import datetime, timedelta
from models.models import Guardia, Novedad, Persona


def obtener_personas_disponibles(fecha, exclude_id=None):
    """Obtiene personas disponibles para una fecha específica"""
    personas = Persona.query.filter_by(activo=True).all()
    disponibles = []

    for p in personas:
        if exclude_id and p.id == exclude_id:
            continue

        tiene_novedad = Novedad.query.filter(
            Novedad.persona_id == p.id,
            Novedad.fecha_inicio <= fecha,
            Novedad.fecha_fin >= fecha
        ).first()

        if tiene_novedad:
            continue

        disponibles.append(p)

    return disponibles


def contar_guardias_mes(persona_id, mes, anio):
    """Cuenta las guardias de una persona en un mes específico

    Solo cuenta:
    1. Guardias donde la persona es el titular actual (persona_id)
    
    No cuenta las guardias donde fue reemplazado (persona_original_id),
    porque el acumulado debe reflejar las guardias que cada uno realmente hizo,
    no las que tenía asignadas originalmente.
    """
    inicio_mes = datetime(anio, mes, 1)
    if mes == 12:
        fin_mes = datetime(anio + 1, 1, 1) - timedelta(days=1)
    else:
        fin_mes = datetime(anio, mes + 1, 1) - timedelta(days=1)

    # Contar solo guardias actuales (como titular)
    guardias_actuales = Guardia.query.filter(
        Guardia.persona_id == persona_id,
        Guardia.fecha >= inicio_mes.date(),
        Guardia.fecha <= fin_mes.date()
    ).count()

    return guardias_actuales


def tiene_guardia_anterior(persona_id, fecha):
    """Verifica si la persona tuvo guardia el día anterior"""
    dia_anterior = fecha - timedelta(days=1)
    guardia = Guardia.query.filter_by(
        persona_id=persona_id,
        fecha=dia_anterior
    ).first()
    return guardia is not None


def tiene_guardia_dia_medio(persona_id, fecha):
    """Verifica si la persona tuvo guardia hace 2 días (día por medio)

    Esta validación es para personas SIPAT que no deben tener turnos
    separados por un día de por medio.

    Args:
        persona_id: ID de la persona
        fecha: Fecha actual a validar

    Returns:
        True si tuvo guardia hace 2 días (fecha - 2), False otherwise
    """
    dia_hace_dos = fecha - timedelta(days=2)
    guardia = Guardia.query.filter_by(
        persona_id=persona_id,
        fecha=dia_hace_dos
    ).first()
    return guardia is not None


def tiene_sipat_guardia_anterior(fecha):
    """Verifica si algún SIPAT tuvo guardia el día anterior

    Esta validación es para evitar que personas SIPAT tengan guardias
    consecutivas entre ellos (ej: Fortunato Viernes, Campillay Sábado).

    Args:
        fecha: Fecha actual a validar

    Returns:
        True si algún SIPAT tuvo guardia el día anterior (fecha - 1), False otherwise
    """
    from models.models import Persona
    dia_anterior = fecha - timedelta(days=1)

    # Obtener todos los SIPAT
    sipats = Persona.query.filter_by(grado='SIPAT').all()
    sipat_ids = [p.id for p in sipats]

    # Verificar si algún SIPAT tuvo guardia el día anterior
    guardia = Guardia.query.filter(
        Guardia.persona_id.in_(sipat_ids),
        Guardia.fecha == dia_anterior
    ).first()

    return guardia is not None


def tuvo_sipat_guardia_en_rango(fecha_inicio, fecha_fin):
    """Verifica si algún SIPAT tuvo guardia en un rango de fechas

    Esta validación es para evitar que personas SIPAT tengan guardias
    consecutivas entre ellos.

    Args:
        fecha_inicio: Fecha de inicio del rango (inclusive)
        fecha_fin: Fecha de fin del rango (inclusive)

    Returns:
        True si algún SIPAT tuvo guardia en el rango, False otherwise
    """
    from models.models import Persona
    
    # Obtener todos los SIPAT
    sipats = Persona.query.filter_by(grado='SIPAT').all()
    sipat_ids = [p.id for p in sipats]

    # Verificar si algún SIPAT tuvo guardia en el rango
    guardia = Guardia.query.filter(
        Guardia.persona_id.in_(sipat_ids),
        Guardia.fecha >= fecha_inicio,
        Guardia.fecha <= fecha_fin
    ).first()

    return guardia is not None


def obtener_rango_mes(mes, anio):
    """Obtiene fecha inicio y fin de un mes"""
    inicio_mes = datetime(anio, mes, 1)
    if mes == 12:
        fin_mes = datetime(anio + 1, 1, 1) - timedelta(days=1)
    else:
        fin_mes = datetime(anio, mes + 1, 1) - timedelta(days=1)
    return inicio_mes, fin_mes


def obtener_guardias_mes(mes, anio):
    """Obtiene todas las guardias de un mes ordenadas por fecha"""
    inicio_mes, fin_mes = obtener_rango_mes(mes, anio)
    return Guardia.query.filter(
        Guardia.fecha >= inicio_mes.date(),
        Guardia.fecha <= fin_mes.date()
    ).order_by(Guardia.fecha).all()


def obtener_persona_por_id(persona_id):
    """Obtiene una persona por su ID"""
    return Persona.query.get(persona_id)


def obtener_todas_las_personas():
    """Obtiene todas las personas"""
    return Persona.query.all()


def obtener_personas_activas():
    """Obtiene solo las personas activas"""
    return Persona.query.filter_by(activo=True).all()
