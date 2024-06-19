from stem import Signal
from stem.control import Controller
from selenium import webdriver
from selenium.webdriver.firefox.options import Options


# Обновления соединения Tor
def renew_connection():
    with Controller.from_port(port=9051) as controller:
        controller.authenticate(password="password")
        controller.signal(Signal.NEWNYM)


# Настройка Selenium для использования Tor
def get_tor_driver():
    options = Options()
    options.set_preference('network.proxy.type', 1)
    options.set_preference('network.proxy.socks', '127.0.0.1')
    options.set_preference('network.proxy.socks_port', 9050)
    options.set_preference('network.proxy.socks_remote_dns', True)
    driver = webdriver.Firefox(options=options)
    return driver

def main():
    # Пример использования Selenium через Tor
    driver = get_tor_driver()
    driver.get("https://api.ipify.org/")
    print(driver.page_source)
    driver.quit()

    renew_connection()

    # После обновления соединения IP будет другим
    driver = get_tor_driver()
    driver.get("https://api.ipify.org/")
    print(driver.page_source)
    driver.quit()


if __name__ == '__main__':
    main()
