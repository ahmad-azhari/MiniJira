from flask import Blueprint, request, jsonify, session, redirect, url_for, flash, current_app
from app.base_datos import db
from app.modelos import CasoPrueba, CicloPrueba
from app.servicios.automatizacion_service import AutomatizacionService
from app.servicios.jenkins_service import ServicioJenkins
from app.decoradores import requerir_autenticacion, requerir_miembro
import uuid

automatizacion_bp = Blueprint('automatizacion_bp', __name__, url_prefix='/automatizacion')


@automatizacion_bp.post('/ejecutar/jenkins/<int:caso_id>')
@requerir_miembro
def ejecutar_test_jenkins(caso_id):
    try:
        caso = CasoPrueba.query.get_or_404(caso_id)

        jenkins = ServicioJenkins()

        if not jenkins.validar_conexion():
            flash('No se puede conectar a Jenkins', 'danger')
            return redirect(request.referrer or url_for('casos_prueba_bp.detalle', caso_id=caso_id))

        exito = jenkins.lanzar_test(
            caso_id=caso_id,
            script_test=caso.script_prueba
        )

        if exito:
            flash('Test enviado a Jenkins correctamente', 'success')
        else:
            flash('Error al enviar test a Jenkins', 'danger')

    except Exception as e:
        current_app.logger.error(f"Error ejecutar test: {e}", exc_info=True)
        flash(f'Error: {str(e)}', 'danger')

    return redirect(request.referrer or url_for('casos_prueba_bp.detalle', caso_id=caso_id))


@automatizacion_bp.post('/ejecutar/ciclo/jenkins/<int:ciclo_id>')
@requerir_miembro
def ejecutar_ciclo_jenkins(ciclo_id):
    try:
        ciclo = CicloPrueba.query.get_or_404(ciclo_id)

        if not ciclo.casos_prueba:
            flash('El ciclo no tiene casos de prueba', 'warning')
            return redirect(request.referrer or url_for('ciclos_prueba_bp.detalle', id=ciclo_id))

        jenkins = ServicioJenkins()

        if not jenkins.validar_conexion():
            flash('No se puede conectar a Jenkins', 'danger')
            return redirect(request.referrer or url_for('ciclos_prueba_bp.detalle', id=ciclo_id))

        cantidad = jenkins.lanzar_ciclo(ciclo_id=ciclo_id)

        if cantidad > 0:
            flash(f'Se enviaron {cantidad} tests a Jenkins correctamente', 'success')
        else:
            flash('Error al enviar tests a Jenkins', 'danger')

    except Exception as e:
        current_app.logger.error(f"Error ejecutar ciclo: {e}", exc_info=True)
        flash(f'Error: {str(e)}', 'danger')

    return redirect(request.referrer or url_for('ciclos_prueba_bp.detalle', id=ciclo_id))


@automatizacion_bp.post('/api/resultados/desde-jenkins/<int:caso_id>')
def callback_jenkins(caso_id):
    try:
        datos = request.get_json()

        if not datos:
            return {'error': 'Sin JSON recibido'}, 400

        resultado = AutomatizacionService.procesar_resultado_jenkins(
            caso_id=caso_id,
            datos=datos
        )

        return {'estado': 'OK', 'resultado_id': resultado.id}, 200

    except ValueError as e:
        current_app.logger.error(f"Error validación callback: {e}")
        return {'error': str(e)}, 400
    except Exception as e:
        current_app.logger.error(f"Error inesperado callback: {e}", exc_info=True)
        return {'error': 'Error interno'}, 500
