from app.modelos import CasoPrueba, CicloPrueba, Resultado, EjecucionCiclo
from app.base_datos import db
from config.constantes import EstadoResultadoEnum, ModoEjecucionEnum, EstadoEjecucionEnum
from flask import current_app
from datetime import datetime
import uuid


class AutomatizacionService:
    @staticmethod
    def _map_estado_resultado(estado_str: str) -> EstadoResultadoEnum:
        estado_map = {
            'PASADO': EstadoResultadoEnum.PASADO,
            'FALLIDO': EstadoResultadoEnum.FALLIDO,
            'EN_PROGRESO': EstadoResultadoEnum.EN_PROGRESO,
        }
        clave = (estado_str or '').upper()
        if clave not in estado_map:
            raise ValueError(f"Estado no válido: {estado_str}")
        return estado_map[clave]

    @staticmethod
    def _fusionar_escenario_en_resultado(resultado: Resultado, datos: dict) -> Resultado:
        nuevo_estado = AutomatizacionService._map_estado_resultado(
            datos.get('estado_prueba', '')
        )
        escenario = (datos.get('resultado_obtenido') or '').strip()
        notas_nuevas = (datos.get('notes', '') or datos.get('notas', '') or '').strip()

        if escenario:
            if resultado.resultado_obtenido and escenario not in resultado.resultado_obtenido:
                resultado.resultado_obtenido = f"{resultado.resultado_obtenido} | {escenario}"
            elif not resultado.resultado_obtenido:
                resultado.resultado_obtenido = escenario

        if notas_nuevas:
            separador = '\n\n---\n\n' if resultado.notas else ''
            if notas_nuevas not in (resultado.notas or ''):
                resultado.notas = f"{resultado.notas or ''}{separador}{notas_nuevas}"

        if nuevo_estado == EstadoResultadoEnum.FALLIDO:
            resultado.estado = EstadoResultadoEnum.FALLIDO
        elif resultado.estado != EstadoResultadoEnum.FALLIDO:
            resultado.estado = nuevo_estado

        if datos.get('jenkins_build_number'):
            resultado.jenkins_build_number = datos.get('jenkins_build_number')
        if datos.get('jenkins_log_url'):
            resultado.jenkins_log_url = datos.get('jenkins_log_url')

        resultado.json_respuesta_jenkins = datos
        resultado.tiempo_fin_jenkins = datetime.utcnow()
        db.session.commit()
        return resultado

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
            if not existente and ':' not in str(id_solicitud):
                existente = Resultado.query.filter_by(
                    id_solicitud=f"{id_solicitud}:{caso_id}"
                ).first()
            if not existente and ciclo_id:
                existente = (
                    Resultado.query.filter_by(
                        caso_prueba_id=caso_id,
                        ciclo_prueba_id=ciclo_id,
                        estado_ejecucion=EstadoEjecucionEnum.PENDIENTE,
                    )
                    .order_by(Resultado.id.desc())
                    .first()
                )
            if existente:
                if existente.estado_ejecucion in (EstadoEjecucionEnum.COMPLETADO, EstadoEjecucionEnum.ERROR):
                    return AutomatizacionService._fusionar_escenario_en_resultado(existente, datos)

                current_app.logger.info(f"Actualizando resultado pendiente para id_solicitud: {id_solicitud}")

                existente.estado = AutomatizacionService._map_estado_resultado(
                    datos.get('estado_prueba', '')
                )
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
                existente.estado_ejecucion = EstadoEjecucionEnum.COMPLETADO
                db.session.commit()
                return existente

        estado_enum = AutomatizacionService._map_estado_resultado(datos.get('estado_prueba', ''))

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
            estado=estado_enum,
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
            f"estado={estado_enum.value}, ciclo={ciclo_id}, id_solicitud={id_solicitud}"
        )

        return resultado

    @staticmethod
    def obtener_resumen_ejecucion_ciclo(ciclo_id: int, solicitud_id: str = None) -> dict:
        ciclo = AutomatizacionService.validar_ciclo_prueba(ciclo_id)
        
        resultados_por_caso = {}
        for resultado in ciclo.resultados:
            caso_id = resultado.caso_prueba_id
            if caso_id not in resultados_por_caso or resultado.fecha_creacion > resultados_por_caso[caso_id].fecha_creacion:
                resultados_por_caso[caso_id] = resultado
        
        casos_con_resultado_auto = {}
        for caso_id, resultado in resultados_por_caso.items():
            if resultado.modo_ejecucion == ModoEjecucionEnum.AUTOMATIZADO:
                casos_con_resultado_auto[caso_id] = resultado
        
        if not casos_con_resultado_auto:
            return {
                'ciclo_id': ciclo_id,
                'ciclo_nombre': ciclo.nombre,
                'casos': [],
                'resumen': {'pasados': 0, 'fallidos': 0, 'total': 0},
                'log_completo': '',
            }
        
        if solicitud_id:
            casos_con_resultado_auto = {
                caso_id: resultado for caso_id, resultado in casos_con_resultado_auto.items()
                if resultado.id_solicitud and resultado.id_solicitud.startswith(f"{solicitud_id}:")
            }
        else:
            ultimo = max(casos_con_resultado_auto.values(), key=lambda r: r.fecha_creacion)
            if not ultimo.id_solicitud or ':' not in ultimo.id_solicitud:
                return {
                    'ciclo_id': ciclo_id,
                    'ciclo_nombre': ciclo.nombre,
                    'casos': [],
                    'resumen': {'pasados': 0, 'fallidos': 0, 'total': 0},
                    'log_completo': '',
                }
            base_solicitud = ultimo.id_solicitud.split(':', 1)[0]
            casos_con_resultado_auto = {
                caso_id: resultado for caso_id, resultado in casos_con_resultado_auto.items()
                if resultado.id_solicitud and resultado.id_solicitud.startswith(f"{base_solicitud}:")
            }
        
        resultados = sorted(casos_con_resultado_auto.values(), key=lambda r: r.caso_prueba_id)
        casos = []
        pasados = 0
        fallidos = 0
        bloques_log = []
        build_number = None
        log_url = None

        for resultado in resultados:
            estado_valor = resultado.estado.value if resultado.estado else 'desconocido'
            if resultado.estado == EstadoResultadoEnum.PASADO:
                pasados += 1
            elif resultado.estado == EstadoResultadoEnum.FALLIDO:
                fallidos += 1

            if resultado.jenkins_build_number and not build_number:
                build_number = resultado.jenkins_build_number
            if resultado.jenkins_log_url and not log_url:
                log_url = resultado.jenkins_log_url

            nombre_caso = resultado.caso_prueba.nombre if resultado.caso_prueba else f"Caso {resultado.caso_prueba_id}"
            casos.append({
                'resultado_id': resultado.id,
                'caso_id': resultado.caso_prueba_id,
                'caso_nombre': nombre_caso,
                'estado': estado_valor,
                'estado_ejecucion': resultado.estado_ejecucion.value if resultado.estado_ejecucion else None,
                'resultado_obtenido': resultado.resultado_obtenido or '',
                'notas': resultado.notas or '',
            })
            bloques_log.append(
                f"=== {nombre_caso} ({estado_valor.upper()}) ===\n"
                f"{resultado.notas or 'Sin notas'}"
            )

        log_jenkins = ''
        for resultado in resultados:
            if resultado.output_jenkins:
                log_jenkins = resultado.output_jenkins
                break

        log_completo = '\n\n'.join(bloques_log)
        if log_jenkins:
            log_completo = f"--- Consola Jenkins (build #{build_number or '?'}) ---\n{log_jenkins}\n\n--- Detalle por caso ---\n\n{log_completo}"

        duracion_total = 0
        fecha_ejecucion = None
        if resultados:
            fechas_inicio = [r.tiempo_inicio_jenkins for r in resultados if r.tiempo_inicio_jenkins]
            fechas_fin = [r.tiempo_fin_jenkins for r in resultados if r.tiempo_fin_jenkins]
            if fechas_inicio and fechas_fin:
                fecha_ejecucion = min(fechas_inicio)
                fecha_fin = max(fechas_fin)
                duracion_total = (fecha_fin - fecha_ejecucion).total_seconds()
            elif resultados[0].fecha_creacion:
                fecha_ejecucion = resultados[0].fecha_creacion

        return {
            'ciclo_id': ciclo_id,
            'ciclo_nombre': ciclo.nombre,
            'id_solicitud': solicitud_id or (resultados[0].id_solicitud.split(':', 1)[0] if resultados and resultados[0].id_solicitud and ':' in resultados[0].id_solicitud else None),
            'jenkins_build_number': build_number,
            'jenkins_log_url': log_url,
            'casos': casos,
            'resumen': {
                'pasados': pasados,
                'fallidos': fallidos,
                'total': len(casos),
            },
            'log_completo': log_completo,
            'detalles': {
                'build_number': build_number,
                'fecha_ejecucion': fecha_ejecucion.isoformat() if fecha_ejecucion else None,
                'duracion_total': duracion_total if duracion_total > 0 else None,
                'estado_ejecucion': 'completado' if resultados and all(r.estado_ejecucion == EstadoEjecucionEnum.COMPLETADO for r in resultados if r.estado_ejecucion) else 'en_progreso',
                'jenkins_url': log_url,
            },
        }

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
            tiempo_ejecucion = delta.total_seconds()

        return {
            'resultado_id': resultado.id,
            'caso_id': resultado.caso_prueba_id,
            'caso_nombre': resultado.caso_prueba.nombre if resultado.caso_prueba else None,
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
            'resultado_obtenido': resultado.resultado_obtenido or '',
            'notas': resultado.notas or '',
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

    @staticmethod
    def crear_ejecucion_ciclo(ciclo_id: int, build_number: int = None, id_solicitud: str = None) -> EjecucionCiclo:
        ciclo = AutomatizacionService.validar_ciclo_prueba(ciclo_id)
        
        ejecucion = EjecucionCiclo(
            ciclo_prueba_id=ciclo_id,
            fecha_ejecucion=datetime.utcnow(),
            total_pruebas=len(ciclo.casos_prueba),
            pruebas_pasadas=0,
            pruebas_fallidas=0,
            pruebas_en_progreso=0,
            estado_ejecucion=EstadoEjecucionEnum.EN_PROGRESO,
            jenkins_build_number=build_number,
            id_solicitud=id_solicitud,
        )
        
        db.session.add(ejecucion)
        db.session.commit()
        
        current_app.logger.info(
            f"Ejecución de ciclo creada: ciclo={ciclo_id}, build={build_number}, id_solicitud={id_solicitud}"
        )
        
        return ejecucion

    @staticmethod
    def actualizar_ejecucion_ciclo(ejecucion_id: int) -> EjecucionCiclo:
        ejecucion = EjecucionCiclo.query.get(ejecucion_id)
        if not ejecucion:
            raise ValueError(f"Ejecución de ciclo {ejecucion_id} no existe")
        
        ciclo = ejecucion.ciclo_prueba
        
        resultados_por_caso = {}
        for resultado in ciclo.resultados:
            caso_id = resultado.caso_prueba_id
            if caso_id not in resultados_por_caso or resultado.fecha_creacion > resultados_por_caso[caso_id].fecha_creacion:
                resultados_por_caso[caso_id] = resultado
        
        pasadas = 0
        fallidas = 0
        en_progreso = 0
        
        for resultado in resultados_por_caso.values():
            if resultado.estado == EstadoResultadoEnum.PASADO:
                pasadas += 1
            elif resultado.estado == EstadoResultadoEnum.FALLIDO:
                fallidas += 1
            elif resultado.estado == EstadoResultadoEnum.EN_PROGRESO:
                en_progreso += 1
        
        ejecucion.pruebas_pasadas = pasadas
        ejecucion.pruebas_fallidas = fallidas
        ejecucion.pruebas_en_progreso = en_progreso
        
        if en_progreso > 0:
            ejecucion.estado_ejecucion = EstadoEjecucionEnum.EN_PROGRESO
        elif fallidas > 0:
            ejecucion.estado_ejecucion = EstadoEjecucionEnum.ERROR
        else:
            ejecucion.estado_ejecucion = EstadoEjecucionEnum.COMPLETADO
        
        db.session.commit()
        
        return ejecucion
