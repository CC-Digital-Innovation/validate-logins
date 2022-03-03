import configparser
import socket
import time
from pathlib import PurePath

from loguru import logger
from winrm.protocol import Protocol

# read and parse config file
config = configparser.ConfigParser()
config_path = PurePath(__file__).parent.parent/'config.ini'
config.read(config_path)

DEFAULT_RDP_PORT = config['rdp'].getint('default_rdp_port')
DEFAULT_WINRM_PORT = config['rdp'].getint('default_winrm_port')
INITIAL_WAIT = config['rdp'].getfloat('initial_wait')
INTERVAL = config['rdp'].getfloat('interval')
ATTEMPTS=config['rdp'].getint('attempts')

def svc_validate(host, port, initial_wait=INITIAL_WAIT, interval=INTERVAL, attempts=ATTEMPTS):
    '''Validates that service is running on specified port.
    Args:
        host (str): hostmane or IP address
        port (int): port number
    '''
    
    logger.debug(f'Initial sleep for {initial_wait}')
    time.sleep(initial_wait)

    logger.info(f'Attempting connection for {host}:{port}.')
    for x in range(1, attempts + 1):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host, port))
        except socket.error as e:
            logger.warning(f'Error on connect: {e}')
            if x < attempts:
                logger.info(f'Trying again...({x})')
                time.sleep(interval)
        else:
            logger.debug(f'{host} is reachable on port {port}')
            return True
        finally:
            s.close()
    logger.warning('Max retries reached.')
    return False


def auth_validate(host, port, transport, username, password, initial_wait=INITIAL_WAIT, interval=INTERVAL, attempts=ATTEMPTS):
    '''Validate login credentials with WinRM connection.
    Args:
        host (str): hostname or IP address
        port (int): WinRM port number
        transport (str): transport type
        username (str): username for auth
        password (str): password for auth
    '''  
    logger.debug(f'Initial sleep for {initial_wait}')
    time.sleep(initial_wait)

    p = Protocol(
        endpoint=f'http://{host}:{port}/wsman',
        transport=transport,
        username=username,
        password=password,
        server_cert_validation='ignore')
    # try opening shell
    logger.info(f'Attempting to open shell as {username}@{host}:{port}')
    for x in range(1, attempts + 1):
        try:
            shell_id = p.open_shell()
        except Exception as e:
            logger.warning(f'Error in validating: {e}')
            if x < attempts:
                logger.info(f'Trying again...({x})')
                time.sleep(interval)
        else:
            p.close_shell(shell_id)
            logger.info(f'Login successful for {username} at {host}:{port}')
            return True
    logger.warning(f'Max retires reached.')
    return False
    

def validate(host, username, password, rdp_port=DEFAULT_RDP_PORT, winrm_port=DEFAULT_WINRM_PORT, transport='ntlm', initial_wait=INITIAL_WAIT):
    '''Test RDP port before validating user credentials with WinRM'''
    if initial_wait:
        logger.debug(f'Initial sleep for {initial_wait}')
    time.sleep(initial_wait)

    if svc_validate(host, rdp_port):
        return auth_validate(host, winrm_port, transport, username, password)
    else:
        raise TimeoutError
