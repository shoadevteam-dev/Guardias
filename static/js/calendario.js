/**
 * Sistema de Guardias - Lógica del Frontend
 * Módulo: Calendario
 */

const CalendarioModule = (function() {
    let fechaReasignar = null;
    let guardiasActuales = 0;

    /**
     * Inicializa el calendario
     */
    function init() {
        const hoy = new Date();
        document.getElementById('selectMes').value = hoy.getMonth() + 1;
        document.getElementById('selectAnio').value = hoy.getFullYear();
        
        // Agregar listeners a los selectores
        document.getElementById('selectMes').addEventListener('change', function() {
            setTimeout(cargarCalendario, 100);
        });
        document.getElementById('selectAnio').addEventListener('change', function() {
            setTimeout(cargarCalendario, 100);
        });
        
        cargarCalendario();
    }

    /**
     * Actualiza el indicador de estado y los botones
     */
    function actualizarEstado(guardiasCount) {
        const estadoEl = document.getElementById('estadoCalendario');
        const btnGuardar = document.getElementById('btnGuardar');
        const btnEliminar = document.getElementById('btnEliminar');
        
        if (guardiasCount === 0) {
            estadoEl.innerHTML = '<span class="badge bg-secondary"><i class="bi bi-calendar-x"></i> Calendario vacío</span>';
            if (btnGuardar) btnGuardar.disabled = true;
            if (btnEliminar) btnEliminar.disabled = true;
        } else {
            estadoEl.innerHTML = `<span class="badge bg-success"><i class="bi bi-calendar-check"></i> ${guardiasCount} guardias asignadas</span>`;
            if (btnGuardar) btnGuardar.disabled = false;
            if (btnEliminar) btnEliminar.disabled = false;
        }
    }

    /**
     * Carga el calendario del mes seleccionado
     */
    async function cargarCalendario() {
        const mes = parseInt(document.getElementById('selectMes').value);
        const anio = parseInt(document.getElementById('selectAnio').value);

        console.log(`Cargando calendario: mes=${mes}, anio=${anio}`);

        try {
            const res = await fetch(`/api/guardias/${mes}/${anio}`);
            console.log(`Respuesta API status: ${res.status}`);
            
            if (!res.ok) {
                console.error('Error al cargar guardias:', res.status);
                return;
            }
            const guardias = await res.json();
            console.log(`Guardias recibidas: ${guardias.length}`);
            
            guardiasActuales = guardias.length;
            
            // Actualizar indicador de estado y botones
            actualizarEstado(guardias.length);

            const guardiasDict = {};
            guardias.forEach(g => {
                guardiasDict[g.fecha] = g;
            });

            const diasSemana = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'];
            const diasFin = new Date(anio, mes, 0).getDate();

            let html = '';
            for (let dia = 1; dia <= diasFin; dia++) {
                const fecha = new Date(anio, mes - 1, dia);
                const fechaStr = `${anio}-${String(mes).padStart(2, '0')}-${String(dia).padStart(2, '0')}`;
                const fechaDisplay = `${String(dia).padStart(2, '0')}/${String(mes).padStart(2, '0')}/${anio}`;
                const diaNombre = diasSemana[fecha.getDay()];
                const esFinde = fecha.getDay() === 0 || fecha.getDay() === 6;

                const guardia = guardiasDict[fechaStr];
                
                // Debug para los primeros 5 días
                if (dia <= 5) {
                    console.log(`Día ${dia}: fechaStr="${fechaStr}", guardia=${guardia ? 'ENCONRADA' : 'NO ENCONTRADA'}`);
                }
                
                const personaNombre = guardia ? guardia.persona_nombre : 'SIN ASIGNAR';
                const retenNombre = guardia ? guardia.reten_nombre : 'SIN RETÉN';
                const tipo = guardia ? guardia.tipo : '-';
                const tipoClass = guardia
                    ? (guardia.es_suplencia ? 'suplencia-badge' : guardia.tipo === 'reten' ? 'reten-badge' : 'bg-primary')
                    : 'bg-secondary';

                html += `
                    <div class="calendar-day ${esFinde ? 'weekend' : ''}">
                        <div class="row align-items-center h-100">
                            <div class="col text-center">${dia}</div>
                            <div class="col text-center">${diaNombre}</div>
                            <div class="col text-center">${fechaDisplay}</div>
                            <div class="col text-center fw-bold">${personaNombre}</div>
                            <div class="col text-center">${retenNombre}</div>
                            <div class="col text-center">
                                ${guardia ? `<span class="badge ${tipoClass}">${tipo.toUpperCase()}</span>` : '-'}
                            </div>
                            <div class="col text-center">
                                ${guardia ? `
                                    <button class="btn btn-sm btn-outline-primary" onclick="ReasignarModule.abrir('${fechaStr}', '${personaNombre}')">
                                        <i class="bi bi-arrow-left-right"></i>
                                    </button>
                                ` : ''}
                            </div>
                        </div>
                    </div>
                `;
            }

            document.getElementById('calendarBody').innerHTML = html;
        } catch (error) {
            console.error('Error en cargarCalendario:', error);
        }
    }

    /**
     * Genera guardias para el mes seleccionado
     */
    async function generarGuardias() {
        const mes = parseInt(document.getElementById('selectMes').value);
        const anio = parseInt(document.getElementById('selectAnio').value);

        const result = await Swal.fire({
            title: '¿Generar guardias?',
            text: `Se generarán las guardias para ${mes}/${anio}`,
            icon: 'question',
            showCancelButton: true,
            confirmButtonText: 'Sí, generar'
        });

        if (result.isConfirmed) {
            try {
                const response = await fetch('/api/guardias/generar', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ mes, anio })
                });

                const data = await response.json();

                if (response.ok) {
                    await new Promise(resolve => setTimeout(resolve, 300));
                    await cargarCalendario();
                    await AcumuladosModule.cargar();
                    Swal.fire('Éxito', data.message || 'Guardias generadas', 'success');
                } else {
                    Swal.fire('Error', data.error || 'Error al generar guardias', 'error');
                }
            } catch (error) {
                console.error('Error:', error);
                Swal.fire('Error', 'No se pudo conectar con el servidor', 'error');
            }
        }
    }

    /**
     * Exporta a Excel
     */
    function exportarExcel() {
        const mes = document.getElementById('selectMes').value;
        const anio = document.getElementById('selectAnio').value;
        window.location.href = `/api/exportar/${mes}/${anio}`;
    }

    /**
     * Elimina todas las guardias de un mes
     */
    async function eliminarCalendario() {
        const mes = parseInt(document.getElementById('selectMes').value);
        const anio = parseInt(document.getElementById('selectAnio').value);

        const result = await Swal.fire({
            title: '¿Eliminar calendario completo?',
            text: `Se eliminarán TODAS las guardias de ${mes}/${anio}. Esta acción no se puede deshacer.`,
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: 'Sí, eliminar todo',
            cancelButtonText: 'Cancelar',
            confirmButtonColor: '#dc3545'
        });

        if (result.isConfirmed) {
            try {
                const response = await fetch(`/api/guardias/${mes}/${anio}/eliminar`, {
                    method: 'POST'
                });

                const data = await response.json();

                if (response.ok) {
                    await cargarCalendario();
                    Swal.fire('Eliminado', data.message, 'success');
                } else {
                    Swal.fire('Error', data.error || 'Error al eliminar', 'error');
                }
            } catch (error) {
                console.error('Error:', error);
                Swal.fire('Error', 'No se pudo conectar con el servidor', 'error');
            }
        }
    }

    /**
     * Guarda el calendario del mes (exporta a Excel)
     */
    async function guardarCalendario() {
        const mes = parseInt(document.getElementById('selectMes').value);
        const anio = parseInt(document.getElementById('selectAnio').value);

        const result = await Swal.fire({
            title: '¿Guardar calendario?',
            text: `Se descargará el calendario de ${mes}/${anio} en formato Excel`,
            icon: 'question',
            showCancelButton: true,
            confirmButtonText: 'Sí, guardar',
            cancelButtonText: 'Cancelar'
        });

        if (result.isConfirmed) {
            exportarExcel();
            Swal.fire('Guardado', 'El calendario se ha descargado correctamente', 'success');
        }
    }

    return {
        init,
        cargarCalendario,
        generarGuardias,
        exportarExcel,
        eliminarCalendario,
        guardarCalendario
    };
})();
