document.addEventListener('DOMContentLoaded', function() {
    const autoButtons = document.querySelectorAll('.execution-auto-btn');

    autoButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const casoId = this.dataset.casoId;
            const cicloId = this.dataset.cicloId;

            if (confirm('¿Ejecutar este caso de forma automática?')) {
                ejecutarAutomatic(casoId, cicloId, this);
            }
        });
    });
});

function ejecutarAutomatic(casoId, cicloId, button) {
    const originalText = button.innerHTML;
    button.disabled = true;
    button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Enviando...';

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
                showNotification('Test enviado a Jenkins', 'success');
                startPolling(data.resultado_id, button);
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
            throw new Error('Error desconocido');
        }
    })
    .catch(error => {
        button.innerHTML = originalText;
        button.disabled = false;
        showNotification(error.message, 'danger');
    });
}

function startPolling(resultadoId, button) {
    const pollInterval = setInterval(() => {
        fetch(`/automatizacion/estado/${resultadoId}`)
            .then(response => response.json())
            .then(data => {
                const estado = data.estado_ejecucion;

                if (estado === 'completado' || estado === 'error') {
                    clearInterval(pollInterval);
                    button.innerHTML = 'Completado';
                    button.classList.remove('btn-outline-success');
                    button.classList.add('btn-success', 'disabled');

                    if (estado === 'completado') {
                        const resultState = data.estado_resultado;
                        if (resultState === 'pasado') {
                            showNotification('Prueba pasada', 'success');
                        } else if (resultState === 'fallido') {
                            showNotification('Prueba fallida', 'danger');
                        } else {
                            showNotification('Prueba completada', 'info');
                        }
                    } else {
                        showNotification('Error en la ejecución', 'danger');
                    }

                    setTimeout(() => location.reload(), 2000);
                }
            })
            .catch(error => {
                console.error('Error polling:', error);
            });
    }, 3000);
}

function showNotification(message, type) {
    const alertClass = `alert-${type}`;
    const alert = document.createElement('div');
    alert.className = `alert ${alertClass} alert-dismissible fade show`;
    alert.setAttribute('role', 'alert');
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    const container = document.querySelector('main') || document.body;
    container.insertBefore(alert, container.firstChild);

    setTimeout(() => {
        alert.remove();
    }, 5000);
}

