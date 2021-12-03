import configparser
import time

import paramiko
from loguru import logger

# read and parse config file
config = configparser.ConfigParser()
config.read('config.ini')

def check_ssh(hostname, username, password, port=22, initial_wait=0, interval=0, retries=3):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    time.sleep(initial_wait)

    for x in range(retries):
        try:
            client.connect(hostname, port, username, password)
        except paramiko.ssh_exception.AuthenticationException:
            logger.warning(f'Authentication failed for {username} at {hostname}.')
            if x+1 < retries:
                logger.warning(f'Trying again...({x+1})')
            time.sleep(interval)
        except (TimeoutError, paramiko.ssh_exception.NoValidConnectionsError):
            logger.warning(f'Failed to establish connection to host {hostname}.')
            if x+1 < retries:
                logger.warning(f'Trying again...({x+1})')
            time.sleep(interval)
        else:
            logger.debug(f'Login successful for {username} at {hostname}!')
            client.close()
            return True
    logger.error(f'Failed to validate for {username} at {hostname}.')
    return False
