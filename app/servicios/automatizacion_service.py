from app.modelos import CasoPrueba, CicloPrueba, Resultado
from app.base_datos import db
from config.constantes import EstadoResultadoEnum, ModoEjecucionEnum, EstadoEjecucionEnum
from flask import current_app
from datetime import datetime
import uuid


class AutomatizacionService:
    @staticmethod
    def validar_caso_prueba(caso_id: int) -> CasoPrueba:
        caso = CasoPrueba.query.get(caso_id)
        if not caso:
            raise ValueError(f"Caso de prueba {caso_id} no existe")
        return caso

    @staticmethod
    def validar_ciclo_prueba(ciclo_id: int) -> CicloPrueba:
        ciclo = CicloPrueba.query.get(ciclo_id)
        if not ciclo:
            raise ValueError(f"Ciclo de prueba {ciclo_id} no existe")
        return ciclo

    @staticmethod
    def procesar_resultado_jenkins(caso_id: int, datos: dict) -> Resultado:
        caso = AutomatizacionService.validar_caso_prueba(caso_id)

        ciclo_id = datos.get('ciclo_prueba_id')
        if ciclo_id:
            ciclo = AutomatizacionService.validar_ciclo_prueba(ciclo_id)
            if caso not in ciclo.casos_prueba:
                raise ValueError(f"Caso {caso_id} no pertenece al ciclo {ciclo_id}")

        id_solicitud = datos.get('id_solicitud')
        if id_solicitud:
            existente = Resultado.query.filter_by(id_solicitud=id_solicitud).first()
            if existente:
                if existente.estado_ejecucion in (EstadoEjecucionEnum.COMPLETADO, EstadoEjecucionEnum.ERROR):
                    current_app.logger.info(f"Solicitud duplicada detectada: {id_solicitud}")
                    return existente

                current_app.logger.info(f"Actualizando resultado pendiente para id_solicitud: {id_solicitud}")

                estado_str = datos.get('estado_prueba', '').upper()
                estado_map = {
                    'PASADO': EstadoResultadoEnum.PASADO,
                    'FALLIDO': EstadoResultadoEnum.FALLIDO,
                    'BLOQUEADO': EstadoResultadoEnum.BLOQUEADO,
                    'EN_PROGRESO': EstadoResultadoEnum.EN_PROGRESO,
                }

                if estado_str not in estado_map:
                    raise ValueError(f"Estado no válido: {estado_str}")

                existente.estado = estado_map[estado_str]
                existente.resultado_obtenido = datos.get('resultado_obtenido', '')
                existente.notas = datos.get('notes', '') or datos.get('notas', '')
                if datos.get('archivo'):
                    existente.archivo_adjunto = datos.get('archivo')
                if datos.get('jenkins_build_number'):
                    existente.jenkins_build_number = datos.get('jenkins_build_number')
                if datos.get('jenkins_log_url'):
                    existente.jenkins_log_url = datos.get('jenkins_log_url')

                tiempo_inicio_crudo = datos.get('tiempo_inicio_jenkins')
                if tiempo_inicio_crudo:
                    try:
                        existente.tiempo_inicio_jenkins = datetime.utcfromtimestamp(float(tiempo_inicio_crudo) / 1000.0)
                    except Exception:
                        pass

                existente.tiempo_fin_jenkins = datetime.utcnow()

                if existente.tiempo_inicio_jenkins and existente.tiempo_fin_jenkins:
                    diferencia_tiempo = existente.tiempo_fin_jenkins - existente.tiempo_inicio_jenkins
                    existente.tiempo_ejecucion = int(diferencia_tiempo.total_seconds())

                if datos.get('numero_intentos'):
                    existente.numero_intentos = datos.get('numero_intentos')

                existente.json_respuesta_jenkins = datos
                db.session.commit()
                return existente

        estado_str = datos.get('estado_prueba', '').upper()
        estado_map = {
            'PASADO': EstadoResultadoEnum.PASADO,
            'FALLIDO': EstadoResultadoEnum.FALLIDO,
            'BLOQUEADO': EstadoResultadoEnum.BLOQUEADO,
            'EN_PROGRESO': EstadoResultadoEnum.EN_PROGRESO,
        }

        if estado_str not in estado_map:
            raise ValueError(f"Estado no válido: {estado_str}")

        tiempo_inicio_crudo = datos.get('tiempo_inicio_jenkins')
        fecha_inicio = None
        if tiempo_inicio_crudo:
            try:
                fecha_inicio = datetime.utcfromtimestamp(float(tiempo_inicio_crudo) / 1000.0)
            except Exception:
                pass

        tiempo_fin_crudo = datos.get('tiempo_fin_jenkins')
        fecha_fin = None
        if tiempo_fin_crudo:
            try:
                fecha_fin = datetime.utcfromtimestamp(float(tiempo_fin_crudo) / 1000.0)
            except Exception:
                pass
        else:
            fecha_fin = datetime.utcnow()

        segundos_ejecucion = None
        if fecha_inicio and fecha_fin:
            segundos_ejecucion = int((fecha_fin - fecha_inicio).total_seconds())

        resultado = Resultado(
            caso_prueba_id=caso_id,
            ciclo_prueba_id=ciclo_id,
            estado=estado_map[estado_str],
            entorno=datos.get('entorno', 'Automatizado'),
            resultado_obtenido=datos.get('resultado_obtenido', ''),
            notas=datos.get('notas', ''),
            archivo_adjunto=datos.get('archivo'),
            id_solicitud=id_solicitud,
            usuario_creacion_id=None,
            modo_ejecucion=ModoEjecucionEnum.AUTOMATIZADO,
            estado_ejecucion=EstadoEjecucionEnum.COMPLETADO,
            jenkins_build_number=datos.get('jenkins_build_number'),
            jenkins_log_url=datos.get('jenkins_log_url'),
            tiempo_inicio_jenkins=fecha_inicio,
            tiempo_fin_jenkins=fecha_fin,
            tiempo_ejecucion=segundos_ejecucion,
            numero_intentos=datos.get('numero_intentos', 1),
            json_respuesta_jenkins=datos,
        )

        db.session.add(resultado)
        db.session.commit()

        current_app.logger.info(
            f"Resultado procesado: caso={caso_id}, "
            f"estado={estado_str}, ciclo={ciclo_id}, id_solicitud={id_solicitud}"
        )

        return resultado

    @staticmethod
    def obtener_casos_ciclo(ciclo_id: int) -> list:
        ciclo = AutomatizacionService.validar_ciclo_prueba(ciclo_id)
        return ciclo.casos_prueba if ciclo else []

    @staticmethod
    def obtener_estado_ejecucion_jenkins(resultado_id: int) -> dict:
        resultado = Resultado.query.get(resultado_id)
        if not resultado:
            raise ValueError(f"Resultado {resultado_id} no existe")

        tiempo_ejecucion = resultado.tiempo_ejecucion
        if tiempo_ejecucion is None and resultado.tiempo_inicio_jenkins and resultado.tiempo_fin_jenkins:
            delta = resultado.tiempo_fin_jenkins - resultado.tiempo_inicio_jenkins
            tiempo_ejecucion = int(delta.total_seconds())

        return {
            'resultado_id': resultado.id,
            'estado_ejecucion': resultado.estado_ejecucion.value if resultado.estado_ejecucion else None,
            'estado_resultado': resultado.estado.value if resultado.estado else None,
            'modo_ejecucion': resultado.modo_ejecucion.value if resultado.modo_ejecucion else None,
            'jenkins_build_number': resultado.jenkins_build_number,
            'jenkins_log_url': resultado.jenkins_log_url,
            'tiempo_inicio': resultado.tiempo_inicio_jenkins.isoformat() if resultado.tiempo_inicio_jenkins else None,
            'tiempo_fin': resultado.tiempo_fin_jenkins.isoformat() if resultado.tiempo_fin_jenkins else None,
            'tiempo_ejecucion': tiempo_ejecucion,
            'numero_intentos': resultado.numero_intentos,
            'fecha_creacion': resultado.fecha_creacion.isoformat(),
            'resultado_obtenido': resultado.resultado_obtenido[:100] if resultado.resultado_obtenido else None,
        }

    @staticmethod
    def reintentar_ejecucion(resultado_id: int) -> dict:
        resultado = Resultado.query.get(resultado_id)
        if not resultado:
            raise ValueError(f"Resultado {resultado_id} no existe")

        if resultado.modo_ejecucion != ModoEjecucionEnum.AUTOMATIZADO:
            raise ValueError(f"Solo se pueden reintentar ejecuciones automatizadas")

        if resultado.estado != EstadoResultadoEnum.FALLIDO:
            current_app.logger.warning(f"Se intenta reintentar resultado que no falló: {resultado_id}")

        resultado.numero_intentos += 1
        resultado.estado_ejecucion = EstadoEjecucionEnum.PENDIENTE
        resultado.tiempo_inicio_jenkins = datetime.utcnow()
        resultado.tiempo_fin_jenkins = None

        db.session.commit()

        current_app.logger.info(f"Reintento #{resultado.numero_intentos} para resultado {resultado_id}")

        return {
            'exito': True,
            'numero_intento': resultado.numero_intentos,
            'resultado_id': resultado.id
        }

    @staticmethod
    def crear_resultado_automatizado(caso_id: int, ciclo_id: int = None,
                                     build_number: int = None, id_solicitud: str = None) -> Resultado:
        caso = AutomatizacionService.validar_caso_prueba(caso_id)

        if ciclo_id:
            ciclo = AutomatizacionService.validar_ciclo_prueba(ciclo_id)
            if caso not in ciclo.casos_prueba:
                raise ValueError(f"Caso {caso_id} no pertenece al ciclo {ciclo_id}")

        if not id_solicitud:
            id_solicitud = str(uuid.uuid4())

        resultado = Resultado(
            caso_prueba_id=caso_id,
            ciclo_prueba_id=ciclo_id,
            estado=EstadoResultadoEnum.EN_PROGRESO,
            entorno='Automatizado',
            modo_ejecucion=ModoEjecucionEnum.AUTOMATIZADO,
            estado_ejecucion=EstadoEjecucionEnum.PENDIENTE,
            jenkins_build_number=build_number,
            id_solicitud=id_solicitud,
            numero_intentos=1,
            tiempo_inicio_jenkins=datetime.utcnow(),
        )

        db.session.add(resultado)
        db.session.commit()

        current_app.logger.info(
            f"Resultado automatizado creado: caso={caso_id}, ciclo={ciclo_id}, "
            f"build={build_number}, id_solicitud={id_solicitud}"
        )

        return resultado
