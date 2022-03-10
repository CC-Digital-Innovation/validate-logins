import configparser
import time
from pathlib import PurePath
from loguru import logger
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib3.exceptions import MaxRetryError

# read and parse config file
config = configparser.ConfigParser()
config_path = PurePath(__file__).parent.parent.parent/'config.ini'
config.read(config_path)

REMOTE_DRIVER = config['selenium']['remote_driver']
BROWSER = config['selenium']['browser']
MAX_WAIT_TIME = config['selenium'].getint('max_wait_time')
INITIAL_WAIT = config['selenium'].getfloat('initial_wait')
INTERVAL = config['selenium'].getfloat('interval')
ATTEMPTS = config['selenium'].getint('attempts')

def validate(url, username, password, max_wait_time=MAX_WAIT_TIME, initial_wait=INITIAL_WAIT, interval=INTERVAL, attempts=ATTEMPTS):
    '''Validates login credentials for UCS webpage.
    Args:
        url (str)
        username (str)
        password (str)
    Returns:
        True if logged in
    Raises:
        ValueError for unsupported browser, or failed to reach remote web driver
        TimeoutError for failed to find elements in browser
        ConnectionError for failed to reach website
    '''
    if BROWSER.lower() == 'firefox':
        options = webdriver.FirefoxOptions()
    elif BROWSER.lower() == 'chrome':
        options = webdriver.ChromeOptions()
    else:
        raise ValueError('Unsupported browser ' + BROWSER)

    logger.debug(f'Initial sleep for {initial_wait}')
    time.sleep(initial_wait)

    logger.info(f'Attempting to validate {username} at {url} (this may take a moment...).')
    for x in range(1, attempts + 1):
        # Connect to website
        try:
            logger.debug(f'Opening browser {url}...')
            driver = webdriver.Remote(command_executor=REMOTE_DRIVER, options=options)
            driver.set_page_load_timeout(MAX_WAIT_TIME)
            driver.get(url)
            logger.debug(f'{url} opened!')
        except MaxRetryError as e:
            logger.error(e)
            driver.quit()
            raise ValueError
        except (WebDriverException, TimeoutException) as e:
            logger.warning(e)
            driver.quit()
            if x < attempts:
                logger.info(f'Trying again...({x})')
                time.sleep(interval)
                continue
            else:
                logger.warning('Max retries reached.')
                raise ConnectionError

        # Attempt to login
        try:
            WebDriverWait(driver, max_wait_time).until(EC.frame_to_be_available_and_switch_to_it(0))
            logger.debug(f'Launching UCS manager...')
            WebDriverWait(driver, max_wait_time).until(EC.element_to_be_clickable((By.LINK_TEXT, 'Launch UCS Manager'))).click()
            driver.switch_to.default_content()

            logger.debug('Finding username input...')
            WebDriverWait(driver, max_wait_time).until(EC.visibility_of_element_located((By.NAME, 'username'))).send_keys(username)
            logger.debug('Username entered!')
            logger.debug('Finding password input...')
            WebDriverWait(driver, max_wait_time).until(EC.visibility_of_element_located((By.NAME, 'password'))).send_keys(password)
            logger.debug('Password entered!')
            logger.debug('Submitting input...')
            WebDriverWait(driver, max_wait_time).until(EC.element_to_be_clickable((By.ID, 'loginContainer_loginSubmit_label'))).click()
            # TODO Compare links to see if successfully logged in or errored. Currently can't tell if timed out due to login page or failed authentication
            logger.debug('Looking for login...')
            logged_in_test = WebDriverWait(driver, max_wait_time).until(EC.visibility_of_element_located((By.XPATH, "//b"))).text
        except TimeoutException as e:
            logger.warning(e)
            if x < attempts:
                logger.info(f'Trying again...({x})')
                time.sleep(interval)
            else:
                logger.warning('Max retries reached.')
                raise TimeoutError
        else:
            if 'Logged in as' in logged_in_test:
                logger.debug(f'Successful: {logged_in_test}')
                return True
            else:
                logger.debug(f'Failed. Logged in message: {logged_in_test}')
                return False
        finally:
            driver.quit()
