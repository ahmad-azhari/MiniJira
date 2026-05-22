@echo off
setlocal enabledelayedexpansion

REM Cambiar al directorio del proyecto
cd /d "%~dp0"

REM Verificar si el venv existe
if not exist "venv" (
    echo Creando entorno virtual...
    python -m venv venv
)

REM Activar venv
call venv\Scripts\activate.bat

REM Instalar dependencias
pip install -r requirements.txt > nul 2>&1

REM Ejecutar script de inicialización
python scripts/inicializar_bd.py

pause
