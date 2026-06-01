import requests
import uuid
from flask import current_app
from config.jenkins_configuracion import obtener_configuracion_jenkins
from config.ssl_config import obtener_verificacion_ssl


class ServicioJenkins:
    def __init__(self):
        self.configuracion = obtener_configuracion_jenkins()
        self.sesion = self._crear_sesion()
        self._verificacion_ssl = obtener_verificacion_ssl()

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
                timeout=self.configuracion['tiempo_espera'],
                verify=self._verificacion_ssl
            )
            if respuesta.status_code == 200:
                self.crear_job_si_no_existe()
                return True
            return False
        except Exception as e:
            current_app.logger.error(f"Fallo conexión Jenkins: {e}")
            return False

    def crear_job_si_no_existe(self):
        try:
            url_job = f"{self.configuracion['url']}/job/{self.configuracion['job']}/api/json"
            respuesta = self.sesion.get(
                url_job,
                timeout=self.configuracion['tiempo_espera'],
                verify=self._verificacion_ssl
            )
            if respuesta.status_code == 200:
                return

            current_app.logger.info(f"El Job '{self.configuracion['job']}' no existe en Jenkins. Creándolo automáticamente...")

            import os
            from xml.sax.saxutils import escape

            ruta_jenkinsfile = None
            posibles_directorios = [
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                os.path.abspath(os.getcwd()),
                os.path.join(os.path.abspath(os.getcwd()), 'MiniJira')
            ]
            for d in posibles_directorios:
                posible_ruta = os.path.join(d, 'Jenkinsfile')
                if os.path.exists(posible_ruta):
                    ruta_jenkinsfile = posible_ruta
                    break

            if not ruta_jenkinsfile:
                current_app.logger.error("No se encontró el archivo Jenkinsfile en ninguna de las ubicaciones buscadas.")
                return

            with open(ruta_jenkinsfile, 'r', encoding='utf-8') as f:
                contenido_jenkinsfile = f.read()

            contenido_jenkinsfile = contenido_jenkinsfile.replace('http://localhost:5000', 'http://app:5000')
            jenkinsfile_escapado = escape(contenido_jenkinsfile)

            xml_config = f"""<?xml version='1.1' encoding='UTF-8'?>
<flow-definition plugin="workflow-job">
  <description>Pipeline automatizado creado por MiniJira</description>
  <keepDependencies>false</keepDependencies>
  <properties>
    <hudson.model.ParametersDefinitionProperty>
      <parameterDefinitions>
        <hudson.model.StringParameterDefinition>
          <name>TEST_SCRIPT</name>
          <description>Contenido Gherkin (individual)</description>
          <trim>true</trim>
        </hudson.model.StringParameterDefinition>
        <hudson.model.StringParameterDefinition>
          <name>TEST_CASE_ID</name>
          <description>ID del caso de prueba</description>
          <trim>true</trim>
        </hudson.model.StringParameterDefinition>
        <hudson.model.StringParameterDefinition>
          <name>TEST_CASE_IDS</name>
          <description>JSON: [1,2,3] o CSV: 1,2,3</description>
          <trim>true</trim>
        </hudson.model.StringParameterDefinition>
        <hudson.model.StringParameterDefinition>
          <name>TEST_CYCLE_ID</name>
          <description>ID del ciclo (opcional)</description>
          <trim>true</trim>
        </hudson.model.StringParameterDefinition>
        <hudson.model.StringParameterDefinition>
          <name>REQUEST_ID</name>
          <description>ID de solicitud</description>
          <trim>true</trim>
        </hudson.model.StringParameterDefinition>
      </parameterDefinitions>
    </hudson.model.ParametersDefinitionProperty>
  </properties>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps">
    <script>{jenkinsfile_escapado}</script>
    <sandbox>true</sandbox>
  </definition>
  <triggers/>
  <disabled>false</disabled>
</flow-definition>
"""
            campo_crumb, valor_crumb = self.obtener_crumb()
            encabezados = {'Content-Type': 'application/xml'}
            if campo_crumb and valor_crumb:
                encabezados[campo_crumb] = valor_crumb

            url_creacion = f"{self.configuracion['url']}/createItem?name={self.configuracion['job']}"
            r_creacion = self.sesion.post(
                url_creacion,
                data=xml_config.encode('utf-8'),
                headers=encabezados,
                timeout=self.configuracion['tiempo_espera'],
                verify=self._verificacion_ssl
            )

            if r_creacion.status_code in (200, 201):
                current_app.logger.info(f"Job '{self.configuracion['job']}' creado exitosamente en Jenkins!")
            else:
                current_app.logger.error(f"Fallo al crear Job en Jenkins: {r_creacion.status_code} - {r_creacion.text}")

        except Exception as e:
            current_app.logger.error(f"Error en crear_job_si_no_existe: {e}")

    def obtener_crumb(self):
        try:
            respuesta = self.sesion.get(
                f"{self.configuracion['url']}/crumbIssuer/api/json",
                timeout=self.configuracion['tiempo_espera'],
                verify=self._verificacion_ssl
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
                timeout=self.configuracion['tiempo_espera'],
                verify=self._verificacion_ssl
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
                allow_redirects=False,
                verify=self._verificacion_ssl
            )

            if respuesta.status_code in (200, 201, 202, 302):
                queue_location = respuesta.headers.get('Location')
                if queue_location:
                    import time
                    for intento in range(5):
                        time.sleep(1)
                        build_number = self._obtener_build_reciente()
                        if build_number:
                            current_app.logger.info(f"Build #{build_number} disparado exitosamente en intento {intento + 1}")
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
                timeout=self.configuracion['tiempo_espera'],
                verify=self._verificacion_ssl
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
                timeout=self.configuracion['tiempo_espera'],
                verify=self._verificacion_ssl
            )

            if respuesta.status_code == 200:
                datos = respuesta.json()
                return {
                    'building': datos.get('building', False),
                    'result': datos.get('result'),
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
                params={'start': 0},
                verify=self._verificacion_ssl
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
                timeout=self.configuracion['tiempo_espera'],
                verify=self._verificacion_ssl
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
