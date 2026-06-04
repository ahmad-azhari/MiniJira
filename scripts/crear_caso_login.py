import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.app import crear_app, db
from app.modelos import CasoPrueba, Usuario, CicloPrueba, Proyecto
from config.constantes import TipoTestEnum, EstadoEnum, PrioridadEnum

app = crear_app()

with app.app_context():
    admin = Usuario.query.filter_by(nombre_usuario='admin').first()
    
    if not admin:
        print('Error: Usuario admin no encontrado')
        sys.exit(1)
    
    caso_login = CasoPrueba(
        nombre='Login exitoso con credenciales válidas',
        objetivo='Verificar que un usuario puede autenticarse correctamente con credenciales válidas',
        precondicion='El usuario debe estar registrado en el sistema',
        descripcion='Prueba de automatización para validar el flujo de login de la aplicación',
        pasos_reproduccion='1. Navegar a la página de login\n2. Ingresar nombre de usuario\n3. Ingresar contraseña\n4. Hacer clic en Login',
        resultado_esperado='El usuario es autenticado exitosamente y redirigido al dashboard',
        estado=EstadoEnum.NUEVO,
        prioridad=PrioridadEnum.ALTA,
        tipo=TipoTestEnum.AUTOMATIZADO,
        url='/auth/login',
        script_prueba='''Feature: Login de Usuario

  Scenario: Login exitoso con credenciales válidas
    Given el usuario está en la página de login
    When ingresa nombre de usuario "admin"
    And ingresa contraseña "admin123"
    And hace clic en el botón Login
    Then es autenticado exitosamente
    And es redirigido al dashboard principal''',
        usuario_creacion_id=admin.id
    )
    
    db.session.add(caso_login)
    db.session.commit()
    
    print(f'Caso de prueba creado con ID: {caso_login.id}')
    print(f'Nombre: {caso_login.nombre}')
    print(f'Tipo: {caso_login.tipo.value}')
