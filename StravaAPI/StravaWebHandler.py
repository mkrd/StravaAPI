import os
import requests
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


class StravaWebHandler:
    def __init__(self):
        self.path = os.path.dirname(os.path.realpath(__file__))
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        options.add_argument('no-sandbox')
        options.add_experimental_option("prefs", {
            "download.default_directory" : "NUL",
            "download.prompt_for_download": False})
        self.driver = webdriver.Chrome(chrome_options=options)
        self.wait = WebDriverWait(self.driver, 20)
        self.cookies = {}


    def login(self, email, password):
        print("1. Weblogin to strava.com ... ")
        login_url = "https://www.strava.com/login"
        self.driver.get(login_url)
        self.wait.until(EC.presence_of_element_located((By.ID,"login-button")))
        self.driver.find_element_by_id("email").send_keys(email)
        self.driver.find_element_by_id("password").send_keys(password)
        self.driver.find_element_by_id("login-button").click()
        self.wait.until(EC.presence_of_element_located((By.ID,"athlete-profile")))
        # Save session cookies for logged in state.
        self.cookies = {c["name"]: c["value"] for c in self.driver.get_cookies()}
        print("1.1 Weblogin success!")


    # Go to the auth_url and click on the button with the id "authorize"
    def authorize(self, auth_url):
        print("Webhandler authorize")
        self.driver.get(auth_url)
        print(f"{auth_url=}")
        self.wait.until(EC.presence_of_element_located((By.ID, "authorize")))
        self.driver.find_element_by_id("authorize").click()



    # Download the TCX file with acitvity_id and save it under file_path.
    def download(self, acitvity_id, file_path):
        download_url = "https://www.strava.com/activities/" + acitvity_id + "/export_tcx"
        r = requests.get(download_url, cookies=self.cookies)
        r.raise_for_status()
        if r.status_code == 200:
            with open(file_path, "wb") as f:
                f.write(r.content)