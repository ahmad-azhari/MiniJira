def test_login_correcto(client):
    response = client.post('/login', data={
        'username': 'admin',
        'password': 'admin123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert "Inicio de sesión exitoso" in response.get_data(as_text=True)


def test_login_incorrecto(client):
    response = client.post('/login', data={
        'username': 'admin',
        'password': 'mal'
    }, follow_redirects=True)
    assert "Usuario o contraseña incorrectos." in response.get_data(as_text=True)
