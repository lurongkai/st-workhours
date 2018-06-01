import requests
import sys
import io
import os.path
import configparser
import json
import datetime

confFile = './iwh.conf'
projectsFile = './projects.json'
mobileBase = 'http://123.56.176.64:88'

username = ''
password = ''
dailyHours = 8

def checkHolidays():
    now = datetime.datetime.now()
    nowStr = now.strftime('%Y%m%d')
    r = requests.get(url='http://api.goseek.cn/Tools/holiday', params={'date': nowStr})
    if not r.status_code == 200:
        print('holiday api error')
        sys.exit(1)
    res = r.json()
    if not res['data'] == 0:
        print('today is holiday, exit...')
        sys.exit(0)
    else:
        print('today is work day, continue')

def loadCreds():
    global username
    global password
    global dailyHours

    if not os.path.exists(confFile):
        return
    config = configparser.ConfigParser()
    config.read(confFile)

    if 'cred' not in config:
        print('[cred] section missing')
        return
    username = config['cred']['username']
    password = config['cred']['password']

    if 'iwh' in config:
        try:
            dailyHours = int(config['iwh']['dailyHours'])
        except:
            print('parse iwh-daily failed, use default: 8')

def getToken():
    url = mobileBase + '/AuthorityApi/Login'
    params = { 'username': username, 'password': password }
    r = requests.get(url=url, params=params)
    if not r.status_code == 200:
        print('authentication failed, exit...')
        sys.exit(1)
    res = r.json()
    return dict(userId=res['UserId'], token=res['TokenCode'])

def loadProjects(cred):
    projects = []
    if os.path.exists(projectsFile):
        with open(projectsFile) as f:
            projects = json.load(f)
        return projects
    projects = getProjects(cred)
    preparingProjects(projects)
    return projects

def getProjects(cred):
    url = mobileBase + '/WorkHoursApi/GetWorkHours'
    headers = { 'CRMApp-Token': cred['token'] }
    r = requests.get(url=url, headers=headers)
    res = r.json()
    return res

def preparingProjects(projects):
    projects = map(lambda p: {
        'ProjectName'       : p['ProjectName'],
        'InvoiceNum'        : p['InvoiceNum'],
        'ProjectOwner'      : p['ProjectOwner'],
        'TotalWorkHours'    : p['TotalWorkHours'],
        
        # 'ProjectStartDate': p['ProjectStartDate'],
        # 'ProjectEndDate': p['ProjectEndDate'],
        # 'CurrentHours': p['CurrentHours'],

        'EmployeeId'        : p['EmployeeId'],
        'PurchaseOrderId'   : p['PurchaseOrderId'],
        'ProjectItemId'     : p['ProjectItemId'],
        'Hours'             : dailyHours
    }, projects)
    projects = list(projects)

    if len(projects) == 0:
        print('no projects found, exit...')
        sys.exit(0)

    with open(projectsFile, 'w') as f:
        json.dump(projects, f, ensure_ascii=False, indent=4)
    if len(projects) > 1:
        print('found multiple projects.')
        print('please manually adjust workhours for each projects in setting file: projects.json')
        print('exit...')
        sys.exit(0)

def setWorkhours(project, cred):
    msg = "submit workhous for [{}]: {}h".format(project['ProjectName'], project['Hours'])
    print(msg)
    url = mobileBase + '/WorkHoursApi/SetWorkHour'
    data = {
        'EmployeeId': project['EmployeeId'],
        'PurchaseOrderId': project['PurchaseOrderId'],
        'ProjectItemId': project['ProjectItemId'],
        'Username': username,
        'Hours': project['Hours']
    }
    headers = { 'CRMApp-Token': cred['token'] }
    r = requests.post(url=url, data=data, headers=headers)
    if r.status_code == 200:
        print('workhours submitted.')
    else:
        print('error occurred, exit...')
        sys.exit(1)

if __name__ == '__main__':
    checkHolidays()
    loadCreds()
    cred = getToken()
    projects = loadProjects(cred)
    for project in projects:
        if project['Hours'] == 0:
            continue
        setWorkhours(project, cred)