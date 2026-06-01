import os
from pathlib import Path


def obtener_ruta_certificado() -> str | None:
    proyecto_raiz = Path(__file__).parent.parent
    ruta_certificado = proyecto_raiz / "certificado.cer"

    if ruta_certificado.exists():
        return str(ruta_certificado)
    return None


def obtener_verificacion_ssl() -> str | bool:
    ruta = obtener_ruta_certificado()
    if ruta:
        return ruta
    return True
