const ejecucionesPendientes = {};
let intervaloPollingGlobal = null;

function iniciarPollingLote(resultadoId, casoId, cicloId, abrirModal = false, boton = null) {
    ejecucionesPendientes[resultadoId] = {
        casoId: casoId,
        cicloId: cicloId,
        abrirModal: abrirModal,
        boton: boton
    };

    actualizarFilaResultado(resultadoId, casoId, {
        estado_ejecucion: 'pendiente',
        estado_resultado: 'en_progreso'
    });

    if (!intervaloPollingGlobal) {
        intervaloPollingGlobal = setInterval(procesarPollingLote, 3000);
    }
}

function procesarPollingLote() {
    const ids = Object.keys(ejecucionesPendientes);

    if (ids.length === 0) {
        clearInterval(intervaloPollingGlobal);
        intervaloPollingGlobal = null;
        return;
    }

    fetch(`/automatizacion/estados?ids=${ids.join(',')}`)
        .then(response => {
            if (!response.ok) throw new Error('Error al consultar estados de lote');
            return response.json();
        })
        .then(data => {
            for (const resultadoId in data) {
                const infoEjecucion = ejecucionesPendientes[resultadoId];
                if (!infoEjecucion) continue;

                const datosResultado = data[resultadoId];
                actualizarFilaResultado(resultadoId, infoEjecucion.casoId, datosResultado);

                const estado = datosResultado.estado_ejecucion;
                if (estado === 'completado' || estado === 'error') {
                    delete ejecucionesPendientes[resultadoId];

                    if (infoEjecucion.boton) {
                        infoEjecucion.boton.innerHTML = 'Completado';
                        infoEjecucion.boton.classList.remove('btn-outline-success');
                        infoEjecucion.boton.classList.add('btn-success', 'disabled');
                    }

                    if (infoEjecucion.abrirModal) {
                        if (estado === 'completado') {
                            const estadoResultadoFinal = datosResultado.estado_resultado;
                            if (estadoResultadoFinal === 'pasado') {
                                mostrarNotificacionDinamica('Prueba pasada con éxito', 'success');
                            } else if (estadoResultadoFinal === 'fallido') {
                                mostrarNotificacionDinamica('La prueba ha fallado', 'danger');
                            } else {
                                mostrarNotificacionDinamica('Prueba finalizada', 'info');
                            }
                        } else {
                            mostrarNotificacionDinamica('Error durante la ejecución del test', 'danger');
                        }

                        setTimeout(() => {
                            if (typeof abrirModalResultado === 'function') {
                                abrirModalResultado(resultadoId);
                            }
                        }, 1000);
                    }
                }
            }
        })
        .catch(error => {
            console.error('Error en el polling de lote:', error);
        });
}

function actualizarFilaResultado(resultadoId, casoId, datos) {
    const fila = document.querySelector(`tr[data-caso-id="${casoId}"]`);
    if (!fila) return;

    fila.setAttribute('data-resultado-id', resultadoId);

    const contenedorEstado = fila.querySelector('.estado-resultado-container');
    if (!contenedorEstado) return;

    const estadoColores = {
        'pasado': 'success',
        'fallido': 'danger',
        'bloqueado': 'warning',
        'en_progreso': 'info',
        'pendiente': 'secondary'
    };

    const colorEstado = estadoColores[datos.estado_resultado] || 'secondary';
    const textoEstado = (datos.estado_resultado || 'N/A').toUpperCase();

    if (datos.estado_ejecucion === 'pendiente' || datos.estado_ejecucion === 'en_progreso') {
        contenedorEstado.innerHTML = `
            <span class="badge bg-info">
                <span class="spinner-border spinner-border-sm me-2" role="status"></span>
                EN PROGRESO
            </span>
            <small class="text-muted d-block" style="font-size: 0.75rem;">Ejecutando...</small>
        `;
    } else if (datos.estado_ejecucion === 'completado' || datos.estado_ejecucion === 'error') {
        const fecha = datos.fecha_creacion ? new Date(datos.fecha_creacion) : new Date();
        const fechaFormato = fecha.toLocaleDateString('es-ES');

        contenedorEstado.innerHTML = `
            <span class="badge bg-${colorEstado}">${textoEstado}</span>
            <small class="text-muted d-block" style="font-size: 0.75rem;">${fechaFormato}</small>
        `;
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const botonesAuto = document.querySelectorAll('.execution-auto-btn');

    botonesAuto.forEach(boton => {
        boton.addEventListener('click', function(e) {
            e.preventDefault();
            const casoId = this.dataset.casoId;
            const cicloId = this.dataset.cicloId;

            if (confirm('¿Ejecutar este caso de forma automática?')) {
                ejecutarAutomaticoDinamico(casoId, cicloId, this);
            }
        });
    });
});

function ejecutarAutomaticoDinamico(casoId, cicloId, boton) {
    const textoOriginal = boton.innerHTML;
    boton.disabled = true;
    boton.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Enviando...';

    fetch(`/automatizacion/ejecutar/jenkins/${casoId}`, {
        method: 'POST',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (response.status === 202) {
            return response.json().then(data => {
                mostrarNotificacionDinamica('Test enviado a Jenkins', 'success');
                boton.innerHTML = 'En ejecución...';
                iniciarPollingLote(data.resultado_id, casoId, cicloId, true, boton);
                return data;
            });
        } else if (response.status === 400) {
            return response.json().then(data => {
                throw new Error(data.error || 'Error en la solicitud');
            });
        } else if (response.status === 503) {
            return response.json().then(data => {
                throw new Error('No se puede conectar a Jenkins');
            });
        } else {
            return response.json().then(data => {
                throw new Error(data.error || 'Error desconocido');
            }).catch(() => {
                throw new Error('Error desconocido al invocar Jenkins');
            });
        }
    })
    .catch(error => {
        boton.innerHTML = textoOriginal;
        boton.disabled = false;
        mostrarNotificacionDinamica(error.message, 'danger');
    });
}

function ejecutarCicloDinamico(cicloId, boton) {
    const textoOriginal = boton.innerHTML;
    boton.disabled = true;
    boton.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Ejecutando...';

    fetch(`/automatizacion/ejecutar/ciclo/jenkins/${cicloId}`, {
        method: 'POST',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (response.status === 202) {
            return response.json().then(data => {
                mostrarNotificacionDinamica(`${data.cantidad} casos enviados a Jenkins`, 'success');

                if (data.resultados && Array.isArray(data.resultados)) {
                    data.resultados.forEach(item => {
                        iniciarPollingLote(item.resultado_id, item.caso_id, cicloId, false, null);
                    });
                }

                boton.innerHTML = 'Ejecutando...';
                return data;
            });
        } else {
            return response.json().then(data => {
                throw new Error(data.error || 'Error en la solicitud');
            });
        }
    })
    .catch(error => {
        boton.innerHTML = textoOriginal;
        boton.disabled = false;
        mostrarNotificacionDinamica(error.message, 'danger');
    });
}

function mostrarNotificacionDinamica(mensaje, tipo) {
    const alertClass = `alert-${tipo}`;
    const alerta = document.createElement('div');
    alerta.className = `alert ${alertClass} alert-dismissible fade show shadow`;
    alerta.setAttribute('role', 'alert');
    alerta.innerHTML = `
        ${mensaje}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    const contenedor = document.querySelector('.container-fluid') || document.body;
    if (contenedor.firstChild) {
        contenedor.insertBefore(alerta, contenedor.firstChild);
    } else {
        contenedor.appendChild(alerta);
    }

    setTimeout(() => {
        alerta.remove();
    }, 5000);
}
