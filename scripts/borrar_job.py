import sys
sys.path.insert(0, '/app')
from run import app
ctx = app.app_context()
ctx.push()
from app.servicios.jenkins_service import ServicioJenkins

j = ServicioJenkins()
crumb_field, crumb_val = j.obtener_crumb()
cabeceras = {}
if crumb_field and crumb_val:
    cabeceras[crumb_field] = crumb_val

url_borrar = f"{j.configuracion['url']}/job/{j.configuracion['job']}/doDelete"
respuesta = j.sesion.post(url_borrar, headers=cabeceras, timeout=15, verify=j._verificacion_ssl)
print(f"Borrado job '{j.configuracion['job']}': HTTP {respuesta.status_code}")

j.crear_job_si_no_existe()
print("Job recreado con Jenkinsfile actualizado.")
