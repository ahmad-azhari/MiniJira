from app.app import crear_app, db
from app.modelos import (
    Usuario, Rol, Proyecto, Epica, CasoPrueba,
    CicloPrueba, Resultado, Defecto, Historial
)
from config.constantes import (
    TipoEnum, EstadoEnum, PrioridadEnum,
    EstadoResultadoEnum, EstadoDefectoEnum,
    TipoTestEnum, RolEnum, EstadoProyectoEnum
)


def inicializar_bd():
    app = crear_app('development')

    with app.app_context():
        db.create_all()
        print("✓ Tablas creadas exitosamente")

        if not Rol.query.first():
            print("\n Creando roles base...")
            roles = [
                Rol(nombre=RolEnum.ADMIN.value, descripcion="Acceso completo al sistema"),
                Rol(nombre=RolEnum.MIEMBRO.value, descripcion="Puede crear y editar épicas, historias, casos de prueba y defectos"),
                Rol(nombre=RolEnum.VIEWER.value, descripcion="Solo lectura de contenido"),
            ]
            db.session.add_all(roles)
            db.session.commit()
            print(f" {len(roles)} roles creados")

            print("\n Creando usuarios de prueba...")
            admin_rol = Rol.query.filter_by(nombre=RolEnum.ADMIN.value).first()
            miembro_rol = Rol.query.filter_by(nombre=RolEnum.MIEMBRO.value).first()
            viewer_rol = Rol.query.filter_by(nombre=RolEnum.VIEWER.value).first()

            admin = Usuario(nombre_usuario="admin", email="admin@example.com")
            admin.establecer_contrasena("admin123")
            admin.roles.append(admin_rol)

            miembro = Usuario(nombre_usuario="miembro", email="miembro@example.com")
            miembro.establecer_contrasena("miembro123")
            miembro.roles.append(miembro_rol)

            viewer = Usuario(nombre_usuario="viewer", email="viewer@example.com")
            viewer.establecer_contrasena("viewer123")
            viewer.roles.append(viewer_rol)

            db.session.add_all([admin, miembro, viewer])
            db.session.commit()
            print(f" 3 usuarios de prueba creados")

        if not Proyecto.query.first():
            print("\n Creando proyectos de prueba...")
            admin = Usuario.query.filter_by(nombre_usuario="admin").first()

            proyecto1 = Proyecto(
                nombre="Proyecto IA",
                descripcion="Sistema de IA para análisis de texto",
                estado=EstadoProyectoEnum.ACTIVO,
                usuario_id=admin.id
            )
            proyecto2 = Proyecto(
                nombre="App Móvil",
                descripcion="Aplicación Android de gestión",
                estado=EstadoProyectoEnum.ACTIVO,
                usuario_id=admin.id
            )
            db.session.add_all([proyecto1, proyecto2])
            db.session.commit()
            print(f" 2 proyectos creados")

            print("\n Creando épicas...")
            epica1 = Epica(
                nombre="Módulo NLP",
                tipo=TipoEnum.EPIC,
                prioridad=PrioridadEnum.ALTA,
                descripcion="Desarrollar modelo de lenguaje natural",
                estado=EstadoEnum.NUEVO,
                proyecto_id=proyecto1.id,
                usuario_creacion_id=admin.id
            )
            epica2 = Epica(
                nombre="Front-End APP",
                tipo=TipoEnum.EPIC,
                prioridad=PrioridadEnum.MEDIA,
                descripcion="Interfaz gráfica de la aplicación",
                estado=EstadoEnum.NUEVO,
                proyecto_id=proyecto2.id,
                usuario_creacion_id=admin.id
            )
            epica3 = Epica(
                nombre="Back-End API",
                tipo=TipoEnum.EPIC,
                prioridad=PrioridadEnum.MEDIA,
                descripcion="Servidor y API REST",
                estado=EstadoEnum.NUEVO,
                proyecto_id=proyecto2.id,
                usuario_creacion_id=admin.id
            )
            db.session.add_all([epica1, epica2, epica3])
            db.session.commit()
            print(f" 3 épicas creadas")

            print("\n Creando historias de usuario...")
            historia1 = Epica(
                nombre="UI de Login",
                tipo=TipoEnum.STORY,
                prioridad=PrioridadEnum.MEDIA,
                descripcion="Pantalla de login y autenticación",
                estado=EstadoEnum.EN_PROGRESO,
                epica_padre_id=epica2.id,
                proyecto_id=proyecto2.id,
                usuario_creacion_id=admin.id
            )
            historia2 = Epica(
                nombre="Gestión de usuarios",
                tipo=TipoEnum.STORY,
                prioridad=PrioridadEnum.ALTA,
                descripcion="CRUD de usuarios en backend",
                estado=EstadoEnum.NUEVO,
                epica_padre_id=epica3.id,
                proyecto_id=proyecto2.id,
                usuario_creacion_id=admin.id
            )
            db.session.add_all([historia1, historia2])
            db.session.commit()
            print(f" 2 historias creadas")

            print("\n Creando casos de prueba...")
            caso1 = CasoPrueba(
                nombre="Login con credenciales válidas",
                objetivo="Verificar que un usuario puede iniciar sesión",
                precondicion="Usuario debe estar registrado",
                descripcion="Ingresar usuario y contraseña válidos",
                resultado_esperado="Sistema muestra dashboard",
                tipo=TipoTestEnum.MANUAL,
                prioridad=PrioridadEnum.ALTA,
                estado=EstadoEnum.NUEVO,
                usuario_creacion_id=admin.id
            )
            caso2 = CasoPrueba(
                nombre="Login con credenciales inválidas",
                objetivo="Verificar rechazo de credenciales incorrectas",
                precondicion="Usuario debe estar registrado",
                descripcion="Ingresar contraseña incorrecta",
                resultado_esperado="Sistema muestra mensaje de error",
                tipo=TipoTestEnum.MANUAL,
                prioridad=PrioridadEnum.MEDIA,
                estado=EstadoEnum.NUEVO,
                usuario_creacion_id=admin.id
            )
            db.session.add_all([caso1, caso2])
            db.session.commit()
            print(f"✓ 2 casos de prueba creados")

            print("\n Creando ciclos de prueba...")
            ciclo1 = CicloPrueba(
                nombre="Sprint 1 - Pruebas",
                descripcion="Ciclo de pruebas del primer sprint",
                estado=EstadoEnum.EN_PROGRESO
            )
            db.session.add(ciclo1)
            db.session.commit()
            print(f" 1 ciclo de prueba creado")

            print("\n Asociando casos a ciclo...")
            ciclo1.casos_prueba.append(caso1)
            ciclo1.casos_prueba.append(caso2)
            db.session.commit()
            print(f" Casos asociados al ciclo")

            print("\n" + "="*50)
            print(" BASE DE DATOS INICIALIZADA EXITOSAMENTE")
            print("="*50)
            print("\n Usuarios de prueba creados:")
            print("  • admin / admin123")
            print("  • miembro / miembro123")
            print("  • viewer / viewer123")
            print("\n Proyectos creados:")
            print(f"  • {proyecto1.nombre}")
            print(f"  • {proyecto2.nombre}")


if __name__ == '__main__':
    inicializar_bd()
