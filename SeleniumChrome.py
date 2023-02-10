from selenium import webdriver
from selenium.webdriver.chrome.options import Options

class ChromeDriver:
    def __init__(self):
        self.options = Options()
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--headless")
        self.options.add_argument("--disable-gpu")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--disable-extensions")
        self.options.add_argument("--disable-web-security")
        self.options.add_argument("--proxy-server=http://approxy.jpmchase.net:8443")
        self.options.add_argument("--proxy-bypass-list=<-loopback>")
        self.options.add_argument("--ignore-ssl-errors=true")
        self.options.add_argument("--remote-debugging-port=9222")
        self.options.binary_location = (
            "C:/ProgramData/Microsoft/AppV/Client/Integration/"
            "F3C7787E-1DDE-4016-9D20-E7CE9483587F/Root/VFS/ProgramFilesX64/"
            "Google/Chrome/Application/chrome.exe")

    def get_driver(self) -> webdriver.Chrome:
        """
        Loads selenium Chrome WebDriver

        :return: Chrome WebDriver
        :rtype: webdriver.Chrome
        """
        driver = webdriver.Chrome(
            executable_path="H:\jpmDesk\Desktop\Projects\ICM\chromedriver.exe", options=self.options)

        driver.implicitly_wait(4)
        return driver

if __name__ == '__main__':
    browser = ChromeDriver().get_driver()
