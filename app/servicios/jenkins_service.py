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
                   ciclo_id: int = None) -> dict:
        id_solicitud = str(uuid.uuid4())

        carga = {
            'TEST_CASE_ID': str(caso_id),
            'TEST_SCRIPT': script_test or '',
            'REQUEST_ID': id_solicitud,
        }

        if ciclo_id:
            carga['TEST_CYCLE_ID'] = str(ciclo_id)

        build_number = self._construir_con_parametros_retornando_build(carga)
        return {
            'exito': build_number is not None,
            'build_number': build_number,
            'id_solicitud': id_solicitud
        }

    def lanzar_ciclo(self, ciclo_id: int) -> dict:
        from app.modelos import CicloPrueba

        ciclo = CicloPrueba.query.get(ciclo_id)
        if not ciclo:
            raise ValueError(f"Ciclo {ciclo_id} no existe")

        ids_test = [str(tc.id) for tc in ciclo.casos_prueba]
        if not ids_test:
            return {
                'exito': False,
                'cantidad': 0,
                'builds': []
            }

        id_solicitud = str(uuid.uuid4())

        carga = {
            'TEST_CASE_IDS': '[' + ','.join(ids_test) + ']',
            'TEST_CYCLE_ID': str(ciclo_id),
            'REQUEST_ID': id_solicitud,
        }

        build_number = self._construir_con_parametros_retornando_build(carga)
        return {
            'exito': build_number is not None,
            'cantidad': len(ids_test) if build_number else 0,
            'build_number': build_number,
            'id_solicitud': id_solicitud,
            'builds': [build_number] if build_number else []
        }

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

    def _construir_con_parametros_retornando_build(self, carga: dict) -> int:
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
                timeout=self.configuracion['tiempo_espera'],
                allow_redirects=False
            )

            if respuesta.status_code in (200, 201, 202, 302):
                # Jenkins devuelve el queue location en el header Location
                queue_location = respuesta.headers.get('Location')
                if queue_location:
                    import re
                    # Intentar extraer el número de build del queue
                    # Esperar a que Jenkins procese la queue
                    import time
                    time.sleep(1)
                    # Intentar obtener el build más reciente
                    build_number = self._obtener_build_reciente()
                    if build_number:
                        current_app.logger.info(f"Build #{build_number} disparado exitosamente")
                        return build_number

                current_app.logger.warning(f"No se pudo extraer build number de: {queue_location}")
                return None
            else:
                current_app.logger.error(f"Fallo disparando build: {respuesta.status_code}")
                return None

        except Exception as e:
            current_app.logger.error(f"Fallo en _construir_con_parametros_retornando_build: {e}")
            return None

    def _obtener_build_reciente(self) -> int:
        try:
            url_job = f"{self.configuracion['url']}/job/{self.configuracion['job']}/api/json"
            respuesta = self.sesion.get(
                url_job,
                timeout=self.configuracion['tiempo_espera']
            )

            if respuesta.status_code == 200:
                datos = respuesta.json()
                builds = datos.get('builds', [])
                if builds:
                    build_number = builds[0].get('number')
                    return build_number
            return None
        except Exception as e:
            current_app.logger.error(f"Fallo obteniendo build reciente: {e}")
            return None

    def obtener_build_status(self, build_number: int) -> dict:
        try:
            url_build = f"{self.configuracion['url']}/job/{self.configuracion['job']}/{build_number}/api/json"
            respuesta = self.sesion.get(
                url_build,
                timeout=self.configuracion['tiempo_espera']
            )

            if respuesta.status_code == 200:
                datos = respuesta.json()
                return {
                    'building': datos.get('building', False),
                    'result': datos.get('result'),  # SUCCESS, FAILURE, ABORTED, etc
                    'timestamp': datos.get('timestamp'),
                    'duration': datos.get('duration'),
                    'estimated_duration': datos.get('estimatedDuration'),
                    'url': datos.get('url'),
                    'display_name': datos.get('displayName'),
                }
            else:
                current_app.logger.warning(f"No se pudo obtener status del build {build_number}: {respuesta.status_code}")
                return None
        except Exception as e:
            current_app.logger.error(f"Fallo obteniendo build status: {e}")
            return None

    def obtener_build_log(self, build_number: int, tail: int = 100) -> str:
        try:
            url_log = f"{self.configuracion['url']}/job/{self.configuracion['job']}/{build_number}/consoleText"
            respuesta = self.sesion.get(
                url_log,
                timeout=self.configuracion['tiempo_espera'],
                params={'start': 0}
            )

            if respuesta.status_code == 200:
                lineas = respuesta.text.split('\n')
                return '\n'.join(lineas[-tail:])
            else:
                current_app.logger.warning(f"No se pudo obtener logs del build {build_number}: {respuesta.status_code}")
                return None
        except Exception as e:
            current_app.logger.error(f"Fallo obteniendo build log: {e}")
            return None

    def cancelar_build(self, build_number: int) -> bool:
        try:
            campo_crumb, valor_crumb = self.obtener_crumb()

            encabezados = {}
            if campo_crumb and valor_crumb:
                encabezados[campo_crumb] = valor_crumb

            url_cancelar = f"{self.configuracion['url']}/job/{self.configuracion['job']}/{build_number}/stop"
            respuesta = self.sesion.post(
                url_cancelar,
                headers=encabezados,
                timeout=self.configuracion['tiempo_espera']
            )

            exito = respuesta.status_code in (200, 201, 302)
            if exito:
                current_app.logger.info(f"Build {build_number} cancelado exitosamente")
            else:
                current_app.logger.warning(f"Fallo cancelando build {build_number}: {respuesta.status_code}")

            return exito
        except Exception as e:
            current_app.logger.error(f"Fallo cancelando build: {e}")
            return False
