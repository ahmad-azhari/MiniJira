let resultadoIdIndividual = null;
let pollingIntervalIndividual = null;

function abrirModalEjecucionIndividual(casoId, casoNombre) {
    const modalEl = document.getElementById('modalEjecucionIndividual');
    if (!modalEl) {
        console.error('Modal #modalEjecucionIndividual no encontrado');
        return;
    }

    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    prepararModalIndividualCargando(casoNombre);
    modal.show();

    ejecutarTestIndividual(casoId);
}

function prepararModalIndividualCargando(casoNombre) {
    document.getElementById('modalCasoNombreIndividual').textContent = casoNombre || '';
    document.getElementById('modalEstadoIndividual').textContent = 'CARGANDO...';
    document.getElementById('modalEstadoIndividual').className = 'badge bg-secondary';
    document.getElementById('modalResultadoObtenidoIndividual').textContent = 'Iniciando ejecución...';
    document.getElementById('modalNotasIndividual').textContent = 'Cargando...';
    document.getElementById('modalLogsIndividual').textContent = 'Esperando logs de Jenkins...';
    document.getElementById('modalBuildNumberIndividual').textContent = '...';
    document.getElementById('modalNumeroIntentosIndividual').textContent = '...';
    document.getElementById('modalTiempoInicioIndividual').textContent = '...';
    document.getElementById('modalDuracionIndividual').textContent = '...';
    document.getElementById('modalEstadoEjecucionIndividual').textContent = '...';
    document.getElementById('modalUrlJenkinsIndividual').textContent = '...';

    const tabResultado = document.getElementById('tabIndividualResultado');
    if (tabResultado) {
        bootstrap.Tab.getOrCreateInstance(tabResultado).show();
    }
}

function ejecutarTestIndividual(casoId) {
    fetch('/automatizacion/ejecutar/jenkins/' + casoId, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    })
    .then(r => r.json())
    .then(data => {
        if (data.exito && data.resultado_id) {
            resultadoIdIndividual = data.resultado_id;
            iniciarPollingIndividual(resultadoIdIndividual);
        } else {
            mostrarErrorIndividual(data.error || 'Error al ejecutar test');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        mostrarErrorIndividual('Error al ejecutar test');
    });
}

function iniciarPollingIndividual(resultadoId) {
    if (pollingIntervalIndividual) {
        clearInterval(pollingIntervalIndividual);
    }

    pollingIntervalIndividual = setInterval(() => {
        actualizarEstadoIndividual(resultadoId);
    }, 2000);

    actualizarEstadoIndividual(resultadoId);
}

function actualizarEstadoIndividual(resultadoId) {
    Promise.all([
        fetch('/automatizacion/estado/' + resultadoId).then(r => r.json()),
        fetch('/automatizacion/logs/' + resultadoId).then(r => r.json())
    ])
    .then(([estado, logs]) => {
        llenarModalIndividual(estado, logs);

        if (estado.estado_ejecucion === 'completado' || estado.estado_ejecucion === 'error') {
            clearInterval(pollingIntervalIndividual);
            pollingIntervalIndividual = null;
            
            setTimeout(() => {
                Promise.all([
                    fetch('/automatizacion/estado/' + resultadoId).then(r => r.json()),
                    fetch('/automatizacion/logs/' + resultadoId).then(r => r.json())
                ])
                .then(([estadoFinal, logsFinal]) => {
                    llenarModalIndividual(estadoFinal, logsFinal);
                })
                .catch(error => {
                    console.error('Error al obtener estado final:', error);
                });
            }, 1000);
        }
    })
    .catch(error => {
        console.error('Error al actualizar estado:', error);
    });
}

