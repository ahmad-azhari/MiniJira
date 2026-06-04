import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.app import crear_app, db
from app.modelos import CasoPrueba, CicloPrueba

app = crear_app()

with app.app_context():
    caso_login = CasoPrueba.query.filter_by(nombre='Login exitoso con credenciales válidas').first()
    
    if not caso_login:
        print('[ERROR] Caso de prueba de login NO encontrado')
        sys.exit(1)
    
    print('[OK] Caso de prueba de login encontrado')
    print(f'   ID: {caso_login.id}')
    print(f'   Nombre: {caso_login.nombre}')
    print(f'   Tipo: {caso_login.tipo.value}')
    print(f'   Script: {"Sí" if caso_login.tiene_script_valido() else "No"}')
    
    ciclo_login = CicloPrueba.query.filter_by(nombre='Ciclo de Pruebas de Login').first()
    
    if not ciclo_login:
        print('[ERROR] Ciclo de prueba de login NO encontrado')
        sys.exit(1)
    
    print('\n[OK] Ciclo de prueba de login encontrado')
    print(f'   ID: {ciclo_login.id}')
    print(f'   Nombre: {ciclo_login.nombre}')
    print(f'   Estado: {ciclo_login.estado.value}')
    print(f'   Casos en el ciclo: {len(ciclo_login.casos_prueba)}')
    
    if caso_login in ciclo_login.casos_prueba:
        print(f'   [OK] Caso de login está en el ciclo')
    else:
        print(f'   [ERROR] Caso de login NO está en el ciclo')
        sys.exit(1)
    
    print('\n[SCRIPT] Script Gherkin del caso:')
    print('-' * 50)
    print(caso_login.script_prueba)
    print('-' * 50)
    
    print('\n[ARCHIVOS] Archivos creados:')
    print('   - scripts/crear_caso_login.py')
    print('   - scripts/crear_ciclo_login.py')
    print('   - test_runner/features/steps/login_steps.py')
    
    print('\n[COMPLETADO] Verificación completada exitosamente')
