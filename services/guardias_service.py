"""
Servicios de negocio - Lógica de guardias
"""
import random
from datetime import datetime, timedelta
from models.models import Guardia, Persona, HistoricoAcumulado, Novedad, db
from services.consultas import (
    obtener_personas_disponibles,
    contar_guardias_mes,
    obtener_guardias_mes,
    tiene_guardia_anterior,
    tiene_guardia_dia_medio,
    tiene_sipat_guardia_anterior,
    tuvo_sipat_guardia_en_rango,
    obtener_rango_mes
)


def generar_guardias_mes(mes, anio):
    """Genera las guardias para un mes completo con balanceo rotativo"""
    inicio_mes, fin_mes = obtener_rango_mes(mes, anio)

    # Limpiar guardias existentes de este mes
    Guardia.query.filter(
        Guardia.fecha >= inicio_mes.date(),
        Guardia.fecha <= fin_mes.date()
    ).delete()
    db.session.commit()

    personas = Persona.query.filter_by(activo=True).all()
    if not personas:
        return False

    # Reiniciar acumulados si es enero (inicio de año)
    if mes == 1:
        HistoricoAcumulado.query.filter_by(anio=anio).delete()
        for p in personas:
            p.acumulado = 0
        db.session.commit()

    num_personas = len(personas)
    num_dias = (fin_mes.date() - inicio_mes.date()).days + 1
    guardias_por_persona = num_dias // num_personas

    # Obtener guardias del mes anterior para rotación
    mes_anterior = mes - 1 if mes > 1 else 12
    anio_anterior = anio if mes > 1 else anio - 1
    guardias_mes_anterior_dict = {
        p.id: contar_guardias_mes(p.id, mes_anterior, anio_anterior) 
        for p in personas
    }

    # Cargar acumulados
    acumulado_dict = {p.id: p.acumulado or 0 for p in personas}

    # Guardias asignadas en este mes
    guardias_mes_dict = {p.id: 0 for p in personas}

    # Límites por persona
    limite_max_dict = {}
    for p in personas:
        limite = guardias_por_persona + 1
        if acumulado_dict.get(p.id, 0) < 0:
            limite = max(guardias_por_persona - 1, limite - 1)
        limite_max_dict[p.id] = min(limite, 3)

    navidad_persona_id = None
    fecha_actual = inicio_mes
    guardias_creadas = 0

    while fecha_actual <= fin_mes:
        disponibles = obtener_personas_disponibles(fecha_actual.date())

        if disponibles:
            # Filtrar candidatos
            candidatos = []
            for p in disponibles:
                guardias_mes = guardias_mes_dict.get(p.id, 0)
                if guardias_mes < limite_max_dict.get(p.id, 3):
                    candidatos.append(p)

            if not candidatos:
                candidatos = disponibles

            # Evitar repetir Navidad
            if fecha_actual.month == 12 and fecha_actual.day in (25, 31):
                candidatos = [p for p in candidatos 
                             if not (navidad_persona_id and p.id == navidad_persona_id)]

            # Calcular scores
            scores = []
            for p in candidatos:
                guardias_mes = guardias_mes_dict.get(p.id, 0)
                acumulado = acumulado_dict.get(p.id, 0)
                guardias_anterior = guardias_mes_anterior_dict.get(p.id, 0)

                score = (
                    guardias_mes * 100
                    - acumulado * 10
                    + guardias_anterior * 5
                    + (100 if tiene_guardia_anterior(p.id, fecha_actual.date()) else 0)
                )

                # Restricciones SIPAT - No consecutivos ni antes ni después
                if p.grado and 'SIPAT' in p.grado.upper():
                    if tiene_guardia_dia_medio(p.id, fecha_actual.date()):
                        score += 20
                    if tiene_guardia_anterior(p.id, fecha_actual.date()):
                        score += 500
                    # Si algún SIPAT tuvo guardia ayer, evitar que otro SIPAT tenga hoy
                    if tiene_sipat_guardia_anterior(fecha_actual.date()):
                        score += 1000
                    # Si algún SIPAT tiene guardia hoy, evitar que otro SIPAT tenga mañana
                    # (esto se aplica cuando se asigna la guardia del día siguiente)

                if guardias_mes >= 3:
                    score += 10000

                scores.append((p, score))

            scores.sort(key=lambda x: x[1])
            persona_elegida = scores[0][0]

            if fecha_actual.month == 12 and fecha_actual.day == 24:
                navidad_persona_id = persona_elegida.id

            guardia = Guardia(
                fecha=fecha_actual.date(),
                persona_id=persona_elegida.id,
                tipo='normal'
            )
            db.session.add(guardia)
            guardias_mes_dict[persona_elegida.id] = guardias_mes_dict.get(persona_elegida.id, 0) + 1
            guardias_creadas += 1
            db.session.commit()

        fecha_actual += timedelta(days=1)

    print(f"Guardias generadas para {mes}/{anio}: {guardias_creadas} días")
    calcular_acumulados(mes, anio)
    _imprimir_balanceo(personas, guardias_mes_dict, mes, anio)

    return True


