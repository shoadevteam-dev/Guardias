/**
 * Sistema de Guardias - Módulo de Personas
 */

const PersonasModule = (function() {
    /**
     * Carga la lista de personas en la tabla
     * @param {number} mes - Mes opcional, si no se pasa usa el valor del select
     * @param {number} anio - Año opcional, si no se pasa usa el valor del select
     */
    async function cargar(mes = null, anio = null) {
        const mesSelect = document.getElementById('selectMes');
        const anioSelect = document.getElementById('selectAnio');
        
        // Usar parámetros o valores del select
        const mesValue = mes || mesSelect.value;
        const anioValue = anio || anioSelect.value;
        
        // Si no hay valores válidos, no cargar
        if (!mesValue || !anioValue) {
            console.log('Esperando valores válidos de mes y año...');
            setTimeout(() => cargar(mes, anio), 100);
            return;
        }
        
        const res = await fetch(`/api/personas?mes=${mesValue}&anio=${anioValue}`);
        const personas = await res.json();

        const tbody = document.getElementById('tablaPersonas');
        tbody.innerHTML = personas.map(p => `
            <tr>
                <td>${p.nombre}</td>
                <td>
                    <span class="badge ${p.activo ? 'bg-success' : 'bg-secondary'}">
                        ${p.activo ? 'Activo' : 'Inactivo'}
                    </span>
                </td>
                <td>
                    <span class="badge acumulado-badge ${p.acumulado > 0 ? 'bg-warning' : p.acumulado < 0 ? 'bg-info' : 'bg-secondary'}">
                        ${p.acumulado}
                    </span>
                </td>
                <td>
                    <span class="badge bg-primary">${p.guardias ?? 0}</span>
                </td>
                <td>
                    <span class="badge bg-dark">${p.retenes ?? 0}</span>
                </td>
                <td>
                    <button class="btn btn-sm ${p.activo ? 'btn-warning' : 'btn-success'}" 
                            onclick="PersonasModule.toggleActivo(${p.id})" 
                            title="${p.activo ? 'Desactivar' : 'Activar'}">
                        <i class="bi bi-${p.activo ? 'pause' : 'play'}-circle"></i>
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="PersonasModule.eliminar(${p.id})">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            </tr>
        `).join('');

        // Llenar select de novedades
        const selectPersona = document.getElementById('novedadPersona');
        selectPersona.innerHTML = personas
            .filter(p => p.activo)
            .map(p => `<option value="${p.id}">${p.nombre}</option>`)
            .join('');
    }

    /**
     * Agrega una nueva persona
     */
    async function agregar() {
        const nombre = document.getElementById('nuevaPersona').value.trim();
        if (!nombre) {
            Swal.fire('Error', 'Ingrese un nombre', 'error');
            return;
        }

        await fetch('/api/personas', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nombre })
        });

        document.getElementById('nuevaPersona').value = '';
        await cargar();
        Swal.fire('Éxito', 'Persona agregada', 'success');
    }

    /**
     * Cambia el estado activo/inactivo de una persona
     */
    async function toggleActivo(id) {
        const result = await Swal.fire({
            title: '¿Cambiar estado?',
            text: 'Esto cambiará el estado de la persona. Las personas inactivas no se incluyen en la generación de guardias.',
            icon: 'question',
            showCancelButton: true,
            confirmButtonText: 'Sí, cambiar',
            cancelButtonText: 'Cancelar',
            confirmButtonColor: '#0d6efd'
        });

        if (result.isConfirmed) {
            await fetch(`/api/personas/${id}/toggle-activo`, { method: 'POST' });
            await cargar();
            Swal.fire('Estado actualizado', '', 'success');
        }
    }

    /**
     * Elimina una persona permanentemente
     */
    async function eliminar(id) {
        const result = await Swal.fire({
            title: '¿Eliminar permanentemente?',
            text: 'Esta acción eliminará la persona y todos sus registros relacionados. ¡No se puede deshacer!',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: 'Sí, eliminar permanentemente',
            cancelButtonText: 'Cancelar',
            confirmButtonColor: '#dc3545'
        });

        if (result.isConfirmed) {
            await fetch(`/api/personas/${id}`, { method: 'DELETE' });
            await cargar();
            Swal.fire('Eliminada', 'Persona eliminada permanentemente', 'success');
        }
    }

    return {
        cargar,
        agregar,
        toggleActivo,
        eliminar
    };
})();
