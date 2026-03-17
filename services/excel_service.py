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
                # Filtrar personas que fueron retén el día anterior
                # Nota: Solo verificamos el día anterior porque procesamos en orden cronológico
                dia_anterior = fecha_actual.date() - timedelta(days=1)

                candidatos = []
                for p in disponibles:
                    fue_reten_anterior = reten_fechas_dict.get((p.id, dia_anterior), False)

                    # Solo agregar si NO fue retén el día anterior
                    if not fue_reten_anterior:
                        candidatos.append(p)

                # Si no hay candidatos (todos tuvieron retén ayer), usar todos los disponibles
                if not candidatos:
                    candidatos = disponibles
                
                candidatos.sort(key=lambda p: reten_contador.get(p.id, 0))
                persona_reten = candidatos[0]
                reten = persona_reten.nombre
                
                # Registrar retén
                reten_fechas_dict[(persona_reten.id, fecha_actual.date())] = True
                reten_contador[persona_reten.id] = reten_contador.get(persona_reten.id, 0) + 1
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
