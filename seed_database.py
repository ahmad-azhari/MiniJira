#!/usr/bin/env python
"""Script para limpiar y poblar la base de datos con datos de prueba realistas."""

import os
import sys
from datetime import datetime, timedelta
from app.app import crear_app
from app.base_datos import db
from app.modelos import (
    Usuario, Rol, Proyecto, Epica, CasoPrueba, CicloPrueba,
    Resultado, Defecto
)
from config.constantes import (
    EstadoEnum, EstadoDefectoEnum, EstadoResultadoEnum, PrioridadEnum,
    TipoEnum, TipoTestEnum, ModoEjecucionEnum, EstadoEjecucionEnum
)

def clear_database():
    print("[*] Limpiando base de datos...")

    from app.modelos.epica import epica_caso_prueba, epica_ciclo_prueba
    from app.modelos.caso_prueba import caso_prueba_ciclo
    from app.modelos.historial import Historial

    db.session.execute(db.delete(epica_caso_prueba))
    db.session.execute(db.delete(epica_ciclo_prueba))
    db.session.execute(db.delete(caso_prueba_ciclo))

    Historial.query.delete()
    Defecto.query.delete()
    Resultado.query.delete()
    CicloPrueba.query.delete()
    CasoPrueba.query.delete()

    db.session.execute(db.update(Epica).values(epica_padre_id=None))
    db.session.commit()

    Epica.query.delete()
    Proyecto.query.delete()

    db.session.commit()
    print("[OK] Base de datos limpiada (usuarios mantenidos)")

def seed_projects_and_epics(usuario):
    print("[*] Creando proyectos...")

    proyecto1 = Proyecto(
        nombre="Sistema de Autenticacion",
        descripcion="Implementacion de sistema de login y sesiones",
        estado="activo",
        usuario_id=usuario.id,
        fecha_creacion=datetime.utcnow()
    )
    db.session.add(proyecto1)
    db.session.flush()

    epica1 = Epica(
        tipo=TipoEnum.EPIC,
        nombre="Login y Registro de Usuarios",
        descripcion="Funcionalidad de autenticación de usuarios",
        estado=EstadoEnum.EN_PROGRESO,
        prioridad=PrioridadEnum.ALTA,
        proyecto_id=proyecto1.id,
        usuario_creacion_id=usuario.id,
        usuario_asignado_id=usuario.id
    )
    db.session.add(epica1)
    db.session.flush()

    historia1_1 = Epica(
        tipo=TipoEnum.STORY,
        nombre="Validar credenciales de usuario",
        descripcion="Validar que el usuario y contraseña sean correctos",
        estado=EstadoEnum.EN_PROGRESO,
        prioridad=PrioridadEnum.ALTA,
        proyecto_id=proyecto1.id,
        epica_padre_id=epica1.id,
        usuario_creacion_id=usuario.id,
        usuario_asignado_id=usuario.id
    )
    db.session.add(historia1_1)
    db.session.flush()

    proyecto2 = Proyecto(
        nombre="Sistema de Gestion de Tareas",
        descripcion="Plataforma de gestion de proyectos y tareas",
        estado="activo",
        usuario_id=usuario.id,
        fecha_creacion=datetime.utcnow()
    )
    db.session.add(proyecto2)
    db.session.flush()

    epica2 = Epica(
        tipo=TipoEnum.EPIC,
        nombre="CRUD de Tareas",
        descripcion="Crear, leer, actualizar y eliminar tareas",
        estado=EstadoEnum.EN_PROGRESO,
        prioridad=PrioridadEnum.MEDIA,
        proyecto_id=proyecto2.id,
        usuario_creacion_id=usuario.id,
        usuario_asignado_id=usuario.id
    )
    db.session.add(epica2)
    db.session.flush()

    historia2_1 = Epica(
        tipo=TipoEnum.STORY,
        nombre="Crear nueva tarea",
        descripcion="El usuario puede crear una nueva tarea con título y descripción",
        estado=EstadoEnum.EN_PROGRESO,
        prioridad=PrioridadEnum.MEDIA,
        proyecto_id=proyecto2.id,
        epica_padre_id=epica2.id,
        usuario_creacion_id=usuario.id,
        usuario_asignado_id=usuario.id
    )
    db.session.add(historia2_1)
    db.session.flush()

    historia2_2 = Epica(
        tipo=TipoEnum.STORY,
        nombre="Listar todas las tareas",
        descripcion="El usuario puede ver un listado de todas las tareas",
        estado=EstadoEnum.EN_PROGRESO,
        prioridad=PrioridadEnum.MEDIA,
        proyecto_id=proyecto2.id,
        epica_padre_id=epica2.id,
        usuario_creacion_id=usuario.id,
        usuario_asignado_id=usuario.id
    )
    db.session.add(historia2_2)
    db.session.flush()

    db.session.commit()
    return {
        'proyecto1': proyecto1,
        'proyecto2': proyecto2,
        'epica1': epica1,
        'epica2': epica2,
        'historia1_1': historia1_1,
        'historia2_1': historia2_1,
        'historia2_2': historia2_2
    }

