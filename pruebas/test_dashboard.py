import pytest
from pruebas.paginas.login_page import LoginPage
from pruebas.paginas.dashboard_page import DashboardPage
from pruebas.paginas.detalle_proyecto_page import DetalleProyectoPage
from pruebas.paginas.nuevo_proyecto_page import NuevoProyectoPage

@pytest.mark.selenium
def test_crear_y_ver_detalle_proyecto(driver):
    login = LoginPage(driver)
    login.load()
    login.login("admin", "admin123")

    dash = DashboardPage(driver)
    dash.load()

    dash.click_crear_proyecto()
    nuevo = NuevoProyectoPage(driver)
    nuevo.rellenar_formulario("Proyecto Selenium", "Descripción Selenium")

    dash.load()
    assert dash.click_proyecto("Proyecto Selenium"), "No se encontró el proyecto en el dashboard"

    detalle = DetalleProyectoPage(driver)
    assert detalle.en_pagina_detalle(), "No se abrió la página de detalle"
    assert detalle.get_titulo() == "Proyecto Selenium"