function llenarModalIndividual(estado, logs) {
    const estadoColores = {
        pasado: 'success',
        fallido: 'danger',
        bloqueado: 'warning',
        en_progreso: 'info',
    };

    const estadoResultado = (estado.estado_resultado || '').toLowerCase();
    document.getElementById('modalEstadoIndividual').textContent = (estadoResultado || 'N/A').toUpperCase();
    document.getElementById('modalEstadoIndividual').className =
        `badge bg-${estadoColores[estadoResultado] || 'secondary'}`;

    document.getElementById('modalResultadoObtenidoIndividual').textContent =
        estado.resultado_obtenido || 'N/A';
    document.getElementById('modalNotasIndividual').textContent = formatearNotas(estado.notas);

    document.getElementById('modalBuildNumberIndividual').textContent = estado.jenkins_build_number || 'N/A';
    document.getElementById('modalNumeroIntentosIndividual').textContent = estado.numero_intentos || '1';

    if (estado.tiempo_inicio) {
        document.getElementById('modalTiempoInicioIndividual').textContent =
            new Date(estado.tiempo_inicio).toLocaleString('es-ES');
    } else {
        document.getElementById('modalTiempoInicioIndividual').textContent = 'N/A';
    }

    if (estado.tiempo_fin) {
        const fin = new Date(estado.tiempo_fin);
        const inicioTxt = document.getElementById('modalTiempoInicioIndividual').textContent;
        if (inicioTxt !== 'N/A') {
            document.getElementById('modalDuracionIndividual').textContent =
                estado.tiempo_ejecucion != null
                    ? `${estado.tiempo_ejecucion.toFixed(2)} seg`
                    : 'Finalizado';
        }
    } else if (estado.tiempo_ejecucion !== null && estado.tiempo_ejecucion !== undefined) {
        document.getElementById('modalDuracionIndividual').textContent = `${estado.tiempo_ejecucion.toFixed(2)} seg`;
    } else if (['pendiente', 'en_progreso'].includes((estado.estado_ejecucion || '').toLowerCase())) {
        document.getElementById('modalDuracionIndividual').textContent = 'En progreso...';
    } else {
        document.getElementById('modalDuracionIndividual').textContent = 'N/A';
    }

    document.getElementById('modalEstadoEjecucionIndividual').textContent =
        (estado.estado_ejecucion || 'N/A').toUpperCase();

    if (estado.jenkins_log_url) {
        document.getElementById('modalUrlJenkinsIndividual').innerHTML =
            `<a href="${estado.jenkins_log_url}" target="_blank" rel="noopener">${estado.jenkins_log_url}</a>`;
    } else {
        document.getElementById('modalUrlJenkinsIndividual').textContent = 'N/A';
    }

    document.getElementById('modalLogsIndividual').textContent =
        logs.output_jenkins || 'Sin logs disponibles';
}

function mostrarErrorIndividual(mensaje) {
    document.getElementById('modalEstadoIndividual').textContent = 'ERROR';
    document.getElementById('modalEstadoIndividual').className = 'badge bg-danger';
    document.getElementById('modalResultadoObtenidoIndividual').textContent = mensaje;
    document.getElementById('modalLogsIndividual').textContent = 'Error: ' + mensaje;
}

function formatearNotas(notas) {
    if (!notas || !String(notas).trim()) {
        return 'Sin notas';
    }
    return String(notas).replace(/\r\n/g, '\n').replace(/\r/g, '\n');
}

document.addEventListener('DOMContentLoaded', function () {
    const btnCopiar = document.getElementById('btnCopiarLogsIndividual');
    if (btnCopiar) {
        btnCopiar.addEventListener('click', function () {
            const logs = document.getElementById('modalLogsIndividual').textContent;
            navigator.clipboard.writeText(logs).then(() => {
                mostrarNotificacion('Logs copiados al portapapeles', 'success');
            }).catch(() => {
                mostrarNotificacion('Error al copiar logs', 'danger');
            });
        });
    }

    const btnDescargar = document.getElementById('btnDescargarLogsIndividual');
    if (btnDescargar) {
        btnDescargar.addEventListener('click', function () {
            const logs = document.getElementById('modalLogsIndividual').textContent;
            const blob = new Blob([logs], { type: 'text/plain' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `jenkins-logs-individual-${new Date().getTime()}.txt`;
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
