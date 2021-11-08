""" Repository Information Retriever

Retrieve information for each repository regarding the license, used programming language,
and amount of Pull Request comments.
Parameters for Github's basic auth can be set in config.ini.
"""
import configparser
import json
import os
import time
from multiprocessing import Pool

import requests
from elasticsearch import Elasticsearch
from git import Repo
from requests.auth import HTTPBasicAuth
from tenacity import retry, wait_exponential, stop_after_attempt
from tqdm import tqdm


@retry(stop=stop_after_attempt(10), wait=wait_exponential(multiplier=1, min=5, max=60))
def get_lang_obj(lang_url, auth):
    temp = requests.get(lang_url, auth=auth)
    if temp.status_code != 200:
        return None
    lang_obj = temp.json()
    return lang_obj


def sort_lang_obj(lang_obj):
    return sorted(lang_obj.items(), key=lambda x: x[1], reverse=True)


def is_java_repo(lang_list):
    return len(list(filter(lambda x: x[0] == 'Java', lang_list[:3]))) > 0


def get_and_check_java_repo(repo_url, auth):
    obj = get_lang_obj(repo_url + '/languages', auth)
    if obj is None:
        return False
    sorted_obj = sort_lang_obj(obj)
    return is_java_repo(sorted_obj)


@retry(stop=stop_after_attempt(10), wait=wait_exponential(multiplier=1, min=5, max=60))
def elasticsearch_helper(es, index_name, body):
    """
    Small helper to exploit decorator
    """
    return es.search(index=index_name, body=body, size=1)


def save_data(java_repos):
    with open('results.json', 'w') as g:
        json.dump(java_repos, g)


def clone(data):
    url = data['git_url']
    Repo.clone_from(url, os.path.join('git', data['full_name'].replace('/', '-')))


def filter_license(data):
    list(filter(lambda x: x['license'] in ('mit', 'apache-2.0'), data))


def main():
    config = configparser.ConfigParser()
    config.read('config.ini')

    host = config['elasticsearch']['Host']
    port = config['elasticsearch']['Port']
    index_name = config['elasticsearch']['IndexName']

    auth_name = config['03-repoinfos']['AuthName']
    auth_password = config['03-repoinfos']['AuthPassword']

    es = Elasticsearch(host, port=port)

    pool = Pool(1)
    processes = []

    # Get list of all repos for 2020
    with open('comments.json') as f:
        data = json.load(f)

    aggs = data['aggregations']['types_count']
    buckets = aggs['buckets']
    auth = HTTPBasicAuth(auth_name, auth_password)
    java_repos = []

    body = '''
    {
      "_source": [
        "payload.pull_request.base.repo.license.key",
        "payload.pull_request.base.repo.git_url",
        "payload.pull_request.base.repo.full_name"
      ],
      "query": {
        "bool": {
          "must": [
            {
              "match": {
                "type": "PullRequestReviewCommentEvent"
              }
            },
            {
              "match": {
                "repo.url.keyword": "https://api.github.com/repos/elastic/kibana"
              }
            }
          ]
        }
      }
    }
    '''
    for elem in tqdm(buckets):
        key = elem['key']
        try:
            is_java = get_and_check_java_repo(key, auth)
            elem['isJava'] = is_java
            response = elasticsearch_helper(es, index_name, body.replace('***', key))
        except:
            save_data(java_repos)
            raise
        source = response['hits']['hits'][0]['_source']
        if 'payload' in source:
            elem['license'] = source['payload']['pull_request']['base']['repo']['license']['key']
        else:
            elem['license'] = None
        java_repos.append(elem)
        if elem['license'] in ('mit', 'apache-2.0'):
            processes.append(pool.apply_async(clone, source['payload']['pull_request']['base']['repo']))
        time.sleep(0.9)

    save_data(java_repos)
    for process in tqdm(processes):
        process.wait()

if __name__ == "__main__":
    main()
