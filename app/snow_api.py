import configparser

import pysnow
import requests

# read and parse config file
config = configparser.ConfigParser()
config.read('config.ini')

SNOW_INSTANCE = config['snow']['snow_instance']
SNOW_USER = config['snow']['api_user']
SNOW_PASS = config['snow']['api_password']
SNOW_BASE_URL = config["snow"]["base_url"]
SNOW_DECRYPT_PATH = config["snow"]["decrypt_path"]
SNOW_API_KEY = config['snow']['api_key']

# service now client
SNOW_CLIENT = pysnow.Client(instance=SNOW_INSTANCE, user=SNOW_USER, password=SNOW_PASS)
COMPANY_NAME = config['snow']['company']

def get_cis():
    '''Returns a list of all devices filtered by company'''
    cis = SNOW_CLIENT.resource(api_path='/table/cmdb_ci_docker_container')
    query = (
        pysnow.QueryBuilder()
        .field('company.name').equals(COMPANY_NAME)
        .AND().field('name').order_ascending()
        .AND().field('install_status').equals('1')      # Installed
        .OR().field('install_status').equals('101')     # Active
        .OR().field('install_status').equals('107')     # Duplicate installed
    )
    response = cis.get(query=query)
    return response.all()

def decrypt_password(sys_id):
    url = f'{SNOW_BASE_URL}/{SNOW_DECRYPT_PATH}/{sys_id}/getcipassword'
    headers = {'Authorization': SNOW_API_KEY}
    response = requests.get(url, headers=headers)
    return response.json()['result']['fs_password']

def get_ci_url(sys_id):
    return f'{SNOW_BASE_URL}/cmdb_ci?sys_id={sys_id}'
