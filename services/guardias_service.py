"""
Servicios de negocio - Lógica de guardias
"""
import random
from datetime import datetime, timedelta
from models.models import Guardia, Persona, HistoricoAcumulado, Novedad, db
from services.consultas import (
    obtener_personas_disponibles,
    contar_guardias_mes,
    tiene_guardia_anterior,
    obtener_rango_mes
)


def generar_guardias_mes(mes, anio):
    """Genera las guardias para un mes completo"""
    inicio_mes, fin_mes = obtener_rango_mes(mes, anio)

    # Limpiar guardias existentes
    Guardia.query.filter(
        Guardia.fecha >= inicio_mes.date(),
        Guardia.fecha <= fin_mes.date()
    ).delete()
    db.session.commit()

    personas = Persona.query.filter_by(activo=True).all()
    if not personas:
        print(f"No hay personas activas")
        return False

    # Cargar acumulados
    acumulado_dict = {p.id: p.acumulado for p in personas}

    # Generar día por día
    fecha_actual = inicio_mes
    guardias_creadas = 0

    while fecha_actual <= fin_mes:
        disponibles = obtener_personas_disponibles(fecha_actual.date())

        if disponibles:
            # Calcular total y ordenar
            totales = {
                p.id: contar_guardias_mes(p.id, mes, anio) + acumulado_dict.get(p.id, 0)
                for p in disponibles
            }
            disponibles.sort(key=lambda p: totales.get(p.id, 0))

            # Intentar asignar (regla: no guardia consecutiva)
            asignado = False
            for p in disponibles:
                if not tiene_guardia_anterior(p.id, fecha_actual.date()):
                    guardia = Guardia(
                        fecha=fecha_actual.date(),
                        persona_id=p.id,
                        tipo='normal'
                    )
                    db.session.add(guardia)
                    asignado = True
                    guardias_creadas += 1
                    break

            # Si no se pudo, asignar cualquiera
            if not asignado and disponibles:
                guardia = Guardia(
                    fecha=fecha_actual.date(),
                    persona_id=disponibles[0].id,
                    tipo='suplencia'
                )
                db.session.add(guardia)
                guardias_creadas += 1

            db.session.commit()

        fecha_actual += timedelta(days=1)

    print(f"Guardias generadas para {mes}/{anio}: {guardias_creadas} días")
    calcular_acumulados(mes, anio)
    return True


def calcular_acumulados(mes, anio):
    """Calcula los acumulados después de generar un mes"""
    personas = Persona.query.filter_by(activo=True).all()
    if not personas:
        return

    total_guardias = sum(contar_guardias_mes(p.id, mes, anio) for p in personas)
    promedio = total_guardias / len(personas)

    for p in personas:
        guardias = contar_guardias_mes(p.id, mes, anio)
        diferencia = int(promedio - guardias)

        historico = HistoricoAcumulado.query.filter_by(
            persona_id=p.id, mes=mes, anio=anio
        ).first()
        if not historico:
            historico = HistoricoAcumulado(persona_id=p.id, mes=mes, anio=anio)

        historico.acumulado = diferencia
        db.session.add(historico)
        p.acumulado = diferencia

    db.session.commit()


def reasignar_guardia(fecha_str, persona_id_nuevo, motivo=''):
    """Reasigna una guardia específica a otra persona"""
    fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()

    guardia = Guardia.query.filter_by(fecha=fecha).first()
    if not guardia:
        return False, "No hay guardia asignada para esa fecha"

    persona_original_id = guardia.persona_id
    disponibles = obtener_personas_disponibles(fecha, exclude_id=persona_original_id)
    persona_nueva = Persona.query.get(persona_id_nuevo)

    if persona_nueva not in disponibles:
        tiene_novedad = Novedad.query.filter(
            Novedad.persona_id == persona_nueva.id,
            Novedad.fecha_inicio <= fecha,
            Novedad.fecha_fin >= fecha
        ).first()
        if tiene_novedad:
            return False, f"La persona {persona_nueva.nombre} tiene una novedad en esa fecha"

    guardia.persona_id = persona_id_nuevo
    guardia.es_suplencia = True
    guardia.persona_original_id = persona_original_id
    guardia.tipo = 'suplencia'

    db.session.commit()
    return True, "Guardia reasignada exitosamente"


def reasignar_guardia_random(fecha_str):
    """Reasigna una guardia aleatoriamente"""
    fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    guardia = Guardia.query.filter_by(fecha=fecha).first()

    if not guardia:
        return False, "No hay guardia para esa fecha", None, None

    persona_original_id = guardia.persona_id
    disponibles = obtener_personas_disponibles(fecha, exclude_id=persona_original_id)

    if not disponibles:
        return False, "No hay personas disponibles", None, None

    persona_nueva = random.choice(disponibles)
    exito, mensaje = reasignar_guardia(fecha_str, persona_nueva.id, 'Asignación random')

    persona_original = Persona.query.get(persona_original_id)
    return exito, mensaje, persona_original.nombre if persona_original else None, persona_nueva.nombre


def asignar_guardia_manual(fecha_str, persona_id):
    """Asigna manualmente una guardia en una fecha específica"""
    fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()

    guardia_existente = Guardia.query.filter_by(fecha=fecha).first()
    if guardia_existente:
        guardia_existente.persona_id = persona_id
        guardia_existente.tipo = 'manual'
    else:
        guardia = Guardia(fecha=fecha, persona_id=persona_id, tipo='manual')
        db.session.add(guardia)

    db.session.commit()
    return True, "Guardia asignada manualmente"


def importar_guardias_desde_lista(fecha_base, personas_nombres):
    """
    Importa guardias desde una lista de nombres
    fecha_base: datetime - primer día del mes
    personas_nombres: lista de nombres en orden de días (día 1, día 2, ...)
    """
    personas_dict = {p.nombre: p.id for p in Persona.query.all()}

    for i, nombre in enumerate(personas_nombres):
        fecha = fecha_base + timedelta(days=i)
        persona_id = personas_dict.get(nombre)

        if persona_id:
            guardia = Guardia.query.filter_by(fecha=fecha).first()
            if guardia:
                guardia.persona_id = persona_id
                guardia.tipo = 'importado'
            else:
                guardia = Guardia(fecha=fecha, persona_id=persona_id, tipo='importado')
                db.session.add(guardia)

    db.session.commit()
    return True
