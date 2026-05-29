from app.modelos import CasoPrueba, CicloPrueba, Resultado
from app.base_datos import db
from config.constantes import EstadoResultadoEnum
from flask import current_app


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
                current_app.logger.info(f"Solicitud duplicada detectada: {id_solicitud}")
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
