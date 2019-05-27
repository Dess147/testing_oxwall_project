import json
import os
import pytest
import allure
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeDriverManager
from webdriver_manager.microsoft import IEDriverManager

from db_connector import OxwallDB
from pages.pages import OxwallApp
from models import User

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

def pytest_addoption(parser):
    parser.addoption("--config", action="store", default="config.json",
                     help="config file")
    parser.addoption("--browser", action="store", default="Chrome",
                     help="browser for web tests")

@pytest.fixture(scope="session")
def config(request):
    file_name = request.config.getoption("--config")
    with open(os.path.join(PROJECT_DIR, file_name)) as f:
        return json.load(f)


@pytest.fixture()
def driver(request):
    """Open browser driver settings"""
    option = request.config.getoption("--browser")
    if option.lower() == "chrome":
        driver = webdriver.Chrome(ChromeDriverManager().install())
    elif option == "firefox":
        driver = webdriver.Firefox(executable_path=GeckoDriverManager().install())
    elif option == "edge":
        driver = webdriver.Edge(EdgeDriverManager().install())
    elif option == "ie":
        driver = webdriver.Ie(IEDriverManager().install())
    else:
        raise ValueError("Unrecognized browser {}".format(option))
    driver.implicitly_wait(5)
    driver.maximize_window()
    yield driver
    driver.quit()


@pytest.fixture(autouse=True)
def app(driver, base_url):
    driver.get(base_url)
    return OxwallApp(driver)

@pytest.fixture(scope="session")
def db(config):
    db = OxwallDB(config["db"])
    yield db
    db.close()

with open(os.path.join(PROJECT_DIR, "data", "user_data.json"), encoding="utf8") as f:
    user_data_list = json.load(f)

@pytest.fixture(params=user_data_list, ids=[str(user) for user in user_data_list])
def user(request, db):
    user = User(**request.param)
    db.create_user(user)
    yield user
    db.delete_user(user)

@allure.step("GIVEN I as a logged user")
@pytest.fixture()
def logged_user(app, config):
    user = User(**config["web"]["admin"], is_admin=True)
    app.main_page.login_as(user)
    yield user
    app.main_page.logout()
