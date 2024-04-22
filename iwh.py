import argparse
import configparser
import io
import json
import logging
import os.path
import requests
import sys
from chinese_calendar import is_workday
from datetime import datetime

logging_level = logging.DEBUG if os.getenv('DEBUG', '0') == '1' else logging.INFO
logging.basicConfig(level=logging_level, format='%(asctime)s.%(msecs)03d %(levelname)-8s %(name)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

conf_file = 'iwh.conf'
proj_file = 'projects.json'

base_dir = os.path.dirname(os.path.realpath(__file__))

def load_config():
    conf_path = os.path.join(base_dir, conf_file)
    if not os.path.exists(conf_path):
        raise Exception(f'config file not found: {conf_path}')

    config = configparser.ConfigParser()
    config.read(conf_path)

    if 'cred' not in config:
        raise Exception('missing [cred] section in config file')

    if 'username' not in config['cred']:
        raise Exception('missing username in [cred] section')
    if 'password' not in config['cred']:
        raise Exception('missing password in [cred] section')

    username = config['cred']['username']
    password = config['cred']['password']

    daily_hours = 8
    api_base = 'https://beacon.shinetechchina.com.cn'

    if 'iwh' in config:
        try:
            daily_hours = int(config['iwh']['dailyHours'])
        except:
            logging.warn('parse daily_hours failed in iwh.conf, use default: 8')

    if 'api' in config:
        api_base = config['api']['base']

    return dict(username=username, password=password, daily_hours=daily_hours, api_base=api_base)

def get_token(config: dict):
    url = config['api_base'] + '/AuthorityApi/Login'
    params = { 'username': config['username'], 'password': config['password'] }

    r = requests.get(url=url, params=params)
    if not r.status_code == 200:
        logging.debug(r.text)
        raise Exception('authentication failed')

    res = r.json()
    return dict(user_id=res['UserId'], token=res['TokenCode'])

def init_projects(config: dict):
    proj_path = os.path.join(base_dir, proj_file)
    if os.path.exists(proj_file):
        logging.warn(f'remove existing projects file: {proj_file}')
        os.remove(proj_file)

    tokens = get_token(config)

    url = config['api_base'] + '/WorkHoursApi/GetWorkHours'
    headers = { 'CRMApp-Token': tokens['token'] }
    r = requests.get(url=url, headers=headers)
    if not r.status_code == 200:
        logging.debug(r.text)
        raise Exception('failed to get projects')

    res = r.json()
    projects = [{
        'project_name'       : p['ProjectName'],
        'invoice_num'        : p['InvoiceNum'],
        'project_owner'      : p['ProjectOwner'],
        'total_workhours'    : p['TotalWorkHours'],

        # 'project_start_date': p['ProjectStartDate'],
        # 'project_end_date':   p['ProjectEndDate'],
        # 'current_hours':      p['CurrentHours'],

        'employee_id'           : p['EmployeeId'],
        'purchase_order_id'     : p['PurchaseOrderId'],
        'project_item_id'       : p['ProjectItemId'],
        'hours'                 : config['daily_hours'],
    } for p in res]

    with open(proj_path, 'w') as f:
        json.dump(projects, f, indent=4)

def load_projects():
    proj_path = os.path.join(base_dir, proj_file)
    if not os.path.exists(proj_path):
        raise Exception(f'projects file not found: {proj_path}')

    with open(proj_path) as f:
        projects = json.load(f)

    return projects

def submit_workhours(config:dict, creds:dict, project:dict):
    logging.info('submit workhours for project: %s', project['project_name'])
    logging.debug('project: %s', project)
    url = config['api_base'] + '/WorkHoursApi/SetWorkHour'
    data = {
        'EmployeeId': project['employee_id'],
        'PurchaseOrderId': project['purchase_order_id'],
        'ProjectItemId': project['project_item_id'],
        'Username': config['username'],
        'Hours': project['hours']
    }
    headers = { 'CRMApp-Token': creds['token'] }
    r = requests.post(url=url, data=data, headers=headers)
    if r.status_code == 200:
        logging.info('workhours submitted')
    else:
        logging.debug(r.text)
        logging.error('workhours submission failed')

def run_workhours(config: dict):
    if not is_workday(datetime.now().date()):
        logging.info('today is a holiday, skip workhours submission')
        return

    projects = load_projects()
    logging.debug('projects: %s', projects)

    tokens = get_token(config)
    for project in projects:
        if project['hours'] == 0:
            logging.info('skip project due to hours is 0: %s', project)
            continue

        submit_workhours(config, tokens, project)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='main.py',
        description='concurrent download files from ods',
        add_help=False
    )

    parser.add_argument('--help', action='help')

    sub_parsers = parser.add_subparsers(dest='command')
    sub_parsers.add_parser('init', help='init project details')
    sub_parsers.add_parser('run', help='run workhours')

    args = parser.parse_args()

    config = load_config()
    if args.command == 'init':
        init_projects(config)
    elif args.command == 'run':
        run_workhours(config)
    else:
        logging.fatal('invalid command')
        sys.exit(1)