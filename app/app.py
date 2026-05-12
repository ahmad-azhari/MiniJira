from flask import Flask, redirect, url_for, session
from config.settings import get_config
from app.base_datos import db
import os


def crear_app(config_name=None):
    app_dir = os.path.dirname(os.path.abspath(__file__))

    app = Flask(__name__,
                template_folder=os.path.join(app_dir, 'plantillas'),
                static_folder=os.path.join(app_dir, 'estaticos'))

    if config_name is None:
        config_name = os.getenv('APP_ENV', 'development')

    config = get_config(config_name)
    app.config.from_object(config)

    db.init_app(app)

    carpeta_subidas = app.config.get('UPLOAD_FOLDER')
    if not os.path.exists(carpeta_subidas):
        os.makedirs(carpeta_subidas)

    from app.modelos import (
        Usuario, Rol, Proyecto, Epica, CasoPrueba,
        CicloPrueba, Resultado, Defecto, Historial
    )

    from app.rutas.auth import auth_bp
    from app.rutas.proyectos import proyectos_bp
    from app.rutas.epicas import epicas_bp
    from app.rutas.casos_prueba import casos_prueba_bp
    from app.rutas.ciclos_prueba import ciclos_prueba_bp
    from app.rutas.resultados import resultados_bp
    from app.rutas.defectos import defectos_bp
    from app.rutas.reportes import reportes_bp
    from app.rutas.usuarios import usuarios_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(proyectos_bp)
    app.register_blueprint(epicas_bp)
    app.register_blueprint(casos_prueba_bp)
    app.register_blueprint(ciclos_prueba_bp)
    app.register_blueprint(resultados_bp)
    app.register_blueprint(defectos_bp)
    app.register_blueprint(reportes_bp)
    app.register_blueprint(usuarios_bp)

    @app.route('/')
    def inicio():
        if 'usuario_id' in session:
            return redirect(url_for('proyectos_bp.indice'))
        else:
            return redirect(url_for('auth_bp.login'))

    @app.shell_context_processor
    def shell_context():
        return {
            'db': db,
            'Usuario': Usuario,
            'Rol': Rol,
            'Proyecto': Proyecto,
            'Epica': Epica,
            'CasoPrueba': CasoPrueba,
            'CicloPrueba': CicloPrueba,
            'Resultado': Resultado,
            'Defecto': Defecto,
            'Historial': Historial,
        }

    return app
