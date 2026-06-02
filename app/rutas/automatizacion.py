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

        ciclo_id = request.args.get('ciclo_id', type=int)
        if not ciclo_id and request.is_json:
            datos_peticion = request.get_json(silent=True) or {}
            ciclo_id = datos_peticion.get('ciclo_id')

        resultado_jenkins = jenkins.lanzar_test(
            caso_id=caso_id,
            script_test=caso.script_prueba,
            ciclo_id=ciclo_id,
        )

        if resultado_jenkins['exito']:
            id_solicitud = resultado_jenkins.get('id_solicitud')
            resultado = AutomatizacionService.crear_resultado_automatizado(
                caso_id=caso_id,
                ciclo_id=ciclo_id,
                build_number=resultado_jenkins.get('build_number'),
                id_solicitud=f"{id_solicitud}:{caso_id}" if id_solicitud else None,
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
            id_solicitud_ciclo = resultado_jenkins.get('id_solicitud')
            ejecucion_ciclo = AutomatizacionService.crear_ejecucion_ciclo(
                ciclo_id=ciclo_id,
                build_number=resultado_jenkins.get('build_number'),
                id_solicitud=id_solicitud_ciclo
            )
            
            resultados_mapeados = []
            casos_a_ejecutar = [c for c in ciclo.casos_prueba if c.tiene_script_valido()]
            for caso in casos_a_ejecutar:
                resultado = AutomatizacionService.crear_resultado_automatizado(
                    caso_id=caso.id,
                    ciclo_id=ciclo_id,
                    build_number=resultado_jenkins.get('build_number'),
                    id_solicitud=f"{id_solicitud_ciclo}:{caso.id}" if id_solicitud_ciclo else None,
                )
                resultados_mapeados.append({
                    'caso_id': caso.id,
                    'resultado_id': resultado.id
                })

            if request.headers.get('Accept') == 'application/json':
                return jsonify({
                    'exito': True,
                    'cantidad': resultado_jenkins['cantidad'],
                    'jenkins_build_number': resultado_jenkins.get('build_number'),
                    'id_solicitud': resultado_jenkins.get('id_solicitud'),
                    'ejecucion_ciclo_id': ejecucion_ciclo.id,
                    'resultados': resultados_mapeados,
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


@automatizacion_bp.get('/estados')
@requerir_autenticacion
def obtener_estados_lote():
    try:
        ids_crudo = request.args.get('ids', '')
        if not ids_crudo:
            return jsonify({}), 200

        ids = []
        for elemento in ids_crudo.split(','):
            elemento_limpio = elemento.strip()
            if elemento_limpio.isdigit():
                ids.append(int(elemento_limpio))

        estados = {}
        for id_resultado in ids:
            try:
                estado = AutomatizacionService.obtener_estado_ejecucion_jenkins(id_resultado)
                if estado['jenkins_build_number'] and estado['estado_ejecucion'] == 'pendiente':
                    try:
                        jenkins = ServicioJenkins()
                        estado_construccion = jenkins.obtener_build_status(estado['jenkins_build_number'])
                        if estado_construccion:
                            estado['jenkins_status'] = estado_construccion
                    except Exception:
                        pass
                estados[id_resultado] = estado
            except ValueError:
                pass
            except Exception as e:
                current_app.logger.error(f"Error obteniendo estado de lote para ID {id_resultado}: {e}")

        return jsonify(estados), 200

    except Exception as e:
        current_app.logger.error(f"Error en endpoint de estados por lote: {e}", exc_info=True)
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

        resultado.estado_ejecucion = EstadoEjecucionEnum.COMPLETADO
        resultado.tiempo_fin_jenkins = __import__('datetime').datetime.utcnow()

        if resultado.tiempo_inicio_jenkins and resultado.tiempo_fin_jenkins:
            diferencia_tiempo = resultado.tiempo_fin_jenkins - resultado.tiempo_inicio_jenkins
            resultado.tiempo_ejecucion = diferencia_tiempo.total_seconds()

        if resultado.jenkins_build_number:
            try:
                jenkins = ServicioJenkins()
                logs = jenkins.obtener_build_log(resultado.jenkins_build_number)
                resultado.output_jenkins = logs if logs else "No se recibieron logs de la consola de Jenkins."
            except Exception as error_log:
                current_app.logger.error(f"Error al descargar logs de Jenkins para el build #{resultado.jenkins_build_number}: {error_log}")
                resultado.output_jenkins = f"Error al descargar logs de Jenkins: {str(error_log)}"

        db.session.commit()

        if resultado.ciclo_prueba_id:
            from app.modelos import EjecucionCiclo
            ejecucion_ciclo = EjecucionCiclo.query.filter_by(
                ciclo_prueba_id=resultado.ciclo_prueba_id
            ).order_by(EjecucionCiclo.fecha_ejecucion.desc()).first()
            if ejecucion_ciclo:
                try:
                    AutomatizacionService.actualizar_ejecucion_ciclo(ejecucion_ciclo.id)
                except Exception as e:
                    current_app.logger.error(f"Error actualizando ejecución de ciclo: {e}")

        return {'status': 'ok'}, 200

    except ValueError as e:
        current_app.logger.error(f"Error validación callback: {e}")
        return {'error': str(e)}, 400
    except Exception as e:
        current_app.logger.error(f"Error inesperado callback: {e}", exc_info=True)
        return {'error': 'Error interno'}, 500


@automatizacion_bp.get('/ciclo/<int:ciclo_id>/resumen')
@requerir_autenticacion
def obtener_resumen_ciclo(ciclo_id):
    try:
        solicitud_id = request.args.get('solicitud_id', '').strip() or None
        resumen = AutomatizacionService.obtener_resumen_ejecucion_ciclo(ciclo_id, solicitud_id)
        return jsonify(resumen), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        current_app.logger.error(f"Error obteniendo resumen de ciclo: {e}", exc_info=True)
        return jsonify({'error': 'Error interno'}), 500


@automatizacion_bp.get('/logs/<int:resultado_id>')
@requerir_autenticacion
def obtener_logs(resultado_id):
    try:
        from app.modelos import Resultado
        resultado = Resultado.query.get_or_404(resultado_id)

        return jsonify({
            'resultado_id': resultado.id,
            'output_jenkins': resultado.output_jenkins or '',
            'jenkins_build_number': resultado.jenkins_build_number,
            'jenkins_log_url': resultado.jenkins_log_url,
            'tiempo_inicio': resultado.tiempo_inicio_jenkins.isoformat() if resultado.tiempo_inicio_jenkins else None,
            'tiempo_fin': resultado.tiempo_fin_jenkins.isoformat() if resultado.tiempo_fin_jenkins else None,
        }), 200


    except Exception as e:
        current_app.logger.error(f"Error obteniendo logs: {e}", exc_info=True)
        return jsonify({'error': 'Error interno'}), 500


@automatizacion_bp.get('/api/casos/<int:caso_id>/script')
def obtener_script_caso(caso_id):
    try:
        caso = CasoPrueba.query.get_or_404(caso_id)
        return jsonify({
            'caso_id': caso.id,
            'nombre': caso.nombre,
            'script_prueba': caso.script_prueba or ''
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error obteniendo script del caso {caso_id}: {e}", exc_info=True)
        return jsonify({'error': 'Error interno'}), 500
