#!/usr/bin/env python
import os
import logging
from app.app import crear_app, db
from app.modelos import Usuario, Rol, Tarea
from config.constantes import RolEnum

app = crear_app(os.getenv('FLASK_ENV', 'development'))
logger = logging.getLogger(__name__)

with app.app_context():
    db.create_all()
    # Minimal seed for API automation runner (users + a couple tasks).
    try:
        if not Rol.query.first():
            roles = [
                Rol(nombre=RolEnum.ADMIN.value, descripcion="Acceso completo al sistema"),
                Rol(nombre=RolEnum.MIEMBRO.value, descripcion="Puede crear y editar contenido"),
                Rol(nombre=RolEnum.VIEWER.value, descripcion="Solo lectura"),
            ]
            db.session.add_all(roles)
            db.session.commit()

        admin = Usuario.query.filter_by(nombre_usuario="admin").first()
        if not admin:
            admin_rol = Rol.query.filter_by(nombre=RolEnum.ADMIN.value).first()
            admin = Usuario(nombre_usuario="admin", email="admin@example.com")
            admin.establecer_contrasena("admin123")
            if admin_rol:
                admin.roles.append(admin_rol)
            db.session.add(admin)
            db.session.commit()

        miembro = Usuario.query.filter_by(nombre_usuario="miembro").first()
        if not miembro:
            miembro_rol = Rol.query.filter_by(nombre=RolEnum.MIEMBRO.value).first()
            miembro = Usuario(nombre_usuario="miembro", email="miembro@example.com")
            miembro.establecer_contrasena("miembro123")
            if miembro_rol:
                miembro.roles.append(miembro_rol)
            db.session.add(miembro)
            db.session.commit()

        if not Tarea.query.first():
            db.session.add(
                Tarea(titulo="Tarea inicial admin", descripcion="Seed", estado="pendiente", usuario_id=admin.id)
            )
            db.session.add(
                Tarea(titulo="Tarea inicial miembro", descripcion="Seed", estado="pendiente", usuario_id=miembro.id)
            )
            db.session.commit()
        elif admin and not Tarea.query.filter_by(usuario_id=admin.id).first():
            db.session.add(
                Tarea(titulo="Tarea inicial admin", descripcion="Seed", estado="pendiente", usuario_id=admin.id)
            )
            db.session.commit()
        elif miembro and not Tarea.query.filter_by(usuario_id=miembro.id).first():
            db.session.add(
                Tarea(titulo="Tarea inicial miembro", descripcion="Seed", estado="pendiente", usuario_id=miembro.id)
            )
            db.session.commit()
    except Exception:
        db.session.rollback()

    try:
        from app.servicios.jenkins_service import ServicioJenkins

        jenkins = ServicioJenkins()
        if jenkins.validar_conexion():
            logger.info('Pipeline Jenkins sincronizado al arrancar.')
    except Exception as exc:
        logger.warning('No se pudo sincronizar Jenkins al arrancar: %s', exc)

if __name__ == '__main__':
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    puerto = int(os.getenv('FLASK_PORT', 5000))
    logger.info(f'Servidor corriendo en http://{host}:{puerto}')
    app.run(host=host, port=puerto, debug=app.config.get('DEBUG', False))

