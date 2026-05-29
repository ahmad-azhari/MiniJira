import requests
import uuid
from flask import current_app
from config.jenkins_configuracion import obtener_configuracion_jenkins


class ServicioJenkins:
    def __init__(self):
        self.configuracion = obtener_configuracion_jenkins()
        self.sesion = self._crear_sesion()

    def _crear_sesion(self):
        sesion = requests.Session()
        sesion.auth = (
            self.configuracion['usuario'],
            self.configuracion['token_api']
        )
        return sesion

    def validar_conexion(self) -> bool:
        try:
            respuesta = self.sesion.get(
                f"{self.configuracion['url']}/api/json",
                timeout=self.configuracion['tiempo_espera']
            )
            return respuesta.status_code == 200
        except Exception as e:
            current_app.logger.error(f"Fallo conexión Jenkins: {e}")
            return False

    def obtener_crumb(self):
        try:
            respuesta = self.sesion.get(
                f"{self.configuracion['url']}/crumbIssuer/api/json",
                timeout=self.configuracion['tiempo_espera']
            )
            if respuesta.status_code == 200:
                datos = respuesta.json()
                return datos.get('crumbRequestField'), datos.get('crumb')
            return None, None
        except Exception as e:
            current_app.logger.error(f"Fallo obteniendo crumb: {e}")
            return None, None

    def lanzar_test(self, caso_id: int, script_test: str,
                   ciclo_id: int = None) -> bool:
        id_solicitud = str(uuid.uuid4())

        carga = {
            'TEST_CASE_ID': str(caso_id),
            'TEST_SCRIPT': script_test or '',
            'REQUEST_ID': id_solicitud,
        }

        if ciclo_id:
            carga['TEST_CYCLE_ID'] = str(ciclo_id)

        return self._construir_con_parametros(carga)

    def lanzar_ciclo(self, ciclo_id: int) -> int:
        from app.modelos import CicloPrueba

        ciclo = CicloPrueba.query.get(ciclo_id)
        if not ciclo:
            raise ValueError(f"Ciclo {ciclo_id} no existe")

        ids_test = [str(tc.id) for tc in ciclo.casos_prueba]
        if not ids_test:
            return 0

        id_solicitud = str(uuid.uuid4())

        carga = {
            'TEST_CASE_IDS': '[' + ','.join(ids_test) + ']',
            'TEST_CYCLE_ID': str(ciclo_id),
            'REQUEST_ID': id_solicitud,
        }

        exito = self._construir_con_parametros(carga)
        return len(ids_test) if exito else 0

    def _construir_con_parametros(self, carga: dict) -> bool:
        try:
            campo_crumb, valor_crumb = self.obtener_crumb()

            encabezados = {}
            if campo_crumb and valor_crumb:
                encabezados[campo_crumb] = valor_crumb

            url_construccion = (
                f"{self.configuracion['url']}/job/{self.configuracion['job']}/buildWithParameters"
                f"?token={self.configuracion['token_construccion']}"
            )

            respuesta = self.sesion.post(
                url_construccion,
                data=carga,
                headers=encabezados,
                timeout=self.configuracion['tiempo_espera']
            )

            exito = respuesta.status_code in (200, 201, 202)

            current_app.logger.info(
                f"Solicitud construcción Jenkins: {respuesta.status_code}, carga={carga}"
            )

            return exito

        except Exception as e:
            current_app.logger.error(f"Fallo construcción Jenkins: {e}")
            return False
