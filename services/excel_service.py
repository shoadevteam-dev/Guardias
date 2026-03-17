"""
Servicio de exportación a Excel
"""
import io
from datetime import timedelta
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from models.models import Guardia, Persona
from services.consultas import (
    obtener_rango_mes,
    obtener_personas_disponibles,
    obtener_guardias_mes
)


def exportar_guardias_excel(mes, anio):
    """Exporta las guardias del mes a un archivo Excel"""
    wb = Workbook()
    ws = wb.active
    ws.title = f"Guardias {mes}-{anio}"

    # Estilos
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    center_alignment = Alignment(horizontal='center', vertical='center')

    inicio_mes, fin_mes = obtener_rango_mes(mes, anio)

    # Obtener guardias
    guardias = obtener_guardias_mes(mes, anio)
    guardias_dict = {g.fecha: g for g in guardias}

    # Nombres
    nombres_meses = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
        7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }
    # weekday() de Python: 0=Lunes, 1=Martes, ..., 6=Domingo
    nombres_dias = {
        0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves',
        4: 'Viernes', 5: 'Sábado', 6: 'Domingo'
    }

    # Encabezados
    headers = ['Fecha', 'Día', 'Mes', 'Informático de Guardia', 'Retén']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_alignment
        cell.border = border

    # Datos
    personas_activas = Persona.query.filter_by(activo=True).all()
    reten_contador = {p.id: 0 for p in personas_activas}
    
    # Tracking de retén para evitar consecutivos
    reten_fechas_dict = {}
    
    # Tracking adicional para SIPAT: si un SIPAT fue retén ayer, ningún SIPAT puede ser retén hoy
    sipat_reten_fechas = set()  # Fechas donde un SIPAT fue retén
    
    # Tracking de fechas donde los SIPAT tienen guardia (para evitar que sean retenes el día anterior)
    sipat_guardia_fechas = {}  # {persona_id: set(fechas)}
    for g in guardias:
        if g.persona_id not in sipat_guardia_fechas:
            sipat_guardia_fechas[g.persona_id] = set()
        sipat_guardia_fechas[g.persona_id].add(g.fecha)
    
    # Crear un set de todas las fechas donde cualquier SIPAT tiene guardia
    todas_sipat_guardia_fechas = set()
    for fechas in sipat_guardia_fechas.values():
        todas_sipat_guardia_fechas.update(fechas)

    row = 2
    fecha_actual = inicio_mes

    while fecha_actual <= fin_mes:
        guardia = guardias_dict.get(fecha_actual.date())

        if guardia:
            persona = Persona.query.get(guardia.persona_id)
            nombre_persona = persona.nombre if persona else 'N/A'

            disponibles = obtener_personas_disponibles(
                fecha_actual.date(),
                exclude_id=guardia.persona_id
            )

            if disponibles:
                # Filtrar personas que fueron retén el día anterior o serán retén el día siguiente
                # para evitar retenes consecutivos (ni antes ni después)
                dia_anterior = fecha_actual.date() - timedelta(days=1)
                dia_siguiente = fecha_actual.date() + timedelta(days=1)

                # Verificar si la persona de guardia es SIPAT
                persona_guardia = Persona.query.get(guardia.persona_id)
                es_guardia_sipat = persona_guardia and persona_guardia.grado and 'SIPAT' in persona_guardia.grado.upper()

                # Verificar si algún SIPAT fue retén el día anterior
                hubo_sipat_reten_ayer = dia_anterior in sipat_reten_fechas

                # Verificar si algún SIPAT fue retén hace 2 días (para evitar días alternos)
                dia_hace_2 = fecha_actual.date() - timedelta(days=2)
                hubo_sipat_reten_hace_2 = dia_hace_2 in sipat_reten_fechas
                
                # Verificar si algún SIPAT tiene guardia hoy, ayer o mañana
                hay_sipat_guardia_hoy = fecha_actual.date() in todas_sipat_guardia_fechas
                hay_sipat_guardia_ayer = dia_anterior in todas_sipat_guardia_fechas
                hay_sipat_guardia_manana = dia_siguiente in todas_sipat_guardia_fechas

                candidatos = []
                for p in disponibles:
                    fue_reten_anterior = reten_fechas_dict.get((p.id, dia_anterior), False)

                    # Verificar si será retén el día siguiente (ya asignado en iteración anterior)
                    fue_reten_siguiente = reten_fechas_dict.get((p.id, dia_siguiente), False)

                    # Si la guardia es de un SIPAT, el retén no puede ser otro SIPAT
                    es_reten_sipat = p.grado and p.grado.upper().find('SIPAT') >= 0
                    if es_guardia_sipat and es_reten_sipat:
                        continue

                    # Si un SIPAT fue retén ayer, ningún SIPAT puede ser retén hoy
                    if hubo_sipat_reten_ayer and es_reten_sipat:
                        continue

                    # Si un SIPAT fue retén hace 2 días, ningún SIPAT puede ser retén hoy
                    if hubo_sipat_reten_hace_2 and es_reten_sipat:
                        continue
                    
                    # Si hay guardia de SIPAT hoy, ayer o mañana, ningún SIPAT puede ser retén hoy
                    if es_reten_sipat and (hay_sipat_guardia_hoy or hay_sipat_guardia_ayer or hay_sipat_guardia_manana):
                        continue

                    # Si este SIPAT tiene guardia mañana, no puede ser retén hoy
                    if p.id in sipat_guardia_fechas and dia_siguiente in sipat_guardia_fechas[p.id]:
                        continue

                    # Si este SIPAT tuvo guardia ayer, no puede ser retén hoy
                    if p.id in sipat_guardia_fechas and dia_anterior in sipat_guardia_fechas[p.id]:
                        continue

                    # Solo agregar si NO fue retén ni antes ni después
                    if not fue_reten_anterior and not fue_reten_siguiente:
                        candidatos.append(p)

                # Si no hay candidatos (todos tuvieron retén ayer o mañana), usar todos los disponibles
                if not candidatos:
                    candidatos = disponibles

                candidatos.sort(key=lambda p: reten_contador.get(p.id, 0))
                persona_reten = candidatos[0]
                reten = persona_reten.nombre
                
                # Recalcular si el retén seleccionado es SIPAT
                es_reten_sipat = persona_reten.grado and 'SIPAT' in persona_reten.grado.upper()

                # Registrar retén
                reten_fechas_dict[(persona_reten.id, fecha_actual.date())] = True
                reten_contador[persona_reten.id] = reten_contador.get(persona_reten.id, 0) + 1
                
                # Registrar si un SIPAT fue retén hoy
                if es_reten_sipat:
                    sipat_reten_fechas.add(fecha_actual.date())
            else:
                reten = 'SIN RETÉN'
        else:
            nombre_persona = 'SIN ASIGNAR'
            reten = 'SIN RETÉN'

        ws.cell(row=row, column=1, value=fecha_actual.day).border = border
        ws.cell(row=row, column=2, value=nombres_dias[fecha_actual.weekday()]).border = border
        ws.cell(row=row, column=3, value=nombres_meses.get(mes, f'Mes {mes}')).border = border
        ws.cell(row=row, column=4, value=nombre_persona).border = border
        ws.cell(row=row, column=5, value=reten).border = border

        for col in range(1, 6):
            ws.cell(row=row, column=col).alignment = center_alignment

        row += 1
        fecha_actual += timedelta(days=1)

    # Hoja de resumen
    _agregar_resumen_excel(
        wb, personas_activas, guardias, reten_contador,
        header_font, header_fill, border, center_alignment
    )

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer


