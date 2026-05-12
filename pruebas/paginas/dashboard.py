from selenium.webdriver.common.by import By

class DashboardPage:
    URL = "http://localhost:5000/proyectos/"

    def __init__(self, driver):
        self.driver = driver

    def load(self):
        self.driver.get(self.URL)

    def click_proyecto(self, nombre):
        proyectos = self.driver.find_elements(By.CSS_SELECTOR, ".project-card h2")
        for p in proyectos:
            if p.text.strip() == nombre:
                p.click()
                return True
        return False

    def click_crear_proyecto(self):
        btn = self.driver.find_element(By.CSS_SELECTOR, ".btn.btn-primary.mb-3")
        btn.click()
