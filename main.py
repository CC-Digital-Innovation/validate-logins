import configparser
import socket
import sys

from loguru import logger

import email_report
import snow_api
import validate_ssh
import validate_rdp

# read and parse config file
config = configparser.ConfigParser()
config.read('config.ini')

LOG_LEVEL = config['local']['log_level'].upper()

def main():
    cis = snow_api.get_cis()
    result = []
    for ci in cis:
        # notes is a newline-separated list of str
        ci_result = {
            'name': ci['name'],
            'link': snow_api.get_ci_url(ci['sys_id']),
            'note': []
        }
        if ci['u_host_name']:
            ci_result['host'] = ci['u_host_name']
        elif ci['ip_address']:
            logger.warning(f'Hostname cannot be found for {ci["name"]}. Trying IP address...')
            ci_result['host'] = ci['ip_address']
            ci_result['note'].append('Could not find hostname so IP address was used.')
        else:
            logger.warning(f'IP Address cannot be found for {ci["name"]}.')
            ci_result['host'] = ''
            ci_result['status'] = 'Error'
            ci_result['note'].append('Could not find hostname or IP address.')
            result.append(ci_result)
            continue
        # feature multiple access methods
        access_methods = [ci['u_primary_acces_method'], ci['u_secondary_access_method']]
        for i, access_method in enumerate(access_methods, start=1):
            ci_result[f'method{i}'] = access_method
            try:
                # validate ssh
                if access_method == 'SSH':
                    try:
                        # check for custom port
                        if 'u_port' in ci and ci['u_port']:
                            is_hostname_valid = validate_ssh.check_ssh(ci_result['host'], ci['u_username'], snow_api.decrypt_password(ci['sys_id']), port=ci['u_port'])
                        else:
                            is_hostname_valid = validate_ssh.check_ssh(ci_result['host'], ci['u_username'], snow_api.decrypt_password(ci['sys_id']))
                        if is_hostname_valid:
                            logger.info(f'Authentication with {ci_result["host"]} successful for {ci["name"]}!')
                            ci_result[f'status{i}'] = 'Success'
                        else:
                            logger.info(f'Authentication with {ci_result["host"]} failed for {ci["name"]}.')
                            ci_result[f'status{i}'] = 'Authentication failed'
                    except socket.gaierror as e:
                        logger.warning(f'Unable to resolve hostname: {ci_result["host"]}')
                        # try again with IP address
                        if ci_result['host'] != ci['ip_address']:
                            if ci['ip_address']:
                                # check for custom port
                                if 'u_port' in ci and ci['u_port']:
                                    is_hostname_valid = validate_ssh.check_ssh(ci['ip_address'], ci['u_username'], snow_api.decrypt_password(ci['sys_id']), port=ci['u_port'])
                                else:
                                    is_hostname_valid = validate_ssh.check_ssh(ci['ip_address'], ci['u_username'], snow_api.decrypt_password(ci['sys_id']))
                                if is_hostname_valid:
                                    logger.info(f'Authentication with {ci["ip_address"]} successful for {ci["name"]}!')
                                    ci_result[f'status{i}'] = 'Success'
                                else:
                                    logger.info(f'Authentication with {ci["ip_address"]} failed for {ci["name"]}.')
                                    ci_result[f'status{i}'] = 'Authentication failed'
                            else:
                                ci_result[f'status{i}'] = 'Error'
                                ci_result['note'].append('Unable to resolve hostname and IP address is empty.')
                # validate rdp
                elif access_method == 'RDP':
                    if ci['u_host_name']:
                        ci_result['host'] = ci['u_host_name']
                        if 'u_port' in ci and ci['u_port']:
                            is_hostname_valid = validate_rdp.check_rdp(ci_result['host'], ci['u_username'], snow_api.decrypt_password(ci['sys_id']), rdp_port=int(ci['u_port']))
                        else:
                            is_hostname_valid = validate_rdp.check_rdp(ci_result['host'], ci['u_username'], snow_api.decrypt_password(ci['sys_id']))
                        if is_hostname_valid:
                            logger.info(f'Authentication with {ci_result["host"]} successful for {ci["name"]}!')
                            ci_result[f'status{i}'] = 'Success'
                        else:
                            logger.info(f'Authentication with {ci_result["host"]} failed for {ci["name"]}.')
                            ci_result[f'status{i}'] = 'Authentication failed'
                else:
                    if access_method:
                        ci_result[f'status{i}'] = 'Error'
                        ci_result['note'].append(f'Access method \'{access_method}\' is not supported.')
                    else:
                        # empty access method
                        ci_result[f'status{i}'] = ''
            except Exception as e:
                logger.exception(f'Uncaught exception: {e}')
                ci_result[f'status{i}'] = f'Unknown error for {access_method}'
                ci_result['note'].append(str(e))
        result.append(ci_result)
    if result:
        email_report.send_validate_report(result)
    

if __name__ == '__main__':
    with logger.catch():
        # remove default logger
        logger.remove()
        if LOG_LEVEL != 'QUIET':
            logger.add(sys.stderr, level=LOG_LEVEL)
        main()
