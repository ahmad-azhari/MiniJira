import pytest
from app.modelos import Proyecto, Epica
from config.constantes import TipoEnum, PrioridadEnum, EstadoEnum

def test_crear_historia_suelta_sin_epica(client):
    client.post('/auth/login', data={
        'nombre_usuario': 'miembro',
        'contrasena': 'miembro123'
    }, follow_redirects=True)

    with client.application.app_context():
        from app.base_datos import db
        proyecto = Proyecto(nombre="Proyecto Test Autocreado", descripcion="Test Description", usuario_id=2)
        db.session.add(proyecto)
        db.session.commit()
        proyecto_id = proyecto.id

    response = client.post('/epicas/historias/nuevo', data={
        'nombre': 'Historia de Prueba Sin Epica',
        'descripcion': 'Prueba descripcion',
        'prioridad': 'alta',
        'proyecto_id': str(proyecto_id),
        'epica_id': ''
    }, follow_redirects=True)

    assert response.status_code == 200
    assert "Historia &#34;Historia de Prueba Sin Epica&#34; creada exitosamente." in response.get_data(as_text=True)

    with client.application.app_context():
        from app.modelos import Epica
        historia = Epica.query.filter_by(nombre='Historia de Prueba Sin Epica').first()
        assert historia is not None
        assert historia.tipo == TipoEnum.STORY
        assert historia.epica_padre_id is None
        assert historia.proyecto_id == proyecto_id
