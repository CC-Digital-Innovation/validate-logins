import configparser
from pathlib import PurePath
from loguru import logger
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# read and parse config file
config = configparser.ConfigParser()
config_path = PurePath(__file__).parent.parent.parent/'config.ini'
config.read(config_path)

REMOTE_DRIVER = config['selenium']['remote_driver']
BROWSER = config['selenium']['browser']
MAX_WAIT_TIME = config['selenium'].getint('max_wait_time')

def validate(url, username, password):
    if BROWSER.lower() == 'firefox':
        options = webdriver.FirefoxOptions()
    elif BROWSER.lower() == 'chrome':
        options = webdriver.ChromeOptions()
    else:
        raise ValueError('Unsupported browser ' + BROWSER)

    driver = webdriver.Remote(
                command_executor=REMOTE_DRIVER,
                options=options)

    try:
        logger.debug(f'Opening browser {url}...')
        driver.get(url)
        logger.debug(f'{url} opened!')
        WebDriverWait(driver, MAX_WAIT_TIME).until(EC.frame_to_be_available_and_switch_to_it(0))
        logger.debug(f'Launching UCS manager...')
        WebDriverWait(driver, MAX_WAIT_TIME).until(EC.element_to_be_clickable((By.LINK_TEXT, 'Launch UCS Manager'))).click()
        driver.switch_to.default_content()

        logger.debug('Finding username input...')
        WebDriverWait(driver, MAX_WAIT_TIME).until(EC.visibility_of_element_located((By.NAME, 'username'))).send_keys(username)
        logger.debug('Username entered!')
        logger.debug('Finding password input...')
        WebDriverWait(driver, MAX_WAIT_TIME).until(EC.visibility_of_element_located((By.NAME, 'password'))).send_keys(password)
        logger.debug('Password entered!')
        logger.debug('Submitting input...')
        WebDriverWait(driver, MAX_WAIT_TIME).until(EC.element_to_be_clickable((By.ID, 'loginContainer_loginSubmit_label'))).click()

        logger.debug('Looking for login...')
        logged_in_test = WebDriverWait(driver, MAX_WAIT_TIME).until(EC.visibility_of_element_located((By.XPATH, "//b"))).text

        if 'Logged in as' in logged_in_test:
            logger.debug(f'Successful: {logged_in_test}')
            return True
        else:
            logger.debug(f'Failed. Logged in message: {logged_in_test}')
    finally:
        driver.quit()