def calcular_retenes_por_mes(mes, anio):
    """Calcula el retén de cada fecha y retorna contador por persona"""
    guardias = obtener_guardias_mes(mes, anio)
    personas_activas = Persona.query.filter_by(activo=True).all()
    reten_contador = {p.id: 0 for p in personas_activas}
    reten_fechas_dict = {}
    sipat_reten_fechas = set()  # fechas donde un SIPAT fue reten

    sipat_guardia_fechas = {}
    for g in guardias:
        persona = Persona.query.get(g.persona_id)
        if persona and persona.grado and 'SIPAT' in persona.grado.upper():
            sipat_guardia_fechas.setdefault(g.persona_id, set()).add(g.fecha)

    todas_sipat_guardia_fechas = set()
    for fechas in sipat_guardia_fechas.values():
        todas_sipat_guardia_fechas.update(fechas)

    reten_por_fecha = {}

    for g in guardias:
        disponibles = obtener_personas_disponibles(g.fecha, exclude_id=g.persona_id)
        reten_id = None

        if disponibles:
            dia_anterior = g.fecha - timedelta(days=1)
            dia_siguiente = g.fecha + timedelta(days=1)

            persona = Persona.query.get(g.persona_id)
            es_guardia_sipat = persona and persona.grado and 'SIPAT' in persona.grado.upper()

            hubo_sipat_reten_ayer = dia_anterior in sipat_reten_fechas
            dia_hace_2 = g.fecha - timedelta(days=2)
            hubo_sipat_reten_hace_2 = dia_hace_2 in sipat_reten_fechas

            hay_sipat_guardia_hoy = g.fecha in todas_sipat_guardia_fechas
            hay_sipat_guardia_ayer = dia_anterior in todas_sipat_guardia_fechas
            hay_sipat_guardia_manana = dia_siguiente in todas_sipat_guardia_fechas

            candidatos = []
            for p in disponibles:
                fue_reten_anterior = reten_fechas_dict.get((p.id, dia_anterior), False)
                fue_reten_siguiente = reten_fechas_dict.get((p.id, dia_siguiente), False)

                es_reten_sipat = p.grado and p.grado.upper().find('SIPAT') >= 0
                if es_guardia_sipat and es_reten_sipat:
                    continue
                if hubo_sipat_reten_ayer and es_reten_sipat:
                    continue
                if hubo_sipat_reten_hace_2 and es_reten_sipat:
                    continue
                if es_reten_sipat and (hay_sipat_guardia_hoy or hay_sipat_guardia_ayer or hay_sipat_guardia_manana):
                    continue
                if p.id in sipat_guardia_fechas and dia_siguiente in sipat_guardia_fechas[p.id]:
                    continue
                if p.id in sipat_guardia_fechas and dia_anterior in sipat_guardia_fechas[p.id]:
                    continue

                if not fue_reten_anterior and not fue_reten_siguiente:
                    candidatos.append(p)

            if not candidatos:
                candidatos = disponibles

            # prioritizar SIPAT que aún no han alcanzado 2 retenes
            sipat_ids = [p.id for p in disponibles if p.grado and 'SIPAT' in p.grado.upper()]
            sipat_necesitan = [p for p in candidatos if p.id in sipat_ids and reten_contador.get(p.id, 0) < 2]
            if sipat_necesitan:
                candidatos = sipat_necesitan

            candidatos.sort(key=lambda p: reten_contador.get(p.id, 0))
            persona_reten = candidatos[0]
            reten_id = persona_reten.id

            es_reten_sipat = persona_reten.grado and 'SIPAT' in persona_reten.grado.upper()
            reten_fechas_dict[(persona_reten.id, g.fecha)] = True
            reten_contador[persona_reten.id] = reten_contador.get(persona_reten.id, 0) + 1
            if es_reten_sipat:
                sipat_reten_fechas.add(g.fecha)

        reten_por_fecha[g.fecha] = reten_id

    return reten_por_fecha, reten_contador


