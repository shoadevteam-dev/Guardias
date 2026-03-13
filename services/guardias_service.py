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
    tiene_guardia_dia_medio,
    tiene_sipat_guardia_anterior,
    obtener_rango_mes
)


def generar_guardias_mes(mes, anio):
    """Genera las guardias para un mes completo con balanceo rotativo anual

    El algoritmo hace balanceo considerando:
    1. El acumulado histórico de cada persona (todo el año)
    2. Quien tiene acumulado NEGATIVO (hizo más guardias) → tiene MENOS prioridad
    3. Quien tiene acumulado POSITIVO (hizo menos guardias) → tiene MÁS prioridad
    4. También considera las guardias del mes anterior para rotación inmediata
    5. Personas SIPAT (Campillay, Fortunato, Rivas) no deben tener día por medio
       pero esta restricción se relaja si causa desbalanceo extremo
    """
    inicio_mes, fin_mes = obtener_rango_mes(mes, anio)

    # Limpiar guardias existentes de este mes
    Guardia.query.filter(
        Guardia.fecha >= inicio_mes.date(),
        Guardia.fecha <= fin_mes.date()
    ).delete()
    db.session.commit()

    personas = Persona.query.filter_by(activo=True).all()
    if not personas:
        print(f"No hay personas activas")
        return False

    num_personas = len(personas)
    num_dias = (fin_mes.date() - inicio_mes.date()).days + 1
    guardias_por_persona = num_dias // num_personas
    guardias_extra = num_dias % num_personas

    # Identificar personas SIPAT
    personas_sipat = [p for p in personas if p.grado and 'SIPAT' in p.grado.upper()]
    ids_sipat = {p.id for p in personas_sipat}

    # Obtener guardias del mes ANTERIOR para rotación inmediata
    mes_anterior = mes - 1 if mes > 1 else 12
    anio_anterior = anio if mes > 1 else anio - 1

    guardias_mes_anterior_dict = {}
    for p in personas:
        guardias_mes_anterior_dict[p.id] = contar_guardias_mes(p.id, mes_anterior, anio_anterior)

    # Cargar acumulados históricos (todo el año)
    acumulado_dict = {p.id: p.acumulado or 0 for p in personas}

    # Contador de guardias asignadas en este mes (por persona)
    guardias_mes_dict = {p.id: 0 for p in personas}

    # Calcular límite máximo de guardias para cada persona este mes
    # Estrategia: mantener todos entre 2-3 guardias (guardias_por_persona ± 1)
    limite_max_dict = {}
    limite_min_dict = {}
    for p in personas:
        acumulado = acumulado_dict.get(p.id, 0)
        guardias_anterior = guardias_mes_anterior_dict.get(p.id, 0)

        # Límite base: todos entre (promedio - 1) y (promedio + 1)
        limite_min = max(0, guardias_por_persona - 1)
        limite_max = guardias_por_persona + 1

        # Ajustes suaves por acumulado histórico
        if acumulado < 0:
            limite_max = max(limite_min, limite_max - 1)
        elif acumulado > 0:
            limite_min = max(0, limite_min - 1)  # Puede tener un poco menos

        # Ajustes por mes anterior
        if guardias_anterior > guardias_por_persona:
            limite_max = max(limite_min, limite_max - 1)
        elif guardias_anterior < guardias_por_persona:
            limite_min = max(0, limite_min - 1)

        limite_max_dict[p.id] = limite_max
        limite_min_dict[p.id] = limite_min

    # Generar día por día
    fecha_actual = inicio_mes
    guardias_creadas = 0

    while fecha_actual <= fin_mes:
        disponibles = obtener_personas_disponibles(fecha_actual.date())

        if disponibles:
            # Calcular días restantes en el mes
            dias_restantes = (fin_mes.date() - fecha_actual.date()).days + 1
            
            # Calcular promedio de guardias que se necesitan por día restante
            guardias_faltantes = num_dias - guardias_creadas
            personas_necesarias = min(len(personas), dias_restantes)
            
            # Filtrar personas que ya alcanzaron su límite máximo
            # Pero si alguien tiene menos del mínimo, priorizarlo
            candidatos = []
            prioritarios = []
            
            for p in disponibles:
                guardias_mes = guardias_mes_dict.get(p.id, 0)
                limite_max = limite_max_dict.get(p.id, guardias_por_persona + 1)
                limite_min = limite_min_dict.get(p.id, guardias_por_persona - 1)
                
                if guardias_mes < limite_min:
                    # Prioritario: tiene menos del mínimo
                    prioritarios.append(p)
                elif guardias_mes < limite_max:
                    # Candidato normal: no alcanzó el máximo
                    candidatos.append(p)
            
            # Si hay prioritarios, usarlos primero
            if prioritarios:
                candidatos = prioritarios
            
            # Si no hay candidatos (todos alcanzaron límite), usar todos los disponibles
            if not candidatos:
                candidatos = disponibles

            # Calcular score para cada candidato
            # PRIORIDAD: quien tiene MÁS acumulado positivo (hizo menos en el año) tiene MÁS prioridad
            scores = []
            for p in candidatos:
                guardias_mes = guardias_mes_dict.get(p.id, 0)
                guardias_anterior = guardias_mes_anterior_dict.get(p.id, 0)
                acumulado = acumulado_dict.get(p.id, 0)
                limite_min = limite_min_dict.get(p.id, guardias_por_persona - 1)
                limite_max = limite_max_dict.get(p.id, guardias_por_persona + 1)

                # Penalización por guardia consecutiva (muy alta para todos)
                tiene_consecutiva = 100 if tiene_guardia_anterior(p.id, fecha_actual.date()) else 0

                # Penalización por día por medio para personas SIPAT
                # Campillay, Fortunato y Rivas no deben tener turnos separados por un día
                # PERO: esta restricción se relaja para mantener balanceo 2-3 guardias
                tiene_dia_medio = 0
                if p.grado and 'SIPAT' in p.grado.upper():
                    # Penalización suave (20) para preferir evitar día por medio
                    # pero permitirlo si es necesario para mantener balanceo
                    tiene_dia_medio = 20 if tiene_guardia_dia_medio(p.id, fecha_actual.date()) else 0

                # Penalización EXTRA para SIPAT por día consecutivo (aún más estricta)
                # Esto asegura que SIPAT nunca tenga guardias consecutivas
                sipat_consecutiva = 0
                if p.grado and 'SIPAT' in p.grado.upper():
                    sipat_consecutiva = 500 if tiene_guardia_anterior(p.id, fecha_actual.date()) else 0

                # Penalización para SIPAT si OTRO SIPAT tuvo guardia ayer
                # Esto evita que SIPAT tengan guardias consecutivas entre ellos
                # (ej: Fortunato Viernes, Campillay Sábado, Rivas Domingo)
                sipat_consecutivo_grupo = 0
                if p.grado and 'SIPAT' in p.grado.upper():
                    sipat_consecutivo_grupo = 1000 if tiene_sipat_guardia_anterior(fecha_actual.date()) else 0

                # Score: menor es mejor
                # Factores (en orden de importancia):
                # 1. Guardias en el mes actual (balanceo dentro del mes)
                # 2. Acumulado histórico (quien hizo menos en el año tiene prioridad)
                # 3. Guardias mes anterior (rotación mes a mes)
                # 4. Restricción SIPAT (no día por medio) - penalización reducida
                # 5. Restricción SIPAT (no días consecutivos) - penalización muy alta
                # 6. Restricción SIPAT (no consecutivos entre SIPAT) - penalización máxima
                score = (guardias_mes * 100) - (acumulado * 10) + (guardias_anterior * 5) + tiene_consecutiva + tiene_dia_medio + sipat_consecutiva + sipat_consecutivo_grupo
                scores.append((p, score))

            # Ordenar por score (menor primero = más prioridad)
            scores.sort(key=lambda x: x[1])

            # Elegir al primero (menor score = más prioridad)
            persona_elegida = scores[0][0]
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

    # Calcular acumulados primero (con normalización)
    calcular_acumulados(mes, anio)

    # Imprimir estadísticas de balanceo (con acumulados ya normalizados)
    _imprimir_balanceo_anual(personas, guardias_mes_dict, guardias_mes_anterior_dict, acumulado_dict, mes, anio)

    return True


