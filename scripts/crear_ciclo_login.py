import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.app import crear_app, db
from app.modelos import CasoPrueba, Usuario, CicloPrueba, Proyecto
from config.constantes import EstadoEnum

app = crear_app()

with app.app_context():
    admin = Usuario.query.filter_by(nombre_usuario='admin').first()
    
    if not admin:
        print('Error: Usuario admin no encontrado')
        sys.exit(1)
    
    proyecto = Proyecto.query.first()
    
    if not proyecto:
        proyecto = Proyecto(
            nombre='Proyecto de Pruebas',
            descripcion='Proyecto para pruebas de automatización',
            usuario_creacion_id=admin.id
        )
        db.session.add(proyecto)
        db.session.commit()
        print(f'Proyecto creado con ID: {proyecto.id}')
    
    caso_login = CasoPrueba.query.filter_by(nombre='Login exitoso con credenciales válidas').first()
    
    if not caso_login:
        print('Error: Caso de prueba de login no encontrado')
        sys.exit(1)
    
    ciclo_login = CicloPrueba(
        nombre='Ciclo de Pruebas de Login',
        descripcion='Ciclo para automatizar pruebas de login con Jenkins',
        estado=EstadoEnum.NUEVO
    )
    
    db.session.add(ciclo_login)
    db.session.commit()
    
    ciclo_login.casos_prueba.append(caso_login)
    db.session.commit()
    
    print(f'Ciclo de prueba creado con ID: {ciclo_login.id}')
    print(f'Nombre: {ciclo_login.nombre}')
    print(f'Casos de prueba en el ciclo: {len(ciclo_login.casos_prueba)}')
    print(f'Caso agregado: {caso_login.nombre} (ID: {caso_login.id})')