def seed_test_cases(usuario, epicas_dict):
    print("[*] Creando casos de prueba...")

    casos = []

    caso1 = CasoPrueba(
        nombre="Verificar login con credenciales válidas",
        objetivo="Validar que un usuario pueda iniciar sesión con credenciales correctas",
        precondicion="Usuario debe estar registrado en el sistema",
        descripcion="Intentar iniciar sesión con usuario y contraseña válidos",
        pasos_reproduccion="1. Ir a la página de login\n2. Ingresar usuario válido\n3. Ingresar contraseña correcta\n4. Hacer clic en 'Iniciar Sesión'",
        resultado_esperado="La sesión se inicia correctamente y se redirige al dashboard",
        estado=EstadoEnum.NUEVO,
        prioridad=PrioridadEnum.ALTA,
        tipo=TipoTestEnum.AUTOMATIZADO,
        usuario_creacion_id=usuario.id,
        script_prueba="""Feature: Login Process

  Scenario: Login con credenciales válidas
    Given el usuario está en la página de login
    When ingresa nombre de usuario "admin"
    And ingresa contraseña "admin123"
    And hace clic en el botón Login
    Then es autenticado exitosamente
    And es redirigido al dashboard principal
""",
        requiere_intento_manual=False
    )
    caso1.epicas.append(epicas_dict['historia1_1'])
    db.session.add(caso1)
    casos.append(caso1)

    caso2 = CasoPrueba(
        nombre="Validar rechazo de contraseña incorrecta",
        objetivo="Verificar que el login falla con contraseña incorrecta",
        precondicion="Usuario debe estar registrado",
        descripcion="Intentar login con contraseña incorrecta",
        pasos_reproduccion="1. Ir a login\n2. Ingresar usuario válido\n3. Ingresar contraseña incorrecta\n4. Clic en 'Iniciar Sesión'",
        resultado_esperado="Se muestra mensaje de error: 'Usuario o contraseña incorrectos'",
        estado=EstadoEnum.NUEVO,
        prioridad=PrioridadEnum.ALTA,
        tipo=TipoTestEnum.AUTOMATIZADO,
        usuario_creacion_id=usuario.id,
        script_prueba="""Feature: Login Process

  Scenario: Validar rechazo de contraseña incorrecta
    Given el usuario está en la página de login
    When ingresa nombre de usuario "admin"
    And ingresa contraseña "wrongpass"
    And hace clic en el botón Login
    Then se muestra mensaje de error "Usuario o contraseña incorrectos"
""",
        requiere_intento_manual=False
    )
    caso2.epicas.append(epicas_dict['historia1_1'])
    db.session.add(caso2)
    casos.append(caso2)

    caso3 = CasoPrueba(
        nombre="Crear tarea con título y descripción",
        objetivo="Automatizar la creación de una nueva tarea",
        precondicion="Usuario debe estar autenticado",
        descripcion="Crear una nueva tarea mediante API",
        pasos_reproduccion="POST /api/tareas",
        resultado_esperado="Tarea creada con ID generado",
        estado=EstadoEnum.NUEVO,
        prioridad=PrioridadEnum.MEDIA,
        tipo=TipoTestEnum.AUTOMATIZADO,
        usuario_creacion_id=usuario.id,
        script_prueba="""Feature: Crear Tarea

  Scenario: Crear una tarea válida
    Given el usuario está autenticado
    When envía una solicitud POST a "/api/tareas" con:
      | campo | valor |
      | titulo | Tarea de prueba |
      | descripcion | Esta es una tarea de prueba |
    Then la respuesta debe tener código 201
    And la respuesta debe contener una "id"
    And la respuesta debe contener "titulo" = "Tarea de prueba"

  Scenario: Crear tarea sin título
    Given el usuario está autenticado
    When envía una solicitud POST a "/api/tareas" con:
      | campo | valor |
      | descripcion | Sin título |
    Then la respuesta debe tener código 400
    And la respuesta debe contener una "error"
""",
        requiere_intento_manual=False
    )
    caso3.epicas.append(epicas_dict['historia2_1'])
    db.session.add(caso3)
    casos.append(caso3)

    caso4 = CasoPrueba(
        nombre="Listar todas las tareas del usuario",
        objetivo="Automatizar la obtención de tareas",
        precondicion="Usuario autenticado con tareas en el sistema",
        descripcion="Obtener listado de tareas mediante API",
        pasos_reproduccion="GET /api/tareas",
        resultado_esperado="Devuelve lista de tareas en formato JSON",
        estado=EstadoEnum.NUEVO,
        prioridad=PrioridadEnum.MEDIA,
        tipo=TipoTestEnum.AUTOMATIZADO,
        usuario_creacion_id=usuario.id,
        script_prueba="""Feature: Listar Tareas

  Scenario: Obtener todas las tareas
    Given el usuario está autenticado
    When envía una solicitud GET a "/api/tareas"
    Then la respuesta debe tener código 200
    And la respuesta debe ser una lista JSON
    And cada elemento debe contener:
      | campo |
      | id |
      | titulo |
      | descripcion |
      | estado |

  Scenario: Listar tareas sin autenticación
    When envía una solicitud GET a "/api/tareas" sin autenticación
    Then la respuesta debe tener código 401
""",
        requiere_intento_manual=False
    )
    caso4.epicas.append(epicas_dict['historia2_2'])
    db.session.add(caso4)
    casos.append(caso4)

    caso5 = CasoPrueba(
        nombre="Actualizar estado de tarea",
        objetivo="Automatizar la actualización de una tarea",
        precondicion="Tarea debe existir",
        descripcion="Cambiar estado de tarea a completada",
        pasos_reproduccion="PUT /api/tareas/{id}",
        resultado_esperado="Tarea actualizada correctamente",
        estado=EstadoEnum.NUEVO,
        prioridad=PrioridadEnum.MEDIA,
        tipo=TipoTestEnum.AUTOMATIZADO,
        usuario_creacion_id=usuario.id,
        script_prueba="""Feature: Actualizar Tarea

  Scenario: Cambiar estado de tarea a completada
    Given existe una tarea
    And el usuario está autenticado
    When envía una solicitud PUT a la tarea con:
      | campo | valor |
      | estado | completada |
    Then la respuesta debe tener código 200
    And el campo "estado" debe ser "completada"

  Scenario: Actualizar tarea inexistente
    Given el usuario está autenticado
    When envía una solicitud PUT a "/api/tareas/9999" con:
      | campo | valor |
      | estado | completada |
    Then la respuesta debe tener código 404
""",
        requiere_intento_manual=False
    )
    caso5.epicas.append(epicas_dict['historia2_1'])
    db.session.add(caso5)
    casos.append(caso5)

    caso6 = CasoPrueba(
        nombre="Eliminar una tarea",
        objetivo="Automatizar la eliminación de tarea",
        precondicion="Tarea debe existir",
        descripcion="Eliminar tarea mediante API",
        pasos_reproduccion="DELETE /api/tareas/{id}",
        resultado_esperado="Tarea eliminada exitosamente",
        estado=EstadoEnum.NUEVO,
        prioridad=PrioridadEnum.MEDIA,
        tipo=TipoTestEnum.AUTOMATIZADO,
        usuario_creacion_id=usuario.id,
        script_prueba="""Feature: Eliminar Tarea

  Scenario: Eliminar tarea existente
    Given existe una tarea
    And el usuario está autenticado
    When envía una solicitud DELETE a la tarea
    Then la respuesta debe tener código 204
    When envía una solicitud GET a la tarea
    Then la respuesta debe tener código 404

  Scenario: Eliminar tarea sin permisos
    Given existe una tarea creada por otro usuario
    And el usuario actual está autenticado
    When envía una solicitud DELETE a "/api/tareas" de otro usuario
    Then la respuesta debe tener código 403
""",
        requiere_intento_manual=False
    )
    caso6.epicas.append(epicas_dict['epica2'])
    db.session.add(caso6)
    casos.append(caso6)

    caso7 = CasoPrueba(
        nombre="Verificar login manual con credenciales válidas",
        objetivo="Validar que un usuario pueda iniciar sesión manualmente",
        precondicion="Usuario debe estar registrado en el sistema",
        descripcion="Intentar iniciar sesión con usuario y contraseña válidos desde la UI visualmente",
        pasos_reproduccion="1. Ir a la página de login\n2. Ingresar usuario válido\n3. Ingresar contraseña correcta\n4. Hacer clic en 'Iniciar Sesión'",
        resultado_esperado="La sesión se inicia correctamente y se redirige al dashboard",
        estado=EstadoEnum.NUEVO,
        prioridad=PrioridadEnum.ALTA,
        tipo=TipoTestEnum.MANUAL,
        usuario_creacion_id=usuario.id,
        requiere_intento_manual=True
    )
    db.session.add(caso7)
    casos.append(caso7)

    caso8 = CasoPrueba(
        nombre="Validar rechazo manual de contraseña incorrecta",
        objetivo="Verificar que el login falla visualmente con contraseña incorrecta",
        precondicion="Usuario debe estar registrado",
        descripcion="Intentar login con contraseña incorrecta y verificar el mensaje de error visual",
        pasos_reproduccion="1. Ir a login\n2. Ingresar usuario válido\n3. Ingresar contraseña incorrecta\n4. Clic en 'Iniciar Sesión'",
        resultado_esperado="Se muestra mensaje de error emergente en color rojo",
        estado=EstadoEnum.NUEVO,
        prioridad=PrioridadEnum.ALTA,
        tipo=TipoTestEnum.MANUAL,
        usuario_creacion_id=usuario.id,
        requiere_intento_manual=True
    )
    db.session.add(caso8)
    casos.append(caso8)

    caso9 = CasoPrueba(
        nombre="Verificar visualización de tareas con descripciones muy largas",
        objetivo="Comprobar que el diseño no se rompe con textos extensos",
        precondicion="Ninguna",
        descripcion="Crear una tarea con una descripción muy larga y visualizarla en la UI",
        pasos_reproduccion="1. Crear tarea con descripción de más de 500 palabras\n2. Ir al listado de tareas\n3. Ver detalle de la tarea",
        resultado_esperado="El texto debe ajustarse al contenedor o cortarse con puntos suspensivos sin deformar la tabla",
        estado=EstadoEnum.NUEVO,
        prioridad=PrioridadEnum.MEDIA,
        tipo=TipoTestEnum.MANUAL,
        usuario_creacion_id=usuario.id,
        requiere_intento_manual=True
    )
    caso9.epicas.append(epicas_dict['historia2_1'])
    db.session.add(caso9)
    casos.append(caso9)

    caso10 = CasoPrueba(
        nombre="Verificar paginación o scroll en listado de tareas",
        objetivo="Asegurar que se pueden ver todas las tareas si hay muchas",
        precondicion="Tener al menos 20 tareas creadas",
        descripcion="Acceder al listado de tareas cuando el usuario tiene un volumen alto de registros",
        pasos_reproduccion="1. Generar 20+ tareas\n2. Ir al listado principal\n3. Desplazarse hacia abajo",
        resultado_esperado="Se debe cargar un scroll infinito o mostrar controles de paginación",
        estado=EstadoEnum.NUEVO,
        prioridad=PrioridadEnum.BAJA,
        tipo=TipoTestEnum.MANUAL,
        usuario_creacion_id=usuario.id,
        requiere_intento_manual=True
    )
    caso10.epicas.append(epicas_dict['historia2_2'])
    db.session.add(caso10)
    casos.append(caso10)

    db.session.flush()
    db.session.commit()
    print(f"[OK] Creados {len(casos)} casos de prueba")
    return casos

