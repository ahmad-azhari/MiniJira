function abrirModalResultado(resultadoId) {
    const modal = new bootstrap.Modal(document.getElementById('modalResultadoEjecucion'));
    const contenedor = document.getElementById('modalResultadoEjecucion');

    fetch(`/automatizacion/estado/${resultadoId}`)
        .then(response => {
            if (!response.ok) throw new Error('Error al obtener estado');
            return response.json();
        })
        .then(estado => {
            fetch(`/automatizacion/logs/${resultadoId}`)
                .then(response => response.json())
                .then(datos => {
                    llenarModalResultado(estado, datos);
                    modal.show();
                });
        })
        .catch(error => {
            console.error('Error:', error);
            mostrarNotificacion('Error al cargar detalles del resultado', 'danger');
        });
}

function llenarModalResultado(estado, datos) {
    const estadoColores = {
        'pasado': 'success',
        'fallido': 'danger',
        'bloqueado': 'warning',
        'en_progreso': 'info'
    };

    document.getElementById('modalEstado').textContent = (estado.estado_resultado || 'N/A').toUpperCase();
    document.getElementById('modalEstado').className = `badge bg-${estadoColores[estado.estado_resultado] || 'secondary'}`;

    document.getElementById('modalResultadoObtenido').textContent = estado.resultado_obtenido || 'N/A';
    document.getElementById('modalNotas').textContent = 'N/A';

    document.getElementById('modalBuildNumber').textContent = estado.jenkins_build_number || 'N/A';
    document.getElementById('modalNumeroIntentos').textContent = estado.numero_intentos || '1';

    if (estado.tiempo_inicio) {
        const fecha = new Date(estado.tiempo_inicio);
        document.getElementById('modalTiempoInicio').textContent = fecha.toLocaleString('es-ES');
    } else {
        document.getElementById('modalTiempoInicio').textContent = 'N/A';
    }

    if (estado.tiempo_ejecucion !== null && estado.tiempo_ejecucion !== undefined) {
        document.getElementById('modalDuracion').textContent = estado.tiempo_ejecucion + ' seg';
    } else {
        document.getElementById('modalDuracion').textContent = 'En progreso...';
    }

    document.getElementById('modalEstadoEjecucion').textContent = (estado.estado_ejecucion || 'N/A').toUpperCase();

    if (estado.jenkins_log_url) {
        document.getElementById('modalUrlJenkins').innerHTML = `<a href="${estado.jenkins_log_url}" target="_blank">${estado.jenkins_log_url}</a>`;
    } else {
        document.getElementById('modalUrlJenkins').textContent = 'N/A';
    }

    document.getElementById('modalLogs').textContent = datos.output_jenkins || 'Sin logs disponibles';
}

document.addEventListener('DOMContentLoaded', function() {
    const btnCopiar = document.getElementById('btnCopiarLogs');
    if (btnCopiar) {
        btnCopiar.addEventListener('click', function() {
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
        btnDescargar.addEventListener('click', function() {
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
    const alertClass = `alert-${tipo}`;
    const alerta = document.createElement('div');
    alerta.className = `alert ${alertClass} alert-dismissible fade show`;
    alerta.setAttribute('role', 'alert');
    alerta.innerHTML = `
        ${mensaje}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    const contenedor = document.querySelector('main') || document.body;
    contenedor.insertBefore(alerta, contenedor.firstChild);

    setTimeout(() => {
        alerta.remove();
    }, 5000);
}
