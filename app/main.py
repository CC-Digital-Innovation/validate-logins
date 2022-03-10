import configparser
import json
import logging.handlers
import requests
import sys
from pathlib import PurePath

from loguru import logger

import email_api
import snow_api
from validate import ssh, rdp
from validate.https import ucs

# read and parse config file
config = configparser.ConfigParser()
config_path = PurePath(__file__).parent/'config.ini'
config.read(config_path)

LOG_LEVEL = config['logger']['log_level'].upper()
SYSLOG = config['logger'].getboolean('syslog')
SYSLOG_HOST = config['logger']['syslog_host']
SYSLOG_PORT = config['logger'].getint('syslog_port')
COMPANY_NAME = config['snow']['company']

def main():
    logger.info('------------------------------------------------------------')
    logger.info(f'Login validation starting for {COMPANY_NAME}!')
    logger.info('Grabbing data from SNOW...')
    cis = snow_api.get_cis()
    logger.debug(json.dumps(cis[:3], sort_keys=True, indent=4))
    result = []
    for ci in cis:
        logger.info(f'Starting validation for device {ci["name"]}')
        ci_result = {
            'Name': ci['name'],
            'Link': snow_api.get_ci_url(ci['sys_id']),
            'Host': ''
        }
        if not ci['u_host_name'] and not ci['ip_address']:
            logger.warning(f'Hostname and IP address cannot be found for {ci["name"]}.')
            # added to preserve column order
            ci_result['Login 1'] = 'Error'
            ci_result['Access Method 1'] = ''
            ci_result['Note 1'] = 'Could not find hostname or IP address.'
            result.append(ci_result)
            continue
        # feature multiple access methods
        access_methods = [ci['u_primary_acces_method'], ci['u_secondary_access_method']]
        for i, access_method in enumerate(access_methods, start=1):
            logger.info(f'Checking {access_method} for device {ci["name"]}.')
            ci_result[f'Access Method {i}'] = access_method
            # validate ssh
            if access_method == 'SSH':
                if ci['u_host_name']:
                    ci_result['Host'] = ci['u_host_name']
                else:
                    ci_result['Host'] = ci['ip_address']
                try:
                    # check for custom port
                    if 'u_port' in ci and ci['u_port']:
                        login_result = ssh.validate(ci_result['Host'], ci['u_username'], snow_api.decrypt_password(ci['sys_id']), port=int(ci['u_port']))
                    else:
                        login_result = ssh.validate(ci_result['Host'], ci['u_username'], snow_api.decrypt_password(ci['sys_id']))
                    if login_result:
                        logger.info(f'Authentication with {ci_result["Host"]} successful for {ci["name"]}!')
                        ci_result[f'Login {i}'] = 'Success'
                    else:
                        logger.warning(f'Authentication with {ci_result["Host"]} failed for {ci["name"]}.')
                        ci_result[f'Login {i}'] = 'Failed'
                except TimeoutError:
                    logger.warning(f'Connection failed at {ci_result["Host"]}.')
                    ci_result[f'Login {i}'] = 'Error'
                    ci_result[f'Note {i}'] = f'Failed to establish connection to host {ci_result["Host"]}.'
            # validate rdp
            elif access_method == 'RDP':
                if ci['u_host_name']:
                    ci_result['Host'] = ci['u_host_name']
                else:
                    ci_result['Host'] = ci['ip_address']
                try:
                    # check for custom port
                    if 'u_port' in ci and ci['u_port']:
                        login_result = rdp.validate(ci_result['Host'], ci['u_username'], snow_api.decrypt_password(ci['sys_id']), rdp_port=int(ci['u_port']))
                    else:
                        login_result = rdp.validate(ci_result['Host'], ci['u_username'], snow_api.decrypt_password(ci['sys_id']))
                    if login_result:
                        logger.info(f'Authentication with {ci_result["Host"]} successful for {ci["name"]}!')
                        ci_result[f'Login {i}'] = 'Success'
                    else:
                        logger.warning(f'Authentication with {ci_result["Host"]} failed for {ci["name"]}.')
                        ci_result[f'Login {i}'] = 'Failed'
                except TimeoutError:
                    logger.warning(f'Connection failed at {ci_result["Host"]}.')
                    ci_result[f'Login {i}'] = 'Error'
                    ci_result[f'Note {i}'] = f'Failed to establish connection to host {ci_result["Host"]}.'
            elif access_method == 'HTTP' or access_method == 'HTTPS':
                # TODO model_number is a temporary solution. Figure out field to filter by device type, e.g. UCS, Unity, Recoverpoint, Datadomain, etc.
                if ci['u_host_name']:
                    ci_result['Host'] = ci['u_host_name']
                else:
                    ci_result['Host'] = ci['ip_address']
                if 'model_number' in ci and ci['model_number']:
                    if ci['model_number'] == 'UCS':
                        try:
                            url = f'{access_method.lower()}://{ci_result["Host"]}'
                            login_result = ucs.validate(url, ci['u_username'], snow_api.decrypt_password(ci['sys_id']))
                        except ValueError as e:
                            logger.error(e)
                            ci_result[f'Login {i}'] = 'Error'
                            ci_result[f'Note {i}'] = 'Server error.'
                        except TimeoutError:
                            logger.warning(f'Connection issue at {ci_result["Host"]}.')
                            ci_result[f'Login {i}'] = 'Error'
                            ci_result[f'Note {i}'] = f'Connection issue to host {ci_result["Host"]}.'
                        except ConnectionError:
                            logger.warning(f'Failed to reach {url}.')
                            ci_result[f'Login {i}'] = 'Error'
                            ci_result[f'Note {i}'] = f'Failed to reach {url}.'
                        else:
                            if login_result:
                                logger.info(f'Authentication with {ci_result["Host"]} successful for {ci["name"]}!')
                                ci_result[f'Login {i}'] = 'Success'
                            else:
                                logger.warning(f'Authentication with {ci_result["Host"]} failed for {ci["name"]}.')
                                ci_result[f'Login {i}'] = 'Failed'
                    else:
                        logger.error(f'Unsupported device type {ci["model_number"]}')
                        ci_result[f'Login {i}'] = 'Error'
                        ci_result[f'Note {i}'] = f'Device {ci["model_number"]} is not supported.'
                else:
                    logger.error('Missing device type.')
                    ci_result[f'Login {i}'] = 'Error'
                    ci_result[f'Note {i}'] = 'Missing device type'
            else:
                if access_method:
                    ci_result[f'Login {i}'] = 'Error'
                    ci_result[f'Note {i}'] = f'Access method \'{access_method}\' is not supported.'
                else:
                    # empty access method
                    ci_result[f'Login {i}'] = ''
                    ci_result[f'Note {i}'] = ''
        result.append(ci_result)
    if result:
        logger.info('Sending report...')
        try:
            logger.debug(result)
            email_api.send_report(result)
        except (requests.ConnectionError, requests.Timeout) as e:
            logger.error(f'Connection issue has occured: {e}')
        except requests.HTTPError as e:
            logger.error(f'Failed to send report: {e}')
        else:
            logger.info('Report sent!')
            logger.info(f'Login validation completed for {COMPANY_NAME}!')
    
def set_log_level(log_level):
    # remove default logger
    logger.remove()
    if log_level == 'QUIET':
        return
    logger.add(sys.stderr, level=log_level)
    if SYSLOG:
       logger.add(logging.handlers.SysLogHandler(address = (SYSLOG_HOST, SYSLOG_PORT)))

if __name__ == '__main__':
    set_log_level(LOG_LEVEL)
    with logger.catch():
        main()
