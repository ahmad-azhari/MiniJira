import os
from urllib.parse import urljoin

from behave import given, then, when
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


def _backend_base() -> str:
    return os.getenv("URL_BACKEND", "http://127.0.0.1:5000").rstrip("/") + "/"


def _abs_url(path: str) -> str:
    return urljoin(_backend_base(), path.lstrip("/"))


@given("el usuario está en la página de login")
def step_usuario_pagina_login(context):
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--proxy-server='direct://'")
    chrome_options.add_argument("--proxy-bypass-list=*")
    chrome_options.add_argument("--window-size=1920,1080")
    
    context.driver = webdriver.Chrome(options=chrome_options)
    context.driver.get(_abs_url("/auth/login"))


@when('ingresa nombre de usuario "{nombre}"')
def step_ingresa_nombre_usuario(context, nombre):
    WebDriverWait(context.driver, 10).until(
        EC.presence_of_element_located((By.NAME, "nombre_usuario"))
    )
    input_field = context.driver.find_element(By.NAME, "nombre_usuario")
    input_field.clear()
    input_field.send_keys(nombre)


@when('ingresa contraseña "{contrasena}"')
def step_ingresa_contrasena(context, contrasena):
    WebDriverWait(context.driver, 10).until(
        EC.presence_of_element_located((By.NAME, "contrasena"))
    )
    input_field = context.driver.find_element(By.NAME, "contrasena")
    input_field.clear()
    input_field.send_keys(contrasena)


@when("hace clic en el botón Login")
def step_clic_login(context):
    WebDriverWait(context.driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
    )
    login_button = context.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    context.driver.execute_script("arguments[0].click();", login_button)


@then("es autenticado exitosamente")
def step_autenticado_exitosamente(context):
    WebDriverWait(context.driver, 10).until(
        EC.url_contains("/proyectos")
    )
    current_url = context.driver.current_url
    assert "/proyectos" in current_url or "/" in current_url, (
        f"No se redirigió correctamente. URL actual: {current_url}"
    )


@then("es redirigido al dashboard principal")
def step_redirigido_dashboard(context):
    WebDriverWait(context.driver, 10).until(
        EC.url_contains("/proyectos")
    )
    current_url = context.driver.current_url
    assert "/proyectos" in current_url, (
        f"No se redirigió al dashboard. URL actual: {current_url}"
    )


@then('se muestra mensaje de error "{mensaje}"')
def step_muestra_mensaje_error(context, mensaje):
    WebDriverWait(context.driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".alert, .text-danger, .invalid-feedback"))
    )
    page_text = context.driver.find_element(By.TAG_NAME, "body").text
    assert mensaje in page_text, (
        f"No se encontró el mensaje '{mensaje}' en la página."
    )


def after_scenario(context, scenario):
    if hasattr(context, "driver"):
        context.driver.quit()