def _imprimir_balanceo_anual(personas, guardias_mes_dict, guardias_mes_anterior_dict, acumulado_dict, mes, anio):
    """Imprime estadísticas de balanceo anual de guardias
    
    Nota: Los acumulados se leen directamente de la persona (ya normalizados),
    no del acumulado_dict que contiene valores sin normalizar.
    """
    print(f"\n=== Balanceo Anual de Guardias {mes}/{anio} ===")

    stats = []
    for p in personas:
        guardias_mes_actual = guardias_mes_dict.get(p.id, 0)
        guardias_mes_anterior = guardias_mes_anterior_dict.get(p.id, 0)
        # Usar el acumulado normalizado de la base de datos
        acumulado_normalizado = p.acumulado or 0
        stats.append((p.nombre, guardias_mes_anterior, guardias_mes_actual, acumulado_normalizado))

    # Ordenar por guardias del mes actual
    stats.sort(key=lambda x: x[2], reverse=True)

    print(f"{'Persona':<25} {'Mes Ant.':<10} {'Este Mes':<10} {'Acum Normalizado':<18}")
    print("-" * 75)
    for nombre, anterior, actual, acum_norm in stats:
        print(f"{nombre:<25} {anterior:<10} {actual:<10} {acum_norm:<18.2f}")

    # Calcular estadísticas
    if stats:
        guardias_actual_list = [s[2] for s in stats]
        promedio = sum(guardias_actual_list) / len(guardias_actual_list)
        max_g = max(guardias_actual_list)
        min_g = min(guardias_actual_list)
        diferencia = max_g - min_g

        print(f"\nPromedio guardias/mes: {promedio:.1f}")
        print(f"Máximo: {max_g}, Mínimo: {min_g}")
        print(f"Diferencia máx-mín: {diferencia} guardias")

        # Verificar balanceo anual con acumulados normalizados
        print("\n=== Análisis de Balanceo ===")
        acumulados = [s[3] for s in stats]
        max_acum = max(acumulados)
        min_acum = min(acumulados)
        print(f"Rango de acumulados normalizados: {min_acum:.2f} a {max_acum:.2f}")
        
        # Verificar que los acumulados estén dentro del rango [-1, 1]
        if max_acum <= 1 and abs(min_acum) <= 1:
            print("✓ Balanceo anual: EXCELENTE (acumulados en rango [-1, 1])")
        elif max_acum - min_acum <= 3:
            print("✓ Balanceo anual: BUENO")
        else:
            print("⚠ Balanceo anual: REGULAR (se irá corrigiendo en meses siguientes)")
    print("=" * 75)


