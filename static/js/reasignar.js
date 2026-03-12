/**
 * Sistema de Guardias - Módulo de Reasignación
 */

const ReasignarModule = (function() {
    let fechaReasignar = null;

    /**
     * Abre el modal de reasignación
     */
    async function abrir(fecha, personaActual) {
        fechaReasignar = fecha;
        document.getElementById('reasignarFecha').textContent = fecha;
        document.getElementById('reasignarActual').textContent = personaActual;

        const res = await fetch('/api/personas');
        const personas = await res.json();

        document.getElementById('reasignarPersona').innerHTML = personas
            .filter(p => p.activo)
            .map(p => `<option value="${p.id}">${p.nombre}</option>`)
            .join('');

        new bootstrap.Modal(document.getElementById('modalReasignar')).show();
    }

    /**
     * Confirma la reasignación manual
     */
    async function confirmar() {
        const personaId = parseInt(document.getElementById('reasignarPersona').value);

        const res = await fetch('/api/guardias/reasignar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                fecha: fechaReasignar,
                persona_id: personaId
            })
        });

        const data = await res.json();

        if (res.ok) {
            bootstrap.Modal.getInstance(document.getElementById('modalReasignar')).hide();
            CalendarioModule.cargarCalendario();
            Swal.fire('Éxito', data.message, 'success');
        } else {
            Swal.fire('Error', data.error, 'error');
        }
    }

    /**
     * Reasignación aleatoria
     */
    async function random() {
        const result = await Swal.fire({
            title: '¿Reasignar aleatoriamente?',
            text: `Se seleccionará una persona disponible al azar para la guardia del ${fechaReasignar}`,
            icon: 'question',
            showCancelButton: true,
            confirmButtonText: 'Sí, asignar random'
        });

        if (result.isConfirmed) {
            const res = await fetch('/api/guardias/reasignar-random', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ fecha: fechaReasignar })
            });

            const data = await res.json();

            if (res.ok) {
                bootstrap.Modal.getInstance(document.getElementById('modalReasignar')).hide();
                CalendarioModule.cargarCalendario();
                Swal.fire({
                    title: 'Éxito',
                    html: `${data.message}<br><br>
                           <strong>Anterior:</strong> ${data.persona_anterior}<br>
                           <strong>Nueva:</strong> ${data.persona_nueva}`,
                    icon: 'success'
                });
            } else {
                Swal.fire('Error', data.error, 'error');
            }
        }
    }

    return {
        abrir,
        confirmar,
        random
    };
})();
