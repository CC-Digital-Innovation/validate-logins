import configparser
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
        ci_result = {
            'name': ci['name'],
            'link': snow_api.get_ci_url(ci['sys_id']),
            'user': ci['u_username'],
            'host': ''
        }
        try:
            # validate ssh
            if ci['u_primary_acces_method'] == 'SSH' or ci['u_secondary_access_method'] == 'SSH':
                if ci['u_host_name']:
                    ci_result['host'] = ci['u_host_name']
                    if 'u_port' in ci and ci['u_port']:
                        is_hostname_valid = validate_ssh.check_ssh(ci['u_host_name'], ci['u_username'], snow_api.decrypt_password(ci['sys_id']), port=ci['u_port'])
                    else:
                        is_hostname_valid = validate_ssh.check_ssh(ci['u_host_name'], ci['u_username'], snow_api.decrypt_password(ci['sys_id']))
                    if is_hostname_valid:
                        logger.info(f'Authentication with {ci["u_host_name"]} successful for {ci["name"]}!')
                        ci_result['status'] = 'Success'
                    else:
                        logger.info(f'Authentication with {ci["u_host_name"]} failed for {ci["name"]}.')
                        ci_result['status'] = 'Authentication failed'
                else:
                    logger.warning(f'Hostname cannot be found for {ci["name"]}. Trying IP address...')
                    if ci['ip_address']:
                        ci_result['host'] = ci['ip_address']
                        if 'u_port' in ci and ci['u_port']:
                            is_ip_address_valid = validate_ssh.check_ssh(ci['u_host_name'], ci['u_username'], snow_api.decrypt_password(ci['sys_id']), port=ci['u_port'])
                        else:
                            is_ip_address_valid = validate_ssh.check_ssh(ci['ip_address'], ci['u_username'], snow_api.decrypt_password(ci['sys_id']))
                        if is_ip_address_valid:
                            logger.info(f'Authentication with {ci["ip_address"]} successful for {ci["name"]}!')
                            ci_result['status'] = 'Success'
                        else:
                            logger.info(f'Authentication with {ci["ip_address"]} failed for {ci["name"]}.')
                            ci_result['status'] = 'Authentication failed'
                            result.append({'name':ci['name'], 'host':ci[''], 'user':ci['u_username'], 'status':'Authentication failed'})
                    else:
                        logger.warning(f'IP Address cannot be found for {ci["name"]}.')
                        ci_result['host'] = ci['ip_address']
                        ci_result['status'] = 'Could not find hostname or IP address.'
            elif ci['u_primary_acces_method'] == 'RDP' or ci['u_secondary_access_method'] == 'RDP':
                if ci['u_host_name']:
                    ci_result['host'] = ci['u_host_name']
                    if 'u_port' in ci and ci['u_port']:
                        is_hostname_valid = validate_rdp.check_rdp(ci['u_host_name'], ci['u_username'], snow_api.decrypt_password(ci['sys_id']), rdp_port=int(ci['u_port']))
                    else:
                        is_hostname_valid = validate_rdp.check_rdp(ci['u_host_name'], ci['u_username'], snow_api.decrypt_password(ci['sys_id']))
                    if is_hostname_valid:
                        logger.info(f'Authentication with {ci["u_host_name"]} successful for {ci["name"]}!')
                        ci_result['status'] = 'Success'
                    else:
                        logger.info(f'Authentication with {ci["u_host_name"]} failed for {ci["name"]}.')
                        ci_result['status'] = 'Authentication failed'
                else:
                    logger.warning(f'Hostname cannot be found for {ci["name"]}. Trying IP address...')
                    if ci['ip_address']:
                        ci_result['host'] = ci['ip_address']
                        if 'u_port' in ci and ci['u_port']:
                            is_ip_address_valid = validate_rdp.check_rdp(ci['u_host_name'], ci['u_username'], snow_api.decrypt_password(ci['sys_id']), rdp_port=int(ci['u_port']))
                        else:
                            is_ip_address_valid = validate_rdp.check_rdp(ci['ip_address'], ci['u_username'], snow_api.decrypt_password(ci['sys_id']))
                        if is_ip_address_valid:
                            logger.info(f'Authentication with {ci["ip_address"]} successful for {ci["name"]}!')
                            ci_result['status'] = 'Success'
                        else:
                            logger.info(f'Authentication with {ci["ip_address"]} failed for {ci["name"]}.')
                            ci_result['status'] = 'Authentication failed'
                            result.append({'name':ci['name'], 'host':ci[''], 'user':ci['u_username'], 'status':'Authentication failed'})
                    else:
                        logger.warning(f'IP Address cannot be found for {ci["name"]}.')
                        ci_result['host'] = ci['ip_address']
                        ci_result['status'] = 'Could not find hostname or IP address.'
        except Exception as e:
            logger.exception(f'Uncaught exception: {e}')
            ci_result['status'] = f'Unknown error: {e}'
        finally:
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