def _agregar_resumen_excel(wb, personas, guardias, reten_contador,
                           header_font, header_fill, border, center_alignment):
    """Agrega hoja de resumen al Excel - Solo guardias del mes"""
    ws2 = wb.create_sheet(title="Resumen Guardias Mes")

    resumen_headers = ['Persona', 'Guardias este Mes']
    for col, header in enumerate(resumen_headers, 1):
        cell = ws2.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_alignment
        cell.border = border

    # Calcular estadísticas - solo guardias del mes
    resumen_dict = {
        p.id: {'nombre': p.nombre, 'guardias': 0}
        for p in personas
    }

    for g in guardias:
        if g.persona_id in resumen_dict:
            resumen_dict[g.persona_id]['guardias'] += 1

    # Escribir datos - ordenado por cantidad de guardias (mayor a menor)
    row = 2
    for datos in sorted(
        resumen_dict.values(),
        key=lambda x: x['guardias'],
        reverse=True
    ):
        ws2.cell(row=row, column=1, value=datos['nombre']).border = border
        ws2.cell(row=row, column=2, value=datos['guardias']).border = border

        for col in range(1, 3):
            ws2.cell(row=row, column=col).alignment = center_alignment
        row += 1

    ws2.column_dimensions['A'].width = 30
    ws2.column_dimensions['B'].width = 18
