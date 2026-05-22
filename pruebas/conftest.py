import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from app.app import crear_app, db as _db
from app.modelos import Rol, Usuario
from config.constantes import RolEnum

@pytest.fixture
def app():
    app = crear_app('testing')
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False
    })

    with app.app_context():
        _db.create_all()
        
        admin_rol = Rol(nombre=RolEnum.ADMIN.value, descripcion="Acceso completo al sistema")
        miembro_rol = Rol(nombre=RolEnum.MIEMBRO.value, descripcion="Miembro")
        viewer_rol = Rol(nombre=RolEnum.VIEWER.value, descripcion="Viewer")
        _db.session.add_all([admin_rol, miembro_rol, viewer_rol])
        
        admin = Usuario(nombre_usuario="admin", email="admin@example.com")
        admin.establecer_contrasena("admin123")
        admin.roles.append(admin_rol)

        miembro = Usuario(nombre_usuario="miembro", email="miembro@example.com")
        miembro.establecer_contrasena("miembro123")
        miembro.roles.append(miembro_rol)

        viewer = Usuario(nombre_usuario="viewer", email="viewer@example.com")
        viewer.establecer_contrasena("viewer123")
        viewer.roles.append(viewer_rol)

        _db.session.add_all([admin, miembro, viewer])
        _db.session.commit()
        
        yield app
        _db.session.remove()
        _db.drop_all()

@pytest.fixture
def driver():
    opciones = Options()
    opciones.add_argument("--disable-gpu")
    opciones.add_argument("--disable-dev-shm-usage")
    opciones.add_argument("--start-maximized")

    driver = webdriver.Chrome(options=opciones)
    driver.set_window_size(1920, 1080)

    yield driver
    driver.quit()
