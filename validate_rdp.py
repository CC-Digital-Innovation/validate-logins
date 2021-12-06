import socket

from loguru import logger
from winrm.protocol import Protocol

def svc_validate(host, port):
    """Validates that service is running on specified host port.
    Args:
        host (str): hostmane or IP address
        port (int): port number
    """    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((host, port))
        success = "{} is reachable on port {}".format(host, port)
        logger.info(success)
        return True
    except socket.error as e:
        logger.error("Error on connect: %s" % e)
        return False
    finally:
        s.close()

def auth_validate(host, port, transport, username, password):
    """[summary]
    Args:
        host (str): hostname or IP address
        port (int): WinRM port number
        transport (str): transport type
        username (str): username for auth
        password (str): password for auth
    """    
    p = Protocol(
        endpoint='http://{}:{}/wsman'.format(host,port),
        transport=transport,
        username=username,
        password=password,
        server_cert_validation='ignore')
    # try opening shell
    try:
        shell_id = p.open_shell()
    except Exception as e:
        logger.error('Error in validating: %s' % e)
        return False
    
    # try running command
    try:
        command_id = p.run_command(shell_id, 'hostname')
        std_out, std_err, status_code = p.get_command_output(shell_id, command_id)
        p.cleanup_command(shell_id, command_id)
        logger.info(std_out.decode("utf-8"))
        if std_err:
            logger.error('Error on command: %s' % std_err.decode('utf-8'))
        logger.info(status_code)
        return True
    except Exception as e:
        logger.error('Exception on command: %s' % e)
        return False
    finally:
        p.close_shell(shell_id)
    

def check_rdp(host, username, password, rdp_port=3389, winrm_port=5985, transport='ntlm'):
    '''Test RDP port before checking validating user credentials'''
    if svc_validate(host, rdp_port):
        if auth_validate(host, winrm_port, transport, username, password) == 0:
            return True
        else:
            return False
    else:
        logger.error('Failed to make RDP connection.')
        return False