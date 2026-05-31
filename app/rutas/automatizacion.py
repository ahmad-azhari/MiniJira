from flask import Blueprint, request, jsonify, session, redirect, url_for, flash, current_app
from app.base_datos import db
from app.modelos import CasoPrueba, CicloPrueba
from app.servicios.automatizacion_service import AutomatizacionService
from app.servicios.jenkins_service import ServicioJenkins
from app.decoradores import requerir_autenticacion, requerir_miembro
from config.constantes import EstadoEjecucionEnum
import uuid

automatizacion_bp = Blueprint('automatizacion_bp', __name__, url_prefix='/automatizacion')


@automatizacion_bp.post('/ejecutar/jenkins/<int:caso_id>')
@requerir_miembro
def ejecutar_test_jenkins(caso_id):
    try:
        caso = CasoPrueba.query.get_or_404(caso_id)

        if not caso.tiene_script_valido():
            return jsonify({
                'error': 'El caso no es automatizado o no tiene script válido'
            }), 400

        jenkins = ServicioJenkins()

        if not jenkins.validar_conexion():
            return jsonify({
                'error': 'No se puede conectar a Jenkins'
            }), 503

        resultado_jenkins = jenkins.lanzar_test(
            caso_id=caso_id,
            script_test=caso.script_prueba
        )

        if resultado_jenkins['exito']:
            resultado = AutomatizacionService.crear_resultado_automatizado(
                caso_id=caso_id,
                build_number=resultado_jenkins.get('build_number')
            )

            if request.headers.get('Accept') == 'application/json':
                return jsonify({
                    'exito': True,
                    'resultado_id': resultado.id,
                    'jenkins_build_number': resultado_jenkins.get('build_number'),
                    'id_solicitud': resultado_jenkins.get('id_solicitud'),
                    'mensaje': 'Test enviado a Jenkins correctamente'
                }), 202
            else:
                flash('Test enviado a Jenkins correctamente', 'success')
                return redirect(request.referrer or url_for('casos_prueba_bp.detalle', caso_id=caso_id))
        else:
            error_msg = 'Error al enviar test a Jenkins'
            if request.headers.get('Accept') == 'application/json':
                return jsonify({'error': error_msg}), 500
            else:
                flash(error_msg, 'danger')
                return redirect(request.referrer or url_for('casos_prueba_bp.detalle', caso_id=caso_id))

    except Exception as e:
        current_app.logger.error(f"Error ejecutar test: {e}", exc_info=True)
        error_msg = f'Error: {str(e)}'
        if request.headers.get('Accept') == 'application/json':
            return jsonify({'error': error_msg}), 500
        else:
            flash(error_msg, 'danger')
            return redirect(request.referrer or url_for('casos_prueba_bp.detalle', caso_id=caso_id))


@automatizacion_bp.post('/ejecutar/ciclo/jenkins/<int:ciclo_id>')
@requerir_miembro
def ejecutar_ciclo_jenkins(ciclo_id):
    try:
        ciclo = CicloPrueba.query.get_or_404(ciclo_id)

        if not ciclo.casos_prueba:
            error_msg = 'El ciclo no tiene casos de prueba'
            if request.headers.get('Accept') == 'application/json':
                return jsonify({'error': error_msg}), 400
            else:
                flash(error_msg, 'warning')
                return redirect(request.referrer or url_for('ciclos_prueba_bp.detalle', id=ciclo_id))

        jenkins = ServicioJenkins()

        if not jenkins.validar_conexion():
            error_msg = 'No se puede conectar a Jenkins'
            if request.headers.get('Accept') == 'application/json':
                return jsonify({'error': error_msg}), 503
            else:
                flash(error_msg, 'danger')
                return redirect(request.referrer or url_for('ciclos_prueba_bp.detalle', id=ciclo_id))

        resultado_jenkins = jenkins.lanzar_ciclo(ciclo_id=ciclo_id)

        if resultado_jenkins['exito']:
            resultados_ids = []
            for caso in ciclo.casos_prueba:
                resultado = AutomatizacionService.crear_resultado_automatizado(
                    caso_id=caso.id,
                    ciclo_id=ciclo_id,
                    build_number=resultado_jenkins.get('build_number')
                )
                resultados_ids.append(resultado.id)

            if request.headers.get('Accept') == 'application/json':
                return jsonify({
                    'exito': True,
                    'cantidad': resultado_jenkins['cantidad'],
                    'jenkins_build_number': resultado_jenkins.get('build_number'),
                    'id_solicitud': resultado_jenkins.get('id_solicitud'),
                    'resultado_ids': resultados_ids,
                    'mensaje': f"Se enviaron {resultado_jenkins['cantidad']} tests a Jenkins correctamente"
                }), 202
            else:
                flash(f"Se enviaron {resultado_jenkins['cantidad']} tests a Jenkins correctamente", 'success')
                return redirect(request.referrer or url_for('ciclos_prueba_bp.detalle', id=ciclo_id))
        else:
            error_msg = 'Error al enviar tests a Jenkins'
            if request.headers.get('Accept') == 'application/json':
                return jsonify({'error': error_msg}), 500
            else:
                flash(error_msg, 'danger')
                return redirect(request.referrer or url_for('ciclos_prueba_bp.detalle', id=ciclo_id))

    except Exception as e:
        current_app.logger.error(f"Error ejecutar ciclo: {e}", exc_info=True)
        error_msg = f'Error: {str(e)}'
        if request.headers.get('Accept') == 'application/json':
            return jsonify({'error': error_msg}), 500
        else:
            flash(error_msg, 'danger')
            return redirect(request.referrer or url_for('ciclos_prueba_bp.detalle', id=ciclo_id))


@automatizacion_bp.get('/estado/<int:resultado_id>')
@requerir_autenticacion
def obtener_estado_ejecucion(resultado_id):
    try:
        estado = AutomatizacionService.obtener_estado_ejecucion_jenkins(resultado_id)

        jenkins = ServicioJenkins()
        if estado['jenkins_build_number'] and estado['estado_ejecucion'] == 'pendiente':
            build_status = jenkins.obtener_build_status(estado['jenkins_build_number'])
            if build_status:
                estado['jenkins_status'] = build_status

        return jsonify(estado), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        current_app.logger.error(f"Error obteniendo estado: {e}", exc_info=True)
        return jsonify({'error': 'Error interno'}), 500


@automatizacion_bp.post('/cancelar/<int:resultado_id>')
@requerir_miembro
def cancelar_ejecucion(resultado_id):
    try:
        from app.modelos import Resultado
        resultado = Resultado.query.get_or_404(resultado_id)

        if resultado.modo_ejecucion.value != 'automatizado':
            return jsonify({'error': 'Solo se pueden cancelar ejecuciones automatizadas'}), 400

        if resultado.jenkins_build_number:
            jenkins = ServicioJenkins()
            cancelado = jenkins.cancelar_build(resultado.jenkins_build_number)

            if cancelado:
                resultado.estado_ejecucion = EstadoEjecucionEnum.ERROR
                db.session.commit()
                return jsonify({
                    'exito': True,
                    'mensaje': f'Build #{resultado.jenkins_build_number} cancelado'
                }), 200

        return jsonify({
            'exito': False,
            'error': 'No hay build activo para cancelar'
        }), 400

    except Exception as e:
        current_app.logger.error(f"Error cancelando ejecución: {e}", exc_info=True)
        return jsonify({'error': 'Error interno'}), 500


@automatizacion_bp.post('/reintentar/<int:resultado_id>')
@requerir_miembro
def reintentar_ejecucion(resultado_id):
    try:
        resultado_info = AutomatizacionService.reintentar_ejecucion(resultado_id)

        return jsonify({
            'exito': True,
            'numero_intento': resultado_info['numero_intento'],
            'mensaje': f"Reintento #{resultado_info['numero_intento']} programado"
        }), 202
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error reintentando: {e}", exc_info=True)
        return jsonify({'error': 'Error interno'}), 500


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

        # Actualizar estado_ejecucion a completado
        resultado.estado_ejecucion = EstadoEjecucionEnum.COMPLETADO
        resultado.tiempo_fin_jenkins = __import__('datetime').datetime.utcnow()

        db.session.commit()

        return {'estado': 'OK', 'resultado_id': resultado.id}, 200

    except ValueError as e:
        current_app.logger.error(f"Error validación callback: {e}")
        return {'error': str(e)}, 400
    except Exception as e:
        current_app.logger.error(f"Error inesperado callback: {e}", exc_info=True)
        return {'error': 'Error interno'}, 500
