/**
 * Sistema de Guardias - Módulo de Acumulados
 */

const AcumuladosModule = (function() {
    /**
     * Carga los acumulados actuales
     */
    async function cargar() {
        const res = await fetch('/api/acumulados');
        const acumulados = await res.json();

        document.getElementById('tablaAcumulados').innerHTML = acumulados.map(a => `
            <tr>
                <td>${a.nombre}</td>
                <td>
                    <span class="badge ${a.acumulado > 0 ? 'bg-warning' : a.acumulado < 0 ? 'bg-info' : 'bg-secondary'}">
                        ${a.acumulado}
                    </span>
                </td>
            </tr>
        `).join('');
    }

    return {
        cargar
    };
})();
