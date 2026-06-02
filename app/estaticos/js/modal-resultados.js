function formatearNotas(notas) {
    if (!notas || !String(notas).trim()) {
        return 'Sin notas';
    }
    return String(notas).replace(/\r\n/g, '\n').replace(/\r/g, '\n');
}

function abrirModalResultado(resultadoId, opciones = {}) {
    const modalEl = document.getElementById('modalResultadoEjecucion');
    if (!modalEl) {
        console.error('Modal #modalResultadoEjecucion no encontrado');
        return;
    }

    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    prepararModalCargando(opciones.casoNombre);

    Promise.all([
        fetch(`/automatizacion/estado/${resultadoId}`).then(r => {
            if (!r.ok) throw new Error('Error al obtener estado');
            return r.json();
        }),
        fetch(`/automatizacion/logs/${resultadoId}`).then(r => {
            if (!r.ok) throw new Error('Error al obtener logs');
            return r.json();
        }),
    ])
        .then(([estado, logs]) => {
            llenarModalResultado(estado, logs, opciones);
            modal.show();
        })
        .catch(error => {
            console.error('Error:', error);
            mostrarNotificacion('Error al cargar detalles del resultado', 'danger');
        });
}

function prepararModalCargando(casoNombre) {
    document.getElementById('modalCasoNombre').textContent = casoNombre || '';
    document.getElementById('modalEstado').textContent = 'CARGANDO...';
    document.getElementById('modalEstado').className = 'badge bg-secondary';
    document.getElementById('modalResultadoObtenido').textContent = 'Cargando...';
    document.getElementById('modalNotas').textContent = 'Cargando...';
    document.getElementById('modalLogs').textContent = 'Cargando logs...';
    document.getElementById('modalBuildNumber').textContent = '...';
    document.getElementById('modalNumeroIntentos').textContent = '...';
    document.getElementById('modalTiempoInicio').textContent = '...';
    document.getElementById('modalDuracion').textContent = '...';
    document.getElementById('modalEstadoEjecucion').textContent = '...';
    document.getElementById('modalUrlJenkins').textContent = '...';

    const tabResultado = document.getElementById('tabResultado');
    if (tabResultado) {
        bootstrap.Tab.getOrCreateInstance(tabResultado).show();
    }
}

function llenarModalResultado(estado, datos, opciones = {}) {
    const estadoColores = {
        pasado: 'success',
        fallido: 'danger',
        bloqueado: 'warning',
        en_progreso: 'info',
    };

    const estadoResultado = (estado.estado_resultado || '').toLowerCase();
    document.getElementById('modalCasoNombre').textContent =
        opciones.casoNombre || estado.caso_nombre || `Resultado #${estado.resultado_id || ''}`;

    document.getElementById('modalEstado').textContent = (estadoResultado || 'N/A').toUpperCase();
    document.getElementById('modalEstado').className =
        `badge bg-${estadoColores[estadoResultado] || 'secondary'}`;

    document.getElementById('modalResultadoObtenido').textContent =
        estado.resultado_obtenido || 'N/A';
    document.getElementById('modalNotas').textContent = formatearNotas(estado.notas);

    document.getElementById('modalBuildNumber').textContent = estado.jenkins_build_number || 'N/A';
    document.getElementById('modalNumeroIntentos').textContent = estado.numero_intentos || '1';

    if (estado.tiempo_inicio) {
        document.getElementById('modalTiempoInicio').textContent =
            new Date(estado.tiempo_inicio).toLocaleString('es-ES');
    } else {
        document.getElementById('modalTiempoInicio').textContent = 'N/A';
    }

    if (estado.tiempo_fin) {
        const fin = new Date(estado.tiempo_fin);
        const inicioTxt = document.getElementById('modalTiempoInicio').textContent;
        if (inicioTxt !== 'N/A') {
            document.getElementById('modalDuracion').textContent =
                estado.tiempo_ejecucion != null
                    ? `${estado.tiempo_ejecucion.toFixed(2)} seg`
                    : 'Finalizado';
        }
    } else if (estado.tiempo_ejecucion !== null && estado.tiempo_ejecucion !== undefined) {
        document.getElementById('modalDuracion').textContent = `${estado.tiempo_ejecucion.toFixed(2)} seg`;
    } else if (['pendiente', 'en_progreso'].includes((estado.estado_ejecucion || '').toLowerCase())) {
        document.getElementById('modalDuracion').textContent = 'En progreso...';
    } else {
        document.getElementById('modalDuracion').textContent = 'N/A';
    }

    document.getElementById('modalEstadoEjecucion').textContent =
        (estado.estado_ejecucion || 'N/A').toUpperCase();

    if (estado.jenkins_log_url) {
        document.getElementById('modalUrlJenkins').innerHTML =
            `<a href="${estado.jenkins_log_url}" target="_blank" rel="noopener">${estado.jenkins_log_url}</a>`;
    } else {
        document.getElementById('modalUrlJenkins').textContent = 'N/A';
    }

    document.getElementById('modalLogs').textContent =
        datos.output_jenkins || 'Sin logs disponibles';
}

document.addEventListener('DOMContentLoaded', function () {
    const btnCopiar = document.getElementById('btnCopiarLogs');
    if (btnCopiar) {
        btnCopiar.addEventListener('click', function () {
            const logs = document.getElementById('modalLogs').textContent;
            navigator.clipboard.writeText(logs).then(() => {
                mostrarNotificacion('Logs copiados al portapapeles', 'success');
            }).catch(() => {
                mostrarNotificacion('Error al copiar logs', 'danger');
            });
        });
    }

    const btnDescargar = document.getElementById('btnDescargarLogs');
    if (btnDescargar) {
        btnDescargar.addEventListener('click', function () {
            const logs = document.getElementById('modalLogs').textContent;
            const blob = new Blob([logs], { type: 'text/plain' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `jenkins-logs-${new Date().getTime()}.txt`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        });
    }
});

function mostrarNotificacion(mensaje, tipo) {
    if (typeof mostrarNotificacionDinamica === 'function') {
        mostrarNotificacionDinamica(mensaje, tipo);
        return;
    }

    const alerta = document.createElement('div');
    alerta.className = `alert alert-${tipo} alert-dismissible fade show`;
    alerta.setAttribute('role', 'alert');
    alerta.innerHTML = `
        ${mensaje}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    const contenedor = document.querySelector('main') || document.body;
    contenedor.insertBefore(alerta, contenedor.firstChild);

    setTimeout(() => alerta.remove(), 5000);
}