def _imprimir_balanceo(personas, guardias_mes_dict, mes, anio):
    """Imprime estadísticas de balanceo de guardias"""
    print(f"\n=== Balanceo de Guardias {mes}/{anio} ===")

    stats = []
    for p in personas:
        guardias_mes = guardias_mes_dict.get(p.id, 0)
        stats.append((p.nombre, guardias_mes, p.acumulado or 0))

    stats.sort(key=lambda x: x[1], reverse=True)

    print(f"{'Persona':<25} {'Este Mes':<10} {'Acumulado':<10}")
    print("-" * 50)
    for nombre, actual, acum in stats:
        print(f"{nombre:<25} {actual:<10} {acum:<10}")

    if stats:
        guardias_list = [s[1] for s in stats]
        promedio = sum(guardias_list) / len(guardias_list)
        print(f"\nPromedio: {promedio:.1f}")
        print(f"Máximo: {max(guardias_list)}, Mínimo: {min(guardias_list)}")
        
        acumulados = [s[2] for s in stats]
        print(f"\nRango acumulados: {min(acumulados)} a {max(acumulados)}")
    print("=" * 50)


def _normalizar_acumulados(acumulados_dict):
    """Normaliza acumulados a valores [-2, -1, 0, 1, 2]
    
    - +2: Máxima prioridad (hizo mucho menos guardias)
    - +1: Más prioridad (hizo menos guardias)
    - 0: Balanceado
    - -1: Menos prioridad (hizo más guardias)
    - -2: Mínima prioridad (hizo mucho más guardias)
    """
    if not acumulados_dict:
        return {}

    valores = list(acumulados_dict.values())
    media = sum(valores) / len(valores)

    normalizados = {}
    for pid, val in acumulados_dict.items():
        centrado = val - media
        
        if centrado < -1.5:
            normalizados[pid] = -2
        elif centrado < -0.5:
            normalizados[pid] = -1
        elif centrado < 0.5:
            normalizados[pid] = 0
        elif centrado < 1.5:
            normalizados[pid] = 1
        else:
            normalizados[pid] = 2

    return normalizados


def calcular_acumulados(mes, anio):
    """Calcula los acumulados después de generar/modificar un mes"""
    personas = Persona.query.filter_by(activo=True).all()
    if not personas:
        return

    # Incluir retén en el cálculo de carga total (guardias + retenes)
    _, retenes_por_fecha = calcular_retenes_por_mes(mes, anio)

    total_tareas = sum(
        contar_guardias_mes(p.id, mes, anio) + retenes_por_fecha.get(p.id, 0)
        for p in personas
    )
    promedio = total_tareas / len(personas)

    acumulados_temp = {}
    for p in personas:
        guardias = contar_guardias_mes(p.id, mes, anio)
        retenes = retenes_por_fecha.get(p.id, 0)
        tareas_totales = guardias + retenes
        diferencia = promedio - tareas_totales

        # Histórico de meses anteriores
        historicos = HistoricoAcumulado.query.filter(
            HistoricoAcumulado.persona_id == p.id,
            (HistoricoAcumulado.mes != mes) | (HistoricoAcumulado.anio != anio)
        ).all()
        acumulado_historico = sum(h.acumulado for h in historicos)

        acumulados_temp[p.id] = acumulado_historico + diferencia

        # Actualizar histórico del mes
        historico = HistoricoAcumulado.query.filter_by(
            persona_id=p.id, mes=mes, anio=anio
        ).first()
        if not historico:
            historico = HistoricoAcumulado(persona_id=p.id, mes=mes, anio=anio)

        historico.acumulado = round(diferencia)
        db.session.add(historico)

    # Normalizar y aplicar
    acumulados_normalizados = _normalizar_acumulados(acumulados_temp)
    for p in personas:
        p.acumulado = acumulados_normalizados.get(p.id, 0)

    db.session.commit()

    # Imprimir resumen
    print(f"\n=== Acumulados {mes}/{anio} ===")
    print(f"{'Persona':<25} {'Guardias':<10} {'Retenes':<10} {'Tareas':<10} {'Diferencia':<12} {'Acumulado':<10}")
    print("-" * 80)
    for p in personas:
        guardias = contar_guardias_mes(p.id, mes, anio)
        retenes = calcular_retenes_por_mes(mes, anio)[1].get(p.id, 0)
        tareas = guardias + retenes
        diferencia = promedio - tareas
        print(f"{p.nombre:<25} {guardias:<10} {retenes:<10} {tareas:<10} {diferencia:<12.2f} {p.acumulado:<10}")
    print("=" * 80)