def seed_test_cycles(usuario, casos):
    print("[*] Creando ciclos de prueba...")

    ciclos = []

    ciclo1 = CicloPrueba(
        nombre="Ciclo 1: Pruebas Login Manuales",
        descripcion="Pruebas manuales del modulo de login y autenticacion",
        estado=EstadoEnum.NUEVO
    )
    db.session.add(ciclo1)
    db.session.flush()

    ciclo1.casos_prueba.append(casos[6])
    ciclo1.casos_prueba.append(casos[7])
    ciclos.append(ciclo1)

    ciclo2 = CicloPrueba(
        nombre="Ciclo 2: Pruebas de Gestion de Tareas",
        descripcion="Pruebas de creacion, lectura, actualizacion y eliminacion de tareas",
        estado=EstadoEnum.NUEVO
    )
    db.session.add(ciclo2)
    db.session.flush()

    ciclo2.casos_prueba.append(casos[2])
    ciclo2.casos_prueba.append(casos[3])
    ciclo2.casos_prueba.append(casos[4])
    ciclo2.casos_prueba.append(casos[5])
    ciclos.append(ciclo2)

    ciclo3 = CicloPrueba(
        nombre="Ciclo 3: Pruebas de Tareas",
        descripcion="Pruebas completas de las tareas del sistema",
        estado=EstadoEnum.NUEVO
    )
    db.session.add(ciclo3)
    db.session.flush()

    ciclo3.casos_prueba.append(casos[2])
    ciclo3.casos_prueba.append(casos[3])
    ciclo3.casos_prueba.append(casos[4])
    ciclo3.casos_prueba.append(casos[5])
    ciclo3.casos_prueba.append(casos[8])
    ciclo3.casos_prueba.append(casos[9])
    ciclos.append(ciclo3)

    ciclo4 = CicloPrueba(
        nombre="Ciclo 4: Pruebas de Autenticacion",
        descripcion="Ciclo dedicado exclusivamente a las pruebas de login automatizadas",
        estado=EstadoEnum.NUEVO
    )
    db.session.add(ciclo4)
    db.session.flush()

    ciclo4.casos_prueba.append(casos[0])
    ciclo4.casos_prueba.append(casos[1])
    ciclos.append(ciclo4)

    db.session.commit()
    print(f"[OK] Creados {len(ciclos)} ciclos de prueba")
    return ciclos

