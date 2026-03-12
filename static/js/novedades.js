/**
 * Sistema de Guardias - Módulo de Novedades
 */

const NovedadesModule = (function() {
    /**
     * Carga la lista de novedades
     */
    async function cargar() {
        const res = await fetch('/api/novedades');
        const novedades = await res.json();

        document.getElementById('tablaNovedades').innerHTML = novedades.map(n => `
            <tr>
                <td>${n.persona_nombre}</td>
                <td><span class="badge bg-warning">${n.tipo}</span></td>
                <td>${n.fecha_inicio}</td>
                <td>${n.fecha_fin}</td>
                <td>
                    <button class="btn btn-sm btn-danger" onclick="NovedadesModule.eliminar(${n.id})">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }

    /**
     * Agrega una nueva novedad
     */
    async function agregar() {
        const data = {
            persona_id: parseInt(document.getElementById('novedadPersona').value),
            tipo: document.getElementById('novedadTipo').value,
            descripcion: document.getElementById('novedadDescripcion').value,
            fecha_inicio: document.getElementById('novedadFechaInicio').value,
            fecha_fin: document.getElementById('novedadFechaFin').value
        };

        if (!data.fecha_inicio || !data.fecha_fin) {
            Swal.fire('Error', 'Complete las fechas', 'error');
            return;
        }

        await fetch('/api/novedades', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        document.getElementById('formNovedad').reset();
        await cargar();
        Swal.fire('Éxito', 'Novedad agregada', 'success');
    }

    /**
     * Elimina una novedad
     */
    async function eliminar(id) {
        await fetch(`/api/novedades/${id}`, { method: 'DELETE' });
        await cargar();
        Swal.fire('Eliminada', '', 'success');
    }

    return {
        cargar,
        agregar,
        eliminar
    };
})();
