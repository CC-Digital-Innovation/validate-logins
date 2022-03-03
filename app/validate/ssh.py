import configparser
import socket
import time
from pathlib import PurePath

import paramiko
from loguru import logger

# read and parse config file
config = configparser.ConfigParser()
config_path = PurePath(__file__).parent.parent/'config.ini'
config.read(config_path)

DEFAULT_PORT=config['ssh'].getint('default_port')
INITIAL_WAIT=config['ssh'].getfloat('initial_wait')
INTERVAL=config['ssh'].getfloat('interval')
ATTEMPTS=config['ssh'].getint('attempts')

def validate(hostname, username, password, port=DEFAULT_PORT, initial_wait=INITIAL_WAIT, interval=INTERVAL, attempts=ATTEMPTS):
    logger.debug(f'Initial sleep for {initial_wait}')
    time.sleep(initial_wait)

    logger.info(f'Attemptting SSH at {username}@{hostname}:{port}.')
    for x in range(1, attempts + 1):
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(hostname, port, username, password)
        except paramiko.ssh_exception.AuthenticationException:
            logger.warning(f'Authentication failed for {username} at {hostname}.')
            return False
        except (TimeoutError, paramiko.ssh_exception.NoValidConnectionsError, socket.gaierror):
            logger.warning(f'Failed to establish connection to host {hostname}.')
            if x < attempts:
                logger.info(f'Trying again...({x})')
                time.sleep(interval)
            else:
                logger.warning('Max retries reached.')
                raise TimeoutError
        else:
            logger.info(f'Login successful for {username} at {hostname}!')
            return True
        finally:
            client.close()
    logger.warning('Max retries reached.')
    return False
