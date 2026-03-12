/**
 * Sistema de Guardias - Módulo de Importación
 */

const ImportarModule = (function() {
    /**
     * Abre el modal de importación
     */
    async function abrirModal() {
        const mes = parseInt(document.getElementById('importarMes').value);
        const anio = parseInt(document.getElementById('importarAnio').value);
        await cargarTabla(mes, anio);
        new bootstrap.Modal(document.getElementById('modalHistorico')).show();
    }

    /**
     * Carga la tabla de importación
     */
    async function cargarTabla(mes, anio) {
        const diasEnMes = new Date(anio, mes, 0).getDate();

        const res = await fetch('/api/personas');
        const personas = await res.json();
        const personasActivas = personas.filter(p => p.activo);

        const resGuardias = await fetch(`/api/guardias/${mes}/${anio}`);
        const guardiasExistentes = await resGuardias.json();
        const guardiasDict = {};
        guardiasExistentes.forEach(g => {
            guardiasDict[g.fecha] = g.persona_id;
        });

        let html = '';
        for (let dia = 1; dia <= diasEnMes; dia++) {
            const fecha = new Date(anio, mes - 1, dia);
            const fechaStr = `${anio}-${String(mes).padStart(2, '0')}-${String(dia).padStart(2, '0')}`;
            const personaId = guardiasDict[fechaStr] || '';

            html += `<tr>
                <td>${dia}</td>
                <td>${fechaStr}</td>
                <td>
                    <select class="form-select form-select-sm" data-fecha="${fechaStr}">
                        <option value="">-- Sin asignar --</option>
                        ${personasActivas.map(p => `
                            <option value="${p.id}" ${p.id == personaId ? 'selected' : ''}>
                                ${p.nombre}
                            </option>
                        `).join('')}
                    </select>
                </td>
            </tr>`;
        }

        document.getElementById('tablaImportar').innerHTML = html;
    }

    /**
     * Guarda la importación
     */
    async function guardar() {
        const mes = parseInt(document.getElementById('importarMes').value);
        const anio = parseInt(document.getElementById('importarAnio').value);

        const selects = document.querySelectorAll('#tablaImportar select');
        const guardias = [];

        for (let select of selects) {
            const personaId = select.value;
            if (personaId) {
                guardias.push({
                    fecha: select.dataset.fecha,
                    persona_id: parseInt(personaId)
                });
            }
        }

        if (guardias.length === 0) {
            Swal.fire('Atención', 'No has asignado ninguna guardia', 'warning');
            return;
        }

        const result = await Swal.fire({
            title: '¿Guardar asignaciones?',
            text: `Se asignarán ${guardias.length} guardias para ${mes}/${anio}`,
            icon: 'question',
            showCancelButton: true,
            confirmButtonText: 'Sí, guardar'
        });

        if (result.isConfirmed) {
            let exitosas = 0;
            for (let guardia of guardias) {
                const res = await fetch('/api/guardias/asignar', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        fecha: guardia.fecha,
                        persona_id: guardia.persona_id
                    })
                });
                if (res.ok) exitosas++;
            }

            bootstrap.Modal.getInstance(document.getElementById('modalHistorico')).hide();
            Swal.fire('Éxito', `Se guardaron ${exitosas}/${guardias.length} guardias`, 'success');
            CalendarioModule.cargarCalendario();
            AcumuladosModule.cargar();
        }
    }

    return {
        abrirModal,
        cargarTabla,
        guardar
    };
})();
