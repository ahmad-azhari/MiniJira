import os
from urllib.parse import urljoin

import requests
from behave import given, then, when


def _backend_base() -> str:
    return os.getenv("URL_BACKEND", "http://127.0.0.1:5000").rstrip("/") + "/"


def _session(context) -> requests.Session:
    if not hasattr(context, "http"):
        context.http = requests.Session()
        context.http.headers.update({"Accept": "application/json"})
    return context.http


def _abs_url(path: str) -> str:
    return urljoin(_backend_base(), path.lstrip("/"))


def _request(context, method: str, path: str, *, json_body=None, with_auth=True):
    s = _session(context) if with_auth else requests.Session()
    if not with_auth:
        s.headers.update({"Accept": "application/json"})
    url = _abs_url(path)
    resp = s.request(method=method, url=url, json=json_body, allow_redirects=False, timeout=10)
    context.last_response = resp
    return resp


def _tabla_a_dict(context):
    data = {}
    for row in context.table:
        data[row["campo"]] = row["valor"]
    return data


@given("el usuario está autenticado")
def step_usuario_autenticado(context):
    s = _session(context)
    url = _abs_url("/auth/login")
    resp = s.post(
        url,
        data={"nombre_usuario": "admin", "contrasena": "admin123"},
        allow_redirects=False,
        timeout=10,
    )
    context.last_auth_response = resp
    assert resp.status_code in (200, 302), (
        f"Login falló: status={resp.status_code}, body={resp.text[:300]}"
    )


@given("el usuario actual está autenticado")
def step_usuario_actual_autenticado(context):
    return step_usuario_autenticado(context)


@given('existe una tarea con ID "{tarea_id}"')
def step_existe_tarea_id(context, tarea_id):
    resp = _request(context, "GET", f"/api/tareas/{tarea_id}", with_auth=True)
    if resp.status_code == 404:
        create_resp = _request(
            context,
            "POST",
            "/api/tareas",
            json_body={
                "titulo": f"Tarea para tests",
                "descripcion": "Creada por el runner de pruebas",
                "estado": "pendiente",
            },
            with_auth=True,
        )
        assert create_resp.status_code in (200, 201), f"No se pudo crear tarea: {create_resp.status_code}"
        body = create_resp.json()
        created_id = body.get("id")
        context.created_task_id = created_id
        resp = _request(context, "GET", f"/api/tareas/{created_id}", with_auth=True)
    else:
        context.created_task_id = tarea_id
    
    assert resp.status_code == 200, (
        f"No se pudo asegurar la tarea: status={resp.status_code}"
    )


@given("existe una tarea creada por otro usuario")
def step_existe_tarea_otro_usuario(context):
    context.other_user_task_id = 2


@given("existe una tarea")
def step_existe_tarea(context):
    step_usuario_autenticado(context)
    create_resp = _request(
        context,
        "POST",
        "/api/tareas",
        json_body={
            "titulo": "Tarea para tests",
            "descripcion": "Creada por el runner de pruebas",
            "estado": "pendiente",
        },
        with_auth=True,
    )
    assert create_resp.status_code in (200, 201), f"No se pudo crear tarea: {create_resp.status_code}, body={create_resp.text}"
    body = create_resp.json()
    context.created_task_id = body.get("id")


@when('envía una solicitud POST a "{ruta}" con')
def step_post_con_tabla(context, ruta):
    _request(context, "POST", ruta, json_body=_tabla_a_dict(context), with_auth=True)


@when('envía una solicitud GET a "{ruta}"')
def step_get(context, ruta):
    _request(context, "GET", ruta, with_auth=True)


@when('envía una solicitud GET a "{ruta}" sin autenticación')
def step_get_sin_auth(context, ruta):
    _request(context, "GET", ruta, with_auth=False)


@when('envía una solicitud PUT a "{ruta}" con')
def step_put_con_tabla(context, ruta):
    if hasattr(context, 'created_task_id') and '/1' in ruta:
        ruta = ruta.replace('/1', f'/{context.created_task_id}')
    _request(context, "PUT", ruta, json_body=_tabla_a_dict(context), with_auth=True)


@when('envía una solicitud PUT a la tarea con')
def step_put_a_la_tarea(context):
    assert hasattr(context, 'created_task_id'), "No hay tarea creada en el contexto"
    ruta = f"/api/tareas/{context.created_task_id}"
    _request(context, "PUT", ruta, json_body=_tabla_a_dict(context), with_auth=True)


@when('envía una solicitud DELETE a "{ruta}"')
def step_delete(context, ruta):
    if hasattr(context, 'created_task_id') and '/1' in ruta:
        ruta = ruta.replace('/1', f'/{context.created_task_id}')
    _request(context, "DELETE", ruta, with_auth=True)


@when('envía una solicitud DELETE a la tarea')
def step_delete_la_tarea(context):
    assert hasattr(context, 'created_task_id'), "No hay tarea creada en el contexto"
    ruta = f"/api/tareas/{context.created_task_id}"
    _request(context, "DELETE", ruta, with_auth=True)


@when('envía una solicitud GET a la tarea')
def step_get_la_tarea(context):
    assert hasattr(context, 'created_task_id'), "No hay tarea creada en el contexto"
    ruta = f"/api/tareas/{context.created_task_id}"
    _request(context, "GET", ruta, with_auth=True)


@when('envía una solicitud DELETE a "{ruta}" de otro usuario')
def step_delete_otro_usuario(context, ruta):
    task_id = getattr(context, "other_user_task_id", 2)
    if hasattr(context, 'created_task_id') and '/1' in ruta:
        ruta = ruta.replace('/1', '')
    _request(context, "DELETE", f"{ruta.rstrip('/')}/{task_id}", with_auth=True)


@then("la respuesta debe tener código {codigo:d}")
def step_then_status(context, codigo):
    resp = getattr(context, "last_response", None)
    assert resp is not None, "No hay respuesta previa"
    assert resp.status_code == codigo, (
        f"Esperado {codigo}, obtuve {resp.status_code}. Body={resp.text[:400]}"
    )


@then('la respuesta debe contener una "{campo}"')
def step_then_contiene_campo(context, campo):
    resp = context.last_response
    assert resp is not None
    body = resp.json()
    assert campo in body, f"Campo '{campo}' no presente. Body={body}"


@then('la respuesta debe contener "{campo}" = "{valor}"')
def step_then_campo_igual(context, campo, valor):
    body = context.last_response.json()
    assert str(body.get(campo)) == valor, (
        f"Esperado {campo}={valor}, obtuve {campo}={body.get(campo)}"
    )


@then('el campo "{campo}" debe ser "{valor}"')
def step_then_campo_debe_ser(context, campo, valor):
    body = context.last_response.json()
    assert str(body.get(campo)) == valor, (
        f"Esperado {campo}={valor}, obtuve {campo}={body.get(campo)}"
    )


@then("la respuesta debe ser una lista JSON")
def step_then_lista_json(context):
    body = context.last_response.json()
    assert isinstance(body, list), f"Esperado lista, obtuve {type(body).__name__}: {body}"


@then("cada elemento debe contener")
def step_then_lista_elementos_contienen(context):
    body = context.last_response.json()
    assert isinstance(body, list), f"Esperado lista, obtuve {type(body).__name__}"
    required = [row["campo"] for row in context.table]
    if not body:
        return
    for idx, item in enumerate(body[:10]):
        for key in required:
            assert key in item, f"Elemento[{idx}] sin '{key}'. Item={item}"