def _normalizar_acumulados(acumulados_dict):
    """Normaliza los acumulados para mantenerlos en valores discretos [-1, 0, 1] con media 0
    
    Estrategia:
    1. Calcular la media y restarla para centrar en 0
    2. Redondear al entero más cercano y clamp a [-1, 0, 1]
    
    Significado del acumulado:
    - +1: Hizo menos guardias → tiene MÁS prioridad para el próximo mes
    - 0: Guardias balanceadas
    - -1: Hizo más guardias → tiene MENOS prioridad para el próximo mes
    """
    if not acumulados_dict:
        return {}
    
    valores = list(acumulados_dict.values())
    n = len(valores)
    
    # Paso 1: Centrar en 0 (restar la media)
    media = sum(valores) / n
    centrados = {pid: val - media for pid, val in acumulados_dict.items()}
    
    # Paso 2: Redondear al entero más cercano y clamp a -1, 0, 1
    normalizados = {}
    for pid, val in centrados.items():
        rounded = round(val)
        clamped = max(-1, min(1, rounded))
        normalizados[pid] = clamped
    
    return normalizados


def obtener_festivos_chile(mes, anio, bonus_personalizados=None):
    """Obtiene los festivos de Chile para un mes y año específicos con bonus opcionales
    
    Args:
        mes: Mes (1-12)
        anio: Año
        bonus_personalizados: Diccionario opcional {fecha: bonus} para personalizar bonus
    
    Returns:
        Lista de tuplas: [(fecha, bonus), ...]
        Por defecto, todos los festivos tienen bonus=1, pero se puede personalizar
    
    Festivos fijos:
    - 1 Enero: Año Nuevo
    - 1 Mayo: Día del Trabajo
    - 21 Mayo: Día de las Glorias Navales
    - 29 Junio: San Pedro y San Pablo (se mueve al lunes más cercano)
    - 16 Julio: Día de la Virgen del Carmen (desde 2024)
    - 15 Agosto: Asunción de la Virgen
    - 18 Septiembre: Independencia Nacional
    - 19 Septiembre: Día de las Glorias del Ejército
    - 12 Octubre: Descubrimiento de Dos Mundos (se mueve al lunes más cercano)
    - 1 Noviembre: Día de Todos los Santos
    - 8 Diciembre: Inmaculada Concepción
    - 25 Diciembre: Navidad
    
    Festivos variables (se calculan aparte):
    - Viernes Santo (marzo/abril)
    - Sábado Santo (marzo/abril)
    """
    from datetime import date, timedelta
    
    if bonus_personalizados is None:
        bonus_personalizados = {}
    
    festivos = []
    
    # Festivos fijos por mes (todos con bonus=1 por defecto)
    festivos_fijos = {
        1: [1],      # Año Nuevo
        5: [1, 21],  # Día del Trabajo, Glorias Navales
        8: [15],     # Asunción de la Virgen
        9: [18, 19], # Fiestas Patrias
        11: [1],     # Todos los Santos
        12: [8, 25], # Inmaculada Concepción, Navidad
    }
    
    # Festivos que se mueven al lunes más cercano
    festivos_lunes = {
        6: 29,  # San Pedro y San Pablo
        10: 12, # Descubrimiento de Dos Mundos
    }
    
    # Agregar festivos fijos del mes
    if mes in festivos_fijos:
        for dia in festivos_fijos[mes]:
            fecha = date(anio, mes, dia)
            bonus = bonus_personalizados.get(fecha, 1)  # Bonus por defecto = 1
            festivos.append((fecha, bonus))
    
    # Agregar festivos que se mueven al lunes
    if mes in festivos_lunes:
        dia = festivos_lunes[mes]
        fecha_original = date(anio, mes, dia)
        # Mover al lunes más cercano
        if fecha_original.weekday() == 0:  # Lunes
            fecha = fecha_original
        elif fecha_original.weekday() == 1:  # Martes
            fecha = fecha_original - timedelta(days=1)
        elif fecha_original.weekday() == 2:  # Miércoles
            fecha = fecha_original - timedelta(days=2)
        elif fecha_original.weekday() == 3:  # Jueves
            fecha = fecha_original - timedelta(days=3)
        elif fecha_original.weekday() == 4:  # Viernes
            fecha = fecha_original + timedelta(days=3)  # Lunes siguiente
        elif fecha_original.weekday() == 5:  # Sábado
            fecha = fecha_original + timedelta(days=2)  # Lunes siguiente
        elif fecha_original.weekday() == 6:  # Domingo
            fecha = fecha_original + timedelta(days=1)  # Lunes siguiente
        
        bonus = bonus_personalizados.get(fecha, 1)
        festivos.append((fecha, bonus))
    
    # Viernes Santo y Sábado Santo (cálculo basado en la fecha de Pascua)
    a = anio % 19
    b = anio % 4
    c = anio % 7
    k = anio // 100
    p = (8 + k) // 25
    q = k - p + 1
    m = (15 - p + 3 * k) % 30
    n = (4 + k - q) % 7
    d = (19 * a + m) % 30
    e = (2 * b + 4 * c + 6 * d + n) % 7
    
    # Fecha de Pascua (Domingo de Resurrección)
    if d + e <= 9:
        dia_pascua = 22 + d + e
        mes_pascua = 3  # Marzo
    elif d == 29 and e == 6:
        dia_pascua = 19
        mes_pascua = 4  # Abril
    elif d == 28 and e == 6 and (11 * m + 11) % 30 < 19:
        dia_pascua = 18
        mes_pascua = 4  # Abril
    else:
        dia_pascua = d + e - 9
        mes_pascua = 4  # Abril
    
    # Viernes Santo = 2 días antes del Domingo de Pascua
    # Sábado Santo = 1 día antes del Domingo de Pascua
    if mes_pascua == mes or (mes_pascua == 4 and mes == 3):
        if mes_pascua == 4:
            fecha_viernes_santo = date(anio, 4, dia_pascua) - timedelta(days=2)
            fecha_sabado_santo = date(anio, 4, dia_pascua) - timedelta(days=1)
        else:
            fecha_viernes_santo = date(anio, 3, dia_pascua) - timedelta(days=2)
            fecha_sabado_santo = date(anio, 3, dia_pascua) - timedelta(days=1)
        
        if fecha_viernes_santo.month == mes:
            bonus = bonus_personalizados.get(fecha_viernes_santo, 2)  # Bonus especial para Viernes Santo
            festivos.append((fecha_viernes_santo, bonus))
        if fecha_sabado_santo.month == mes:
            bonus = bonus_personalizados.get(fecha_sabado_santo, 1)
            festivos.append((fecha_sabado_santo, bonus))
    
    # 16 Julio - Día de la Virgen del Carmen (desde 2024)
    if mes == 7 and anio >= 2024:
        fecha = date(anio, 7, 16)
        bonus = bonus_personalizados.get(fecha, 1)
        festivos.append((fecha, bonus))
    
    return festivos


