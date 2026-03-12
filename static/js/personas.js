/**
 * Sistema de Guardias - Módulo de Personas
 */

const PersonasModule = (function() {
    /**
     * Carga la lista de personas en la tabla
     */
    async function cargar() {
        const res = await fetch('/api/personas');
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
        eliminar
    };
})();
