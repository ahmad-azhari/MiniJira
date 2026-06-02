function abrirModalPruebaManual(casoId) {
    const modalEl = document.getElementById('modalPruebaManual');
    if (!modalEl) {
        console.error('Modal #modalPruebaManual no encontrado');
        return;
    }

    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    document.getElementById('modalPruebaManualNombre').textContent = 'Cargando...';
    document.getElementById('modalPruebaManualPrioridad').textContent = '';
    document.getElementById('modalPruebaManualEstado').textContent = '';
    document.getElementById('modalPruebaManualFechaCreacion').textContent = '';
    document.getElementById('modalPruebaManualHistorias').textContent = '';
    document.getElementById('modalPruebaManualObjetivo').textContent = '';
    document.getElementById('modalPruebaManualPrecondicion').textContent = '';
    document.getElementById('modalPruebaManualPasos').textContent = '';
    document.getElementById('modalPruebaManualResultadoEsperado').textContent = '';
    document.getElementById('modalPruebaManualResultadoObtenido').textContent = '';
    document.getElementById('modalPruebaManualNotas').textContent = '';

    fetch(`/casos-prueba/${casoId}/api/detalles`)
        .then((r) => {
            if (!r.ok) throw new Error('No se pudo cargar los detalles de la prueba manual');
            return r.json();
        })
        .then((data) => {
            llenarModalPruebaManual(data);
            modal.show();
        })
        .catch((error) => {
            console.error(error);
            if (typeof mostrarNotificacion === 'function') {
                mostrarNotificacion(error.message, 'danger');
            }
        });
}

function llenarModalPruebaManual(data) {
    document.getElementById('modalPruebaManualNombre').textContent = data.nombre || 'N/A';

    const prioridadColores = {
        'alta': 'danger',
        'media': 'warning',
        'baja': 'success'
    };
    const prioridadColor = prioridadColores[data.prioridad] || 'secondary';
    document.getElementById('modalPruebaManualPrioridad').innerHTML = 
        `<span class="badge bg-${prioridadColor}">${data.prioridad.toUpperCase()}</span>`;

    const estadoColores = {
        'nuevo': 'info',
        'en_progreso': 'primary',
        'terminado': 'success'
    };
    const estadoColor = estadoColores[data.estado] || 'secondary';
    document.getElementById('modalPruebaManualEstado').innerHTML = 
        `<span class="badge bg-${estadoColor}">${data.estado.toUpperCase()}</span>`;

    if (data.fecha_creacion) {
        const fecha = new Date(data.fecha_creacion);
        document.getElementById('modalPruebaManualFechaCreacion').textContent = 
            fecha.toLocaleDateString('es-ES') + ' ' + fecha.toLocaleTimeString('es-ES');
    } else {
        document.getElementById('modalPruebaManualFechaCreacion').textContent = 'N/A';
    }

    document.getElementById('modalPruebaManualHistorias').textContent = 
        data.historias.length > 0 ? data.historias.join(', ') : 'Sin historias asociadas';

    document.getElementById('modalPruebaManualObjetivo').textContent = data.objetivo || 'Sin objetivo';
    document.getElementById('modalPruebaManualPrecondicion').textContent = data.precondicion || 'Sin precondición';
    document.getElementById('modalPruebaManualPasos').textContent = data.pasos_reproduccion || 'Sin pasos de reproducción';
    document.getElementById('modalPruebaManualResultadoEsperado').textContent = data.resultado_esperado || 'Sin resultado esperado';
    document.getElementById('modalPruebaManualResultadoObtenido').textContent = data.resultado_obtenido || 'Sin resultado obtenido';
    document.getElementById('modalPruebaManualNotas').textContent = data.notas || 'Sin notas';
}

document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.btn-ver-prueba-manual').forEach((btn) => {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            const casoId = this.dataset.casoId;
            abrirModalPruebaManual(casoId);
        });
    });
});
