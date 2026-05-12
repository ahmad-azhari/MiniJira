from selenium.webdriver.common.by import By

class NuevoProyectoPage:

    def __init__(self, driver):
        self.driver = driver

    def rellenar_formulario(self, nombre, descripcion):
        self.driver.find_element(By.ID, "nombre").send_keys(nombre)
        self.driver.find_element(By.ID, "descripcion").send_keys(descripcion)
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
