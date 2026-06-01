import pytest
from app.modelos import Proyecto, CicloPrueba, CasoPrueba, Resultado
from config.constantes import EstadoResultadoEnum, EstadoEjecucionEnum, ModoEjecucionEnum
from datetime import datetime, timedelta

def test_ejecucion_sin_autenticar(client):
    """Acceso a /ejecucion sin iniciar sesión debe redirigir a login."""
    response = client.get('/ejecucion/', follow_redirects=True)
    assert response.status_code == 200
    assert "iniciar" in response.get_data(as_text=True).lower() or "login" in response.get_data(as_text=True).lower()

def test_ejecucion_autenticado_vacio(client):
    """Acceso a /ejecucion autenticado sin ciclos de prueba."""
    client.post('/auth/login', data={
        'nombre_usuario': 'miembro',
        'contrasena': 'miembro123'
    }, follow_redirects=True)

    response = client.get('/ejecucion/')
    assert response.status_code == 200
    assert "ejecución" in response.get_data(as_text=True).lower()

def test_ejecucion_con_ciclo_y_caso(client):
    """Acceso a /ejecucion con un ciclo y caso de prueba."""
    client.post('/auth/login', data={
        'nombre_usuario': 'miembro',
        'contrasena': 'miembro123'
    }, follow_redirects=True)

    with client.application.app_context():
        from app.base_datos import db
        proyecto = Proyecto(nombre="Proyecto Ejecución Test", descripcion="Descripción", usuario_id=2)
        db.session.add(proyecto)
        db.session.commit()

        caso = CasoPrueba(nombre="Caso Ejecutable 1", objetivo="Objetivo del caso", descripcion="Prueba", usuario_creacion_id=2)
        db.session.add(caso)
        db.session.commit()

        ciclo = CicloPrueba(nombre="Ciclo de Ejecución Alpha", descripcion="Primer ciclo de prueba")
        ciclo.casos_prueba.append(caso)
        db.session.add(ciclo)
        db.session.commit()

        ciclo_id = ciclo.id
        caso_id = caso.id

    response = client.get('/ejecucion/')
    assert response.status_code == 200
    content = response.get_data(as_text=True)
    assert "Ciclo de Ejecución Alpha" in content
    assert "Caso Ejecutable 1" in content

    response_ciclo = client.get(f'/ejecucion/?ciclo_id={ciclo_id}')
    assert response_ciclo.status_code == 200
    assert "Ciclo de Ejecución Alpha" in response_ciclo.get_data(as_text=True)

def test_ejecucion_preseleccion_ciclo_resultado(client):
    """Verifica que al redirigir para crear un resultado, el ciclo se preselecciona."""
    client.post('/auth/login', data={
        'nombre_usuario': 'miembro',
        'contrasena': 'miembro123'
    }, follow_redirects=True)

    with client.application.app_context():
        from app.base_datos import db
        proyecto = Proyecto(nombre="Proyecto Preseleccion", descripcion="Desc", usuario_id=2)
        db.session.add(proyecto)
        db.session.commit()

        caso = CasoPrueba(nombre="Caso a Ejecutar", objetivo="Test", descripcion="Desc", usuario_creacion_id=2)
        db.session.add(caso)
        db.session.commit()

        ciclo = CicloPrueba(nombre="Ciclo Preseleccionado", descripcion="Ciclo")
        ciclo.casos_prueba.append(caso)
        db.session.add(ciclo)
        db.session.commit()

        ciclo_id = ciclo.id
        caso_id = caso.id

    response = client.get(f'/resultados/nuevo/{caso_id}?ciclo_id={ciclo_id}')
    assert response.status_code == 200
    content = response.get_data(as_text=True)
    assert "Ciclo Preseleccionado" in content
    assert f'value="{ciclo_id}" selected' in content

    response_post = client.post(f'/resultados/nuevo/{caso_id}', data={
        'estado': 'pasado',
        'notas': 'Se ejecutó exitosamente',
        'ciclo_id': str(ciclo_id),
        'entorno': 'Staging',
        'resultado_obtenido': 'El caso pasó sin inconvenientes'
    }, follow_redirects=True)
    
    assert response_post.status_code == 200
    assert "Resultado de prueba registrado exitosamente." in response_post.get_data(as_text=True)

    with client.application.app_context():
        resultado = Resultado.query.filter_by(caso_prueba_id=caso_id, ciclo_prueba_id=ciclo_id).first()
        assert resultado is not None
        assert resultado.estado == EstadoResultadoEnum.PASADO
        assert resultado.notas == 'Se ejecutó exitosamente'