def reasignar_guardia(fecha_str, persona_id_nuevo, motivo=''):
    """Reasigna una guardia específica a otra persona"""
    fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()

    guardia = Guardia.query.filter_by(fecha=fecha).first()
    if not guardia:
        return False, "No hay guardia asignada para esa fecha"

    persona_original_id = guardia.persona_id
    persona_nueva = Persona.query.get(persona_id_nuevo)

    # Verificar novedades
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
    calcular_acumulados(fecha.month, fecha.year)
    
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

    # Filtrar por restricciones SIPAT
    candidatos = []
    for p in disponibles:
        if p.grado and 'SIPAT' in p.grado.upper():
            if tiene_guardia_dia_medio(p.id, fecha) or tiene_guardia_anterior(p.id, fecha):
                continue
            # Si algún SIPAT tuvo guardia el día anterior, evitar que este SIPAT tenga hoy
            if tiene_sipat_guardia_anterior(fecha):
                continue
        candidatos.append(p)

    if not candidatos:
        candidatos = disponibles

    # Seleccionar aleatorio entre los con menos guardias
    mes, anio = fecha.month, fecha.year
    scores = [(p, contar_guardias_mes(p.id, mes, anio) * 100) for p in candidatos]
    min_score = min(score for _, score in scores)
    mejores = [p for p, score in scores if score == min_score]
    persona_nueva = random.choice(mejores)

    exito, mensaje = reasignar_guardia(fecha_str, persona_nueva.id, 'Random')

    if exito:
        calcular_acumulados(mes, anio)

    persona_original = Persona.query.get(persona_original_id)
    return exito, mensaje, persona_original.nombre if persona_original else None, persona_nueva.nombre


def asignar_guardia_manual(fecha_str, persona_id):
    """Asigna manualmente una guardia en una fecha específica"""
    fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()

    guardia = Guardia.query.filter_by(fecha=fecha).first()
    if guardia:
        guardia.persona_id = persona_id
        guardia.tipo = 'manual'
    else:
        guardia = Guardia(fecha=fecha, persona_id=persona_id, tipo='manual')
        db.session.add(guardia)

    db.session.commit()
    calcular_acumulados(fecha.month, fecha.year)

    return True, "Guardia asignada manualmente"


def resetear_acumulados():
    """Resetea todos los acumulados a cero"""
    personas = Persona.query.filter_by(activo=True).all()
    for p in personas:
        p.acumulado = 0
    HistoricoAcumulado.query.delete()
    db.session.commit()


def eliminar_acumulados_mes(mes, anio):
    """Resta los acumulados de un mes específico del total de cada persona"""
    personas = Persona.query.filter_by(activo=True).all()

    acumulados_mes = {
        h.persona_id: h.acumulado
        for h in HistoricoAcumulado.query.filter_by(mes=mes, anio=anio).all()
    }

    for p in personas:
        acumulado_mes = acumulados_mes.get(p.id, 0)
        p.acumulado = (p.acumulado or 0) - acumulado_mes

    db.session.commit()


def asignar_guardia_manual(fecha_str, persona_id):
    """Asigna manualmente una guardia en una fecha específica"""
    fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()

    # Verificar si ya existe una guardia en esa fecha
    guardia_existente = Guardia.query.filter_by(fecha=fecha).first()
    if guardia_existente:
        return False, "Ya existe una guardia asignada para esa fecha"

    persona = Persona.query.get(persona_id)
    if not persona:
        return False, "Persona no encontrada"

    if not persona.activo:
        return False, "La persona no está activa"

    # Verificar novedades
    tiene_novedad = Novedad.query.filter(
        Novedad.persona_id == persona.id,
        Novedad.fecha_inicio <= fecha,
        Novedad.fecha_fin >= fecha
    ).first()
    
    if tiene_novedad:
        return False, f"La persona {persona.nombre} tiene una novedad en esa fecha"

    guardia = Guardia(
        fecha=fecha,
        persona_id=persona_id,
        tipo='manual'
    )
    db.session.add(guardia)
    db.session.commit()
    
    calcular_acumulados(fecha.month, fecha.year)
    
    return True, "Guardia asignada exitosamente"
