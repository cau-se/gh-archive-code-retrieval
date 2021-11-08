""" Repository cloner

This script clones all projects with a given list after a filter step.
Only projects with a certain activity and with Java as main language are cloned.
Parameters for authentication from [03-repoinfos] is used here.
"""
import configparser
import json
from git import Repo
import requests
from requests.auth import HTTPBasicAuth
from tqdm import tqdm
import os

def main():
    config = configparser.ConfigParser()
    config.read('config.ini')

    auth_name = config['03-repoinfos']['AuthName']
    auth_password = config['03-repoinfos']['AuthPassword']

    auth = HTTPBasicAuth(auth_name, auth_password)

    with open('results.json', 'r') as f:
        data = json.load(f)

    data = list(filter(lambda x: x['isJava'] and x['doc_count'] > 10, data))

    for elem in tqdm(data):
        temp = requests.get(elem['key'], auth=auth)
        if temp.status_code != 200:
            return None
        langObj = temp.json()
        url = langObj['git_url']
        Repo.clone_from(url, os.path.join('git', data['full_name'].replace('/', '-')))

if __name__ == "__main__":
    main()

