function abrirModalCiclo(cicloId, opciones = {}) {
    const modalEl = document.getElementById('modalResultadoCiclo');
    if (!modalEl) {
        console.error('Modal #modalResultadoCiclo no encontrado');
        return;
    }

    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    document.getElementById('modalCicloNombre').textContent = opciones.cicloNombre || 'Cargando...';
    document.getElementById('modalCicloStats').innerHTML = '';
    document.getElementById('modalCicloTablaCasos').innerHTML = `
        <tr><td colspan="4" class="text-muted">Cargando resultados...</td></tr>
    `;
    document.getElementById('modalCicloLogCompleto').textContent = 'Cargando log...';

    const params = new URLSearchParams();
    if (opciones.solicitudId) {
        params.set('solicitud_id', opciones.solicitudId);
    }
    const query = params.toString() ? `?${params.toString()}` : '';

    fetch(`/automatizacion/ciclo/${cicloId}/resumen${query}`)
        .then((r) => {
            if (!r.ok) throw new Error('No se pudo cargar el resumen del ciclo');
            return r.json();
        })
        .then((data) => {
            llenarModalCiclo(data);
            modal.show();
        })
        .catch((error) => {
            console.error(error);
            if (typeof mostrarNotificacion === 'function') {
                mostrarNotificacion(error.message, 'danger');
            }
        });
}

function llenarModalCiclo(data) {
    const resumen = data.resumen || { pasados: 0, fallidos: 0, total: 0 };
    document.getElementById('modalCicloNombre').textContent = data.ciclo_nombre || `Ciclo #${data.ciclo_id}`;

    document.getElementById('modalCicloStats').innerHTML = `
        <div class="col-md-4">
            <div class="border rounded p-2 text-center">
                <div class="small text-muted">Total</div>
                <div class="fw-bold fs-5">${resumen.total}</div>
            </div>
        </div>
        <div class="col-md-4">
            <div class="border rounded p-2 text-center">
                <div class="small text-muted">Pasados</div>
                <div class="fw-bold fs-5 text-success">${resumen.pasados}</div>
            </div>
        </div>
        <div class="col-md-4">
            <div class="border rounded p-2 text-center">
                <div class="small text-muted">Fallidos</div>
                <div class="fw-bold fs-5 text-danger">${resumen.fallidos}</div>
            </div>
        </div>
    `;

    const tbody = document.getElementById('modalCicloTablaCasos');
    if (!data.casos || data.casos.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-muted">Sin resultados automatizados.</td></tr>';
    } else {
        tbody.innerHTML = data.casos.map((caso) => {
            const estado = (caso.estado || '').toLowerCase();
            const color = estado === 'pasado' ? 'success' : estado === 'fallido' ? 'danger' : 'secondary';
            const texto = (caso.estado || 'N/A').toUpperCase();
            const resultado = caso.resultado_obtenido || '—';
            return `
                <tr>
                    <td>${caso.caso_nombre}</td>
                    <td><span class="badge bg-${color}">${texto}</span></td>
                    <td class="small text-truncate" style="max-width: 220px;" title="${resultado}">${resultado}</td>
                    <td class="text-end">
                        <button type="button" class="btn btn-sm btn-outline-secondary btn-ver-caso-ciclo"
                                data-resultado-id="${caso.resultado_id}"
                                data-caso-nombre="${caso.caso_nombre}">
                            Ver
                        </button>
                    </td>
                </tr>
            `;
        }).join('');

        tbody.querySelectorAll('.btn-ver-caso-ciclo').forEach((btn) => {
            btn.addEventListener('click', () => {
                if (typeof abrirModalResultado === 'function') {
                    abrirModalResultado(btn.dataset.resultadoId, {
                        casoNombre: btn.dataset.casoNombre,
                    });
                }
            });
        });
    }

    document.getElementById('modalCicloLogCompleto').textContent =
        data.log_completo || 'Sin log disponible';

    if (data.detalles) {
        document.getElementById('modalCicloBuildNumber').textContent = data.detalles.build_number || 'N/A';
        
        if (data.detalles.fecha_ejecucion) {
            document.getElementById('modalCicloFechaEjecucion').textContent =
                new Date(data.detalles.fecha_ejecucion).toLocaleString('es-ES');
        } else {
            document.getElementById('modalCicloFechaEjecucion').textContent = 'N/A';
        }
        
        document.getElementById('modalCicloTotalCasos').textContent = resumen.total || 'N/A';
        
        if (data.detalles.duracion_total != null) {
            document.getElementById('modalCicloDuracionTotal').textContent = 
                `${data.detalles.duracion_total.toFixed(2)} seg`;
        } else {
            document.getElementById('modalCicloDuracionTotal').textContent = 'N/A';
        }
        
        document.getElementById('modalCicloEstadoEjecucion').textContent = 
            (data.detalles.estado_ejecucion || 'N/A').toUpperCase();
        
        if (data.detalles.jenkins_url) {
            document.getElementById('modalCicloUrlJenkins').innerHTML =
                `<a href="${data.detalles.jenkins_url}" target="_blank" rel="noopener">${data.detalles.jenkins_url}</a>`;
        } else {
            document.getElementById('modalCicloUrlJenkins').textContent = 'N/A';
        }
    }
}

document.addEventListener('DOMContentLoaded', function () {
    const btnCopiar = document.getElementById('btnCopiarLogCiclo');
    if (btnCopiar) {
        btnCopiar.addEventListener('click', function () {
            const logs = document.getElementById('modalCicloLogCompleto').textContent;
            navigator.clipboard.writeText(logs).then(() => {
                if (typeof mostrarNotificacion === 'function') {
                    mostrarNotificacion('Log copiado al portapapeles', 'success');
                }
            });
        });
    }
});
