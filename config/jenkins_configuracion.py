import os


def obtener_configuracion_jenkins() -> dict:
    configuracion = {
        'url': os.getenv('JENKINS_URL', 'http://localhost:8080'),
        'job': os.getenv('JENKINS_JOB', 'Pipeline'),
        'usuario': os.getenv('JENKINS_USUARIO'),
        'token_api': os.getenv('JENKINS_TOKEN_API') or os.getenv('JENKINS_PASSWORD'),
        'token_construccion': os.getenv('JENKINS_TOKEN_CONSTRUCCION'),
        'tiempo_espera': int(os.getenv('JENKINS_TIEMPO_ESPERA', '30')),
        'ruta_python': os.getenv('JENKINS_RUTA_PYTHON'),
    }

    requeridos = ['usuario', 'token_api', 'token_construccion', 'ruta_python']
    faltantes = [k for k in requeridos if not configuracion.get(k)]

    if faltantes:
        raise ValueError(f"Configuración Jenkins incompleta: {faltantes}")

    return configuracion
