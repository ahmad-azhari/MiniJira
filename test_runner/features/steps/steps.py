from behave import given, when, then

@given("que el navegador está en la página inicial")
def step_navegador_pagina_inicial(context):
    pass

@when("el usuario ingresa credenciales de admin")
def step_ingresa_credenciales(context):
    pass

@when("hace clic en el botón Login")
def step_clic_login(context):
    pass

@then("se autentica exitosamente")
def step_autentica_exitosamente(context):
    pass

@then("se redirige al dashboard principal")
def step_redirige_dashboard(context):
    pass
