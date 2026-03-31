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


def esta_en_descanso(persona_id, fecha):
    """Verifica si una persona está en período de descanso después de una guardia
    
    Regla de entrega de guardia:
    - Lunes: entrega Martes, descansa Martes, vuelve Miércoles
    - Martes: entrega Miércoles, descansa Miércoles, vuelve Jueves
    - Miércoles: entrega Jueves, descansa Jueves, vuelve Viernes
    - Jueves: entrega Viernes, descansa Viernes + Fin de Semana, vuelve Lunes
    - Viernes: entrega Sábado, descansa Sábado + Domingo + Lunes, vuelve Martes
    - Sábado: entrega Domingo, descansa Domingo + Lunes, vuelve Martes
    - Domingo: entrega Lunes, descansa Lunes, vuelve Martes
    
    Args:
        persona_id: ID de la persona
        fecha: Fecha actual a validar
        
    Returns:
        True si la persona está en período de descanso, False si puede tener guardia
    """
    # Buscar guardias anteriores (últimos 4 días para cubrir el caso más largo: Viernes)
    for dias_atras in range(1, 5):
        fecha_guardia = fecha - timedelta(days=dias_atras)
        guardia = Guardia.query.filter_by(
            persona_id=persona_id,
            fecha=fecha_guardia
        ).first()
        
        if guardia:
            dia_semana_guardia = fecha_guardia.weekday()  # 0=Lunes, 6=Domingo
            dias_desde_guardia = (fecha - fecha_guardia).days
            
            # Calcular días de descanso según el día de la guardia
            if dia_semana_guardia == 0:  # Lunes
                # Descansa Martes (1 día después)
                if dias_desde_guardia == 1:
                    return True
            elif dia_semana_guardia == 1:  # Martes
                # Descansa Miércoles (1 día después)
                if dias_desde_guardia == 1:
                    return True
            elif dia_semana_guardia == 2:  # Miércoles
                # Descansa Jueves (1 día después)
                if dias_desde_guardia == 1:
                    return True
            elif dia_semana_guardia == 3:  # Jueves
                # Descansa Viernes, Sábado, Domingo (1, 2, 3 días después)
                if dias_desde_guardia in [1, 2, 3]:
                    return True
            elif dia_semana_guardia == 4:  # Viernes
                # Descansa Sábado, Domingo, Lunes (1, 2, 3 días después)
                if dias_desde_guardia in [1, 2, 3]:
                    return True
            elif dia_semana_guardia == 5:  # Sábado
                # Descansa Domingo, Lunes (1, 2 días después)
                if dias_desde_guardia in [1, 2]:
                    return True
            elif dia_semana_guardia == 6:  # Domingo
                # Descansa Lunes (1 día después)
                if dias_desde_guardia == 1:
                    return True
            
            # Si ya pasó el período de descanso, no bloquear
            return False
    
    return False


def tuvo_guardia_viernes_o_sabado_semana_anterior(persona_id, fecha):
    """Verifica si una persona tuvo guardia el Viernes o Sábado de la semana anterior
    
    Esta regla busca evitar que la misma persona tenga guardia el Viernes o Sábado
    en semanas consecutivas, para rotar estos turnos más pesados.
    
    Args:
        persona_id: ID de la persona
        fecha: Fecha actual a validar
        
    Returns:
        True si tuvo guardia el Viernes o Sábado de la semana anterior, False otherwise
    """
    # Calcular la fecha del mismo día de la semana anterior
    fecha_semana_anterior = fecha - timedelta(days=7)
    
    # Verificar si tuvo guardia el Viernes o Sábado de la semana anterior
    guardia_viernes = Guardia.query.filter_by(
        persona_id=persona_id,
        fecha=fecha_semana_anterior
    ).first()
    
    # También verificar el Sábado de la semana anterior
    fecha_sabado_semana_anterior = fecha_semana_anterior + timedelta(days=1)
    guardia_sabado = Guardia.query.filter_by(
        persona_id=persona_id,
        fecha=fecha_sabado_semana_anterior
    ).first()
    
    return guardia_viernes is not None or guardia_sabado is not None


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


def formatear_nombre(nombre):
    """Formatea el nombre en el formato abreviado en mayúscula
    Ejemplos:
    - P.Ramirez T. -> P. RAMIREZ T.
    - A.Fortunato B. -> A. FORTUNATO B.
    - G.San Martin R. -> G. SAN MARTIN R.
    """
    if not nombre:
        return nombre

    nombre = nombre.strip().upper()
    # Normalizar espacios alrededor de puntos y eliminar múltiples espacios
    nombre = nombre.replace('.', '. ').replace('  ', ' ').strip()
    while '  ' in nombre:
        nombre = nombre.replace('  ', ' ')

    partes = nombre.split()

    # Si el nombre ya viene con inicial y punto (ej: P. RAMIREZ T. o A. FORTUNATO B.)
    if partes and partes[0].endswith('.'):
        if len(partes) == 1:
            return partes[0]
        # Manejar caso con apellido materno (ej: P. RAMIREZ T.)
        if len(partes) >= 3 and partes[-1].endswith('.'):
            # Formato: Inicial Nombre. Apellido Paterno. Inicial Materno.
            return partes[0] + ' ' + ' '.join(partes[1:])
        return partes[0] + ' ' + ' '.join(partes[1:])

    if len(partes) <= 1:
        return nombre
    if len(partes) == 2:
        return partes[0][0] + '. ' + partes[1]
    if len(partes) == 3:
        return partes[0][0] + '. ' + partes[1][0] + '. ' + partes[2]

    # Para más de 3 partes, iniciales juntas de los primeros, inicial del penúltimo, apellido
    iniciales_primeros = ''.join(p[0] for p in partes[:-2])
    inicial_penultimo = partes[-2][0]
    apellido = partes[-1]
    return f"{iniciales_primeros}. {inicial_penultimo}. {apellido}"
