import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.app import crear_app, db
from app.modelos import CicloPrueba

app = crear_app()

with app.app_context():
    ciclo_login = CicloPrueba.query.filter_by(nombre='Ciclo de Pruebas de Login').first()
    
    if not ciclo_login:
        print('Error: Ciclo de prueba de login no encontrado')
        sys.exit(1)
    
    ciclo_login.nombre = 'Pruebas de Login'
    db.session.commit()
    
    print(f'Ciclo de prueba renombrado')
    print(f'ID: {ciclo_login.id}')
    print(f'Nuevo nombre: {ciclo_login.nombre}')
