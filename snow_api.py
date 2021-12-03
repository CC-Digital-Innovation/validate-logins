import configparser

import pysnow
import requests

# read and parse config file
config = configparser.ConfigParser()
config.read('config.ini')

# service now client
snow_client = pysnow.Client(instance=config['snow']['snow_instance'], user=config['snow']['api_user'], password=config['snow']['api_password'])
company_name = config['snow']['company']

def get_cis():
    '''Returns a list of all devices filtered by company'''
    cis = snow_client.resource(api_path='/table/cmdb_ci_docker_container')
    query = (
        pysnow.QueryBuilder()
        .field('company.name').equals(company_name)
        .AND().field('name').order_ascending()
        .AND().field('install_status').equals('1')      # Installed
        .OR().field('install_status').equals('101')     # Active
        .OR().field('install_status').equals('107')     # Duplicate installed
    )
    response = cis.get(query=query)
    return response.all()

def decrypt_password(sys_id):
    url = f'{config["snow"]["base_url"]}/{config["snow"]["decrypt_path"]}/{sys_id}/getcipassword'
    headers = {'Authorization': config['snow']['api_key']}
    response = requests.get(url, headers=headers)
    return response.json()['result']['fs_password']

def get_ci_url(sys_id):
    return f'{config["snow"]["base_url"]}/cmdb_ci?sys_id={sys_id}'