const ejecucionesPendientes = {};
const seguimientoCiclos = {};
let intervaloPollingGlobal = null;

const HTML_BTN_CICLO_ORIGINAL = '<i class="bi bi-play-fill"></i> Ejecutar Ciclo Completo';
const HTML_BTN_CICLO_DETALLE = '<i class="bi bi-play-fill"></i> Ejecutar con Jenkins';

function iniciarPollingLote(resultadoId, casoId, cicloId, abrirModal = false, boton = null) {
    ejecucionesPendientes[resultadoId] = {
        casoId: casoId,
        cicloId: cicloId,
        abrirModal: abrirModal,
        boton: boton,
    };

    actualizarFilaResultado(resultadoId, casoId, {
        estado_ejecucion: 'pendiente',
        estado_resultado: 'en_progreso',
    });

    if (!intervaloPollingGlobal) {
        intervaloPollingGlobal = setInterval(procesarPollingLote, 3000);
    }
}

function iniciarSeguimientoCiclo(cicloId, boton, resultadoIds, solicitudId) {
    seguimientoCiclos[cicloId] = {
        pendientes: new Set(resultadoIds.map(String)),
        boton,
        solicitudId: solicitudId || null,
        textoOriginal: boton.dataset.textoOriginal || boton.innerHTML,
    };
    boton.dataset.textoOriginal = seguimientoCiclos[cicloId].textoOriginal;
    if (solicitudId) {
        boton.dataset.ultimaSolicitud = solicitudId;
    }
    boton.disabled = true;
    boton.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Ejecutando...';
    mostrarBotonResumenCiclo(cicloId, false);
}

function finalizarSeguimientoCicloSiCorresponde(cicloId, resultadoId) {
    const seg = seguimientoCiclos[cicloId];
    if (!seg) return;

    seg.pendientes.delete(String(resultadoId));
    if (seg.pendientes.size > 0) return;

    seg.boton.disabled = false;
    seg.boton.innerHTML = 'Ejecutar de nuevo';
    seg.boton.classList.remove('btn-secondary');
    if (!seg.boton.classList.contains('btn-success')) {
        seg.boton.classList.add('btn-success');
    }
    mostrarBotonResumenCiclo(cicloId, true, seg.solicitudId);
    mostrarNotificacionDinamica('Ejecución del ciclo finalizada', 'info');
    delete seguimientoCiclos[cicloId];
}

function mostrarBotonResumenCiclo(cicloId, visible, solicitudId) {
    document.querySelectorAll(`[data-ver-ciclo-id="${cicloId}"]`).forEach((btn) => {
        if (visible) {
            btn.classList.remove('d-none');
            if (solicitudId) {
                btn.dataset.solicitudId = solicitudId;
            }
        } else {
            btn.classList.add('d-none');
        }
    });
}

function reanudarPollingPendientes() {
    document.querySelectorAll('tr[data-resultado-id][data-caso-id]').forEach((fila) => {
        const resultadoId = fila.getAttribute('data-resultado-id');
        const casoId = fila.getAttribute('data-caso-id');
        const cicloId = fila.getAttribute('data-ciclo-id');
        const pendiente = fila.getAttribute('data-ejecucion-pendiente') === 'true';

        if (resultadoId && casoId && pendiente && !ejecucionesPendientes[resultadoId]) {
            iniciarPollingLote(resultadoId, casoId, cicloId, false, null);
        }
    });

    reanudarSeguimientoCicloSiHayPendientes();
}

function reanudarSeguimientoCicloSiHayPendientes() {
    const botonCiclo = document.getElementById('executeFullCycleBtn')
        || document.getElementById('executeJenkinsCycleBtn');
    if (!botonCiclo) return;

    const cicloId = botonCiclo.dataset.cicloId;
    if (!cicloId) return;

    const filasPendientes = document.querySelectorAll(
        `tr[data-ciclo-id="${cicloId}"][data-ejecucion-pendiente="true"]`
    );
    if (filasPendientes.length === 0) return;

    const ids = [];
    filasPendientes.forEach((fila) => {
        const resultadoId = fila.getAttribute('data-resultado-id');
        if (resultadoId) ids.push(resultadoId);
    });
    if (ids.length === 0) return;

    if (!seguimientoCiclos[cicloId]) {
        iniciarSeguimientoCiclo(cicloId, botonCiclo, ids, botonCiclo.dataset.ultimaSolicitud);
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
        .then((response) => {
            if (!response.ok) throw new Error('Error al consultar estados de lote');
            return response.json();
        })
        .then((data) => {
            for (const resultadoId in data) {
                const infoEjecucion = ejecucionesPendientes[resultadoId];
                if (!infoEjecucion) continue;

                const datosResultado = data[resultadoId];
                actualizarFilaResultado(resultadoId, infoEjecucion.casoId, datosResultado);

                const estadoEjecucion = (datosResultado.estado_ejecucion || '').toLowerCase();
                if (estadoEjecucion === 'completado' || estadoEjecucion === 'error') {
                    delete ejecucionesPendientes[resultadoId];
                    habilitarBotonVerResultado(resultadoId, infoEjecucion.casoId);

                    if (infoEjecucion.cicloId) {
                        finalizarSeguimientoCicloSiCorresponde(infoEjecucion.cicloId, resultadoId);
                    }

                    if (infoEjecucion.boton) {
                        infoEjecucion.boton.innerHTML = 'Completado';
                        infoEjecucion.boton.classList.remove('btn-outline-success');
                        infoEjecucion.boton.classList.add('btn-success', 'disabled');
                    }

                    if (infoEjecucion.abrirModal) {
                        const estadoResultadoFinal = (datosResultado.estado_resultado || '').toLowerCase();
                        if (estadoEjecucion === 'completado') {
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
                                abrirModalResultado(resultadoId, {
                                    casoNombre: obtenerNombreCaso(infoEjecucion.casoId),
                                });
                            }
                        }, 800);
                    }
                }
            }
        })
        .catch((error) => {
            console.error('Error en el polling de lote:', error);
        });
}

function obtenerNombreCaso(casoId) {
    const fila = document.querySelector(`tr[data-caso-id="${casoId}"]`);
    if (!fila) return '';
    const titulo = fila.querySelector('.fw-bold');
    return titulo ? titulo.textContent.trim() : '';
}

function habilitarBotonVerResultado(resultadoId, casoId) {
    const fila = document.querySelector(`tr[data-caso-id="${casoId}"]`);
    if (!fila) return;
    fila.setAttribute('data-resultado-id', resultadoId);
    fila.setAttribute('data-ejecucion-pendiente', 'false');

    const btn = fila.querySelector('.btn-ver-resultado');
    if (btn) {
        btn.disabled = false;
        btn.classList.remove('d-none');
    }
}

function actualizarFilaResultado(resultadoId, casoId, datos) {
    const fila = document.querySelector(`tr[data-caso-id="${casoId}"]`);
    if (!fila) return;

    const tipoCaso = fila.getAttribute('data-tipo-caso');
    if (tipoCaso !== 'automatizado') {
        return;
    }

    const resultadoIdExistente = fila.getAttribute('data-resultado-id');
    if (!resultadoIdExistente || resultadoIdExistente === resultadoId) {
        fila.setAttribute('data-resultado-id', resultadoId);
    } else {
        return;
    }

    const contenedorEstado = fila.querySelector('.estado-resultado-container');
    if (!contenedorEstado) return;

    const estadoColores = {
        pasado: 'success',
        fallido: 'danger',
        en_progreso: 'info',
        pendiente: 'secondary',
    };

    const estadoResultado = (datos.estado_resultado || '').toLowerCase();
    const estadoEjecucion = (datos.estado_ejecucion || '').toLowerCase();
    const colorEstado = estadoColores[estadoResultado] || 'secondary';
    const textoEstado = (datos.estado_resultado || 'N/A').toUpperCase();

    if (estadoEjecucion === 'pendiente' || estadoEjecucion === 'en_progreso') {
        fila.setAttribute('data-ejecucion-pendiente', 'true');
        contenedorEstado.innerHTML = `
            <span class="badge bg-info">
                <span class="spinner-border spinner-border-sm me-2" role="status"></span>
                EN PROGRESO
            </span>
            <small class="text-muted d-block" style="font-size: 0.75rem;">Ejecutando en Jenkins...</small>
        `;
    } else if (estadoEjecucion === 'completado' || estadoEjecucion === 'error') {
        fila.setAttribute('data-ejecucion-pendiente', 'false');
        const fecha = datos.fecha_creacion ? new Date(datos.fecha_creacion) : new Date();
        const fechaFormato = fecha.toLocaleDateString('es-ES');

        contenedorEstado.innerHTML = `
            <span class="badge bg-${colorEstado}">${textoEstado}</span>
            <small class="text-muted d-block" style="font-size: 0.75rem;">${fechaFormato}</small>
        `;
    }
}

document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.btn-ver-resultado').forEach((btn) => {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            const fila = this.closest('tr');
            const resultadoId = fila?.getAttribute('data-resultado-id');
            const casoId = fila?.getAttribute('data-caso-id');
            if (resultadoId && typeof abrirModalResultado === 'function') {
                abrirModalResultado(resultadoId, { casoNombre: obtenerNombreCaso(casoId) });
            }
        });
    });

    document.querySelectorAll('.btn-ver-resumen-ciclo').forEach((btn) => {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            const cicloId = this.dataset.verCicloId;
            const solicitudId = this.dataset.solicitudId || null;
            const cicloNombre = this.dataset.cicloNombre || '';
            if (cicloId && typeof abrirModalCiclo === 'function') {
                abrirModalCiclo(cicloId, { solicitudId, cicloNombre });
            }
        });
    });

    document.querySelectorAll('.execution-auto-btn').forEach((boton) => {
        boton.addEventListener('click', function (e) {
            e.preventDefault();
            const casoId = this.dataset.casoId;
            const cicloId = this.dataset.cicloId;

            if (confirm('¿Ejecutar este caso de forma automática?')) {
                ejecutarAutomaticoDinamico(casoId, cicloId, this);
            }
        });
    });

    reanudarPollingPendientes();
});

function ejecutarAutomaticoDinamico(casoId, cicloId, boton) {
    const textoOriginal = boton.innerHTML;
    boton.disabled = true;
    boton.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Enviando...';

    const body = cicloId ? JSON.stringify({ ciclo_id: cicloId }) : null;

    fetch(`/automatizacion/ejecutar/jenkins/${casoId}`, {
        method: 'POST',
        headers: {
            Accept: 'application/json',
            ...(body ? { 'Content-Type': 'application/json' } : {}),
        },
        body,
    })
        .then((response) => {
            if (response.status === 202) {
                return response.json().then((data) => {
                    mostrarNotificacionDinamica('Test enviado a Jenkins', 'success');
                    boton.innerHTML = 'En ejecución...';
                    iniciarPollingLote(data.resultado_id, casoId, cicloId, true, boton);
                    return data;
                });
            }
            return response.json().then((data) => {
                throw new Error(data.error || 'Error en la solicitud');
            });
        })
        .catch((error) => {
            boton.innerHTML = textoOriginal;
            boton.disabled = false;
            mostrarNotificacionDinamica(error.message, 'danger');
        });
}

function ejecutarCicloDinamico(cicloId, boton) {
    const textoOriginal = boton.dataset.textoOriginal || boton.innerHTML;
    boton.disabled = true;
    boton.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Enviando...';

    fetch(`/automatizacion/ejecutar/ciclo/jenkins/${cicloId}`, {
        method: 'POST',
        headers: {
            Accept: 'application/json',
            'Content-Type': 'application/json',
        },
    })
        .then((response) => {
            if (response.status === 202) {
                return response.json().then((data) => {
                    mostrarNotificacionDinamica(`${data.cantidad} casos enviados a Jenkins`, 'success');

                    if (data.resultados && Array.isArray(data.resultados)) {
                        const ids = data.resultados.map((item) => item.resultado_id);
                        iniciarSeguimientoCiclo(cicloId, boton, ids, data.id_solicitud);
                        data.resultados.forEach((item) => {
                            iniciarPollingLote(item.resultado_id, item.caso_id, cicloId, false, null);
                        });
                    } else {
                        boton.disabled = false;
                        boton.innerHTML = textoOriginal;
                    }

                    return data;
                });
            }
            return response.json().then((data) => {
                throw new Error(data.error || 'Error en la solicitud');
            });
        })
        .catch((error) => {
            boton.innerHTML = textoOriginal;
            boton.disabled = false;
            mostrarNotificacionDinamica(error.message, 'danger');
        });
}

function mostrarNotificacionDinamica(mensaje, tipo) {
    const alerta = document.createElement('div');
    alerta.className = `alert alert-${tipo} alert-dismissible fade show shadow`;
    alerta.setAttribute('role', 'alert');
    alerta.innerHTML = `
        ${mensaje}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    const contenedor = document.querySelector('.container-fluid') || document.querySelector('main') || document.body;
    if (contenedor.firstChild) {
        contenedor.insertBefore(alerta, contenedor.firstChild);
    } else {
        contenedor.appendChild(alerta);
    }

    setTimeout(() => alerta.remove(), 5000);
}