def seed_defects(usuario, casos):
    print("[*] Creando defectos...")

    defectos = []

    defecto1 = Defecto(
        titulo="Campo de contrasena no valida caracteres especiales",
        descripcion="Cuando el usuario intenta usar caracteres especiales en la contrasena, el sistema rechaza la solicitud. Se esperaba que aceptara @#$% en la contrasena pero muestra error de validacion",
        estado=EstadoDefectoEnum.ABIERTO,
        prioridad=PrioridadEnum.MEDIA,
        caso_prueba_id=casos[1].id,
        usuario_asignado_id=usuario.id,
        usuario_creacion_id=usuario.id
    )
    db.session.add(defecto1)
    defectos.append(defecto1)

    defecto2 = Defecto(
        titulo="La API de tareas es lenta con muchos registros",
        descripcion="Cuando hay mas de 1000 tareas, la API tarda mas de 5 segundos en responder. Se esperaba una respuesta en menos de 1 segundo.",
        estado=EstadoDefectoEnum.ABIERTO,
        prioridad=PrioridadEnum.ALTA,
        caso_prueba_id=casos[3].id,
        usuario_asignado_id=usuario.id,
        usuario_creacion_id=usuario.id
    )
    db.session.add(defecto2)
    defectos.append(defecto2)

    db.session.commit()
    print(f"[OK] Creados {len(defectos)} defectos")
    return defectos

def seed_jenkins_results(usuario, casos, ciclos):
    print("[*] Sembrando ejemplos de ejecuciones de Jenkins...")
    print("[OK] Ejemplos de ejecuciones omitidos")

def main():
    app = crear_app()

    with app.app_context():
        usuario = Usuario.query.filter_by(nombre_usuario='admin').first()

        if not usuario:
            print("❌ Error: Usuario 'admin' no existe")
            sys.exit(1)

        print(f"\n{'='*50}")
        print("SEED DE BASE DE DATOS MEJORADO")
        print(f"{'='*50}\n")

        clear_database()

        epicas_dict = seed_projects_and_epics(usuario)

        casos = seed_test_cases(usuario, epicas_dict)

        ciclos = seed_test_cycles(usuario, casos)

        defectos = seed_defects(usuario, casos)

        seed_jenkins_results(usuario, casos, ciclos)

        print(f"\n{'='*50}")
        print("SEED COMPLETADO CON EXITO")
        print(f"{'='*50}")

if __name__ == '__main__':
    main()