def test_estados_lote_endpoint(client):
    """Prueba que el endpoint /automatizacion/estados retorna correctamente los estados."""
    # Autenticar como miembro
    client.post('/auth/login', data={
        'nombre_usuario': 'miembro',
        'contrasena': 'miembro123'
    }, follow_redirects=True)

    with client.application.app_context():
        from app.base_datos import db
        proyecto = Proyecto(nombre="Proy Lote", descripcion="Desc", usuario_id=2)
        db.session.add(proyecto)
        db.session.commit()

        caso = CasoPrueba(nombre="Caso Lote 1", objetivo="Test", descripcion="Desc", usuario_creacion_id=2)
        db.session.add(caso)
        db.session.commit()

        resultado = Resultado(
            caso_prueba_id=caso.id,
            estado=EstadoResultadoEnum.EN_PROGRESO,
            entorno='Automatizado',
            modo_ejecucion=ModoEjecucionEnum.AUTOMATIZADO,
            estado_ejecucion=EstadoEjecucionEnum.PENDIENTE,
            jenkins_build_number=10,
            id_solicitud="test-solicitud-lote",
            tiempo_inicio_jenkins=datetime.utcnow()
        )
        db.session.add(resultado)
        db.session.commit()
        res_id = resultado.id

    # Consultar estados lote
    response = client.get(f'/automatizacion/estados?ids={res_id},abc,,99999')
    assert response.status_code == 200
    data = response.get_json()
    assert str(res_id) in data
    assert data[str(res_id)]['estado_ejecucion'] == 'pendiente'
    assert '99999' not in data


def test_callback_jenkins_updates_existing_result(client):
    """Prueba que el callback de Jenkins actualiza un resultado existente en estado PENDIENTE."""
    with client.application.app_context():
        from app.base_datos import db
        proyecto = Proyecto(nombre="Proy Callback", descripcion="Desc", usuario_id=2)
        db.session.add(proyecto)
        db.session.commit()

        caso = CasoPrueba(nombre="Caso Callback", objetivo="Test", descripcion="Desc", usuario_creacion_id=2)
        db.session.add(caso)
        db.session.commit()

        resultado = Resultado(
            caso_prueba_id=caso.id,
            estado=EstadoResultadoEnum.EN_PROGRESO,
            entorno='Automatizado',
            modo_ejecucion=ModoEjecucionEnum.AUTOMATIZADO,
            estado_ejecucion=EstadoEjecucionEnum.PENDIENTE,
            jenkins_build_number=15,
            id_solicitud="id-solicitud-callback-test",
            tiempo_inicio_jenkins=datetime.utcnow() - timedelta(minutes=5)
        )
        db.session.add(resultado)
        db.session.commit()
        res_id = resultado.id
        caso_id = caso.id

    # Simular callback de Jenkins
    payload = {
        'id_solicitud': 'id-solicitud-callback-test',
        'estado_prueba': 'PASADO',
        'resultado_obtenido': 'Todo pasó correctamente',
        'notas': 'Comentario de behave',
        'jenkins_build_number': 15,
        'jenkins_log_url': 'http://jenkins/job/Pipeline/15/console',
        'tiempo_inicio_jenkins': int((datetime.utcnow() - timedelta(minutes=5)).timestamp() * 1000)
    }

    response = client.post(f'/automatizacion/api/resultados/desde-jenkins/{caso_id}', json=payload)
    assert response.status_code == 200

    with client.application.app_context():
        updated_res = Resultado.query.get(res_id)
        assert updated_res.estado_ejecucion == EstadoEjecucionEnum.COMPLETADO
        assert updated_res.estado == EstadoResultadoEnum.PASADO
        assert updated_res.resultado_obtenido == 'Todo pasó correctamente'
        assert updated_res.tiempo_ejecucion is not None
        assert updated_res.tiempo_ejecucion >= 290  # ~300 segundos
