import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

@pytest.fixture
def driver():
    opciones = Options()
    opciones.add_argument("--disable-gpu")
    opciones.add_argument("--disable-dev-shm-usage")
    opciones.add_argument("--start-maximized")

    driver = webdriver.Chrome(options=opciones)
    driver.set_window_size(1920, 1080)

    yield driver
    driver.quit()