def _imprimir_balanceo_rotativo(personas, guardias_mes_dict, guardias_mes_anterior_dict, acumulado_dict, mes, anio):
    """Función legacy - redirige a la nueva función"""
    _imprimir_balanceo_anual(personas, guardias_mes_dict, guardias_mes_anterior_dict, acumulado_dict, mes, anio)


def _imprimir_balanceo(personas, guardias_mes_dict, acumulado_dict, mes, anio):
    """Función legacy - redirige a la nueva función"""
    _imprimir_balanceo_anual(personas, guardias_mes_dict, {}, acumulado_dict, mes, anio)


def calcular_acumulados(mes, anio):
    """Calcula los acumulados después de generar un mes

    El acumulado representa el desbalance:
    - POSITIVO = hizo MENOS guardias que el promedio (tiene prioridad para el próximo mes)
    - NEGATIVO = hizo MÁS guardias que el promedio (tiene menos prioridad para el próximo mes)

    El acumulado se normaliza para mantenerse en rango [-2, 2] con media 0.
    """
    personas = Persona.query.filter_by(activo=True).all()
    if not personas:
        return

    total_guardias = sum(contar_guardias_mes(p.id, mes, anio) for p in personas)
    promedio = total_guardias / len(personas)

    # Primero calcular los nuevos acumulados
    acumulados_temp = {}
    for p in personas:
        guardias = contar_guardias_mes(p.id, mes, anio)

        # Diferencia = promedio - guardias_hechas
        # Si hizo MÁS que el promedio → diferencia NEGATIVA (menos prioridad)
        # Si hizo MENOS que el promedio → diferencia POSITIVA (más prioridad)
        diferencia = round(promedio - guardias)

        # Sumar al acumulado existente (acumulativo histórico)
        acumulado_anterior = p.acumulado or 0
        acumulados_temp[p.id] = acumulado_anterior + diferencia

        historico = HistoricoAcumulado.query.filter_by(
            persona_id=p.id, mes=mes, anio=anio
        ).first()
        if not historico:
            historico = HistoricoAcumulado(persona_id=p.id, mes=mes, anio=anio)

        historico.acumulado = diferencia
        db.session.add(historico)

    # Normalizar acumulados para que estén en rango [-1, 0, 1] y media 0
    acumulados_normalizados = _normalizar_acumulados(acumulados_temp)

    # Aplicar acumulados normalizados
    for p in personas:
        p.acumulado = acumulados_normalizados.get(p.id, 0)

    db.session.commit()
    
    # Imprimir resumen de acumulados
    print(f"\n=== Acumulados calculados para {mes}/{anio} ===")
    print(f"{'Persona':<25} {'Guardias':<10} {'Promedio':<10} {'Diferencia':<12} {'Nuevo Acum':<10}")
    print("-" * 70)
    for p in personas:
        guardias = contar_guardias_mes(p.id, mes, anio)
        diferencia = round(promedio - guardias)
        acumulado = p.acumulado or 0
        print(f"{p.nombre:<25} {guardias:<10} {promedio:<10.1f} {diferencia:<12} {acumulado:<10.2f}")
    print("=" * 70)


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

    # Recalcular acumulados para mantener el balanceo
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

    persona_nueva = random.choice(disponibles)
    exito, mensaje = reasignar_guardia(fecha_str, persona_nueva.id, 'Asignación random')

    # Regenerar el mes completo para rebalancear después de la reasignación
    if exito:
        generar_guardias_mes(fecha.month, fecha.year)

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

    # Recalcular acumulados para mantener el balanceo
    calcular_acumulados(fecha.month, fecha.year)

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


def resetear_acumulados():
    """Resetea todos los acumulados a cero"""
    personas = Persona.query.filter_by(activo=True).all()
    for p in personas:
        p.acumulado = 0
    
    # Eliminar histórico de acumulados
    HistoricoAcumulado.query.delete()
    
    db.session.commit()
    print("Acumulados reseteados a cero")


def eliminar_acumulados_mes(mes, anio):
    """
    Resta los acumulados de un mes específico del total de cada persona.
    
    El acumulado en Persona es la suma de todos los acumulados históricos.
    Al eliminar un mes, restamos el acumulado de ese mes del total.
    
    Nota: Esta función NO elimina el registro histórico, solo resta los valores.
    La eliminación del histórico la hace la ruta que llama a esta función.
    """
    personas = Persona.query.filter_by(activo=True).all()
    
    # Obtener los acumulados del mes que se está eliminando
    acumulados_mes = {
        h.persona_id: h.acumulado 
        for h in HistoricoAcumulado.query.filter_by(mes=mes, anio=anio).all()
    }
    
    # Restar el acumulado de ese mes del total de cada persona
    for p in personas:
        acumulado_mes = acumulados_mes.get(p.id, 0)
        p.acumulado = (p.acumulado or 0) - acumulado_mes
