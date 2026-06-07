import json
import os
import sys
import subprocess
import traceback
import uuid
from pathlib import Path


def ejecutar_feature(ruta_feature: str):
    try:
        directorio_base = Path(__file__).parent
        directorio_features = directorio_base / 'features'
        directorio_resultados = directorio_base / 'resultados'
        directorio_resultados.mkdir(exist_ok=True)

        nombre_feature = Path(ruta_feature).name
        ruta_absoluta = (directorio_features / nombre_feature).resolve()

        try:
            ruta_absoluta.relative_to(directorio_features)
        except ValueError:
            raise PermissionError(f"Acceso denegado: {ruta_feature}")

        if not ruta_absoluta.exists():
            raise FileNotFoundError(f"Feature no encontrado: {ruta_absoluta}")

        id_ejecucion = uuid.uuid4().hex[:8]
        ruta_resultado_json = directorio_resultados / f"resultado_{id_ejecucion}.json"

        entorno = os.environ.copy()
        entorno.setdefault('URL_BACKEND', 'http://app:5000')

        proceso = subprocess.run(
            [
                sys.executable, '-m', 'behave',
                str(ruta_absoluta.relative_to(directorio_base)),
                '-f', 'json',
                '-o', str(ruta_resultado_json)
            ],
            cwd=directorio_base,
            env=entorno,
            capture_output=True,
            text=True,
            timeout=300
        )

        if not ruta_resultado_json.exists():
            salida_json = {
                'estado_prueba': 'FALLIDO',
                'resultado_obtenido': 'Behave no generó result.json',
                'notas': f"STDOUT: {proceso.stdout}\nSTDERR: {proceso.stderr}\nReturn Code: {proceso.returncode}",
                'archivo': None
            }
            print(json.dumps(salida_json))
            return

        with open(ruta_resultado_json, 'r', encoding='utf-8') as archivo:
            datos = json.load(archivo)

        if datos and len(datos) > 0:
            caracteristica = datos[0]
            for escenario in caracteristica.get('elements', []):
                pasos = escenario.get('steps', [])
                todos_pasaron = all(
                    p.get('result', {}).get('status') == 'passed'
                    for p in pasos
                )
                estado = 'PASADO' if todos_pasaron else 'FALLIDO'

                lineas_notas = [f"Característica: {caracteristica.get('name', '')}"]
                for p in pasos:
                    estado_paso = p.get('result', {}).get('status', 'OMITIDO')
                    lineas_notas.append(f"{p.get('keyword', '')} {p.get('name', '')} → {estado_paso}")
                    error_msg = p.get('result', {}).get('error_message')
                    if estado_paso == 'failed' and error_msg:
                        lineas_notas.append(f"  Error: {error_msg}")

                salida = {
                    'estado_prueba': estado,
                    'resultado_obtenido': escenario.get('name', ''),
                    'notas': '\n'.join(lineas_notas),
                    'archivo': None
                }
                print(json.dumps(salida))

        try:
            ruta_resultado_json.unlink()
        except:
            pass

    except Exception as e:
        print(json.dumps({
            'estado_prueba': 'FALLIDO',
            'resultado_obtenido': type(e).__name__,
            'notas': str(e),
            'archivo': None
        }))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(json.dumps({
            'estado_prueba': 'FALLIDO',
            'resultado_obtenido': 'Uso: ejecutor.py <ruta_feature>',
            'notas': 'Se requiere la ruta del archivo .feature',
            'archivo': None
        }))
    else:
        ejecutar_feature(sys.argv[1])
