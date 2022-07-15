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

def validate(hostname, username, password, port=DEFAULT_PORT):
    logger.debug(f'Attemptting SSH at {username}@{hostname}:{port}.')
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname, port, username, password)
    except paramiko.ssh_exception.AuthenticationException:
        logger.warning(f'Authentication failed for {username} at {hostname}.')
        return False
    except (TimeoutError, paramiko.ssh_exception.NoValidConnectionsError, socket.gaierror):
        logger.warning(f'Failed to establish connection to host {hostname}.')
        raise TimeoutError
    else:
        logger.debug(f'Login successful for {username} at {hostname}!')
        return True
    finally:
        client.close()
    return False
