from selenium.webdriver.common.by import By

class DetalleProyectoPage:

    def __init__(self, driver):
        self.driver = driver

    def get_titulo(self):
        return self.driver.find_element(By.TAG_NAME, "h1").text.strip()

    def en_pagina_detalle(self):
        return "/proyecto/" in self.driver.current_url
