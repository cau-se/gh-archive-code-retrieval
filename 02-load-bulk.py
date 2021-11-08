""" Load data from archives to Elasticsearch

This script opens all archive files, extracts them, and loads the contained data to Elasticsearch sequentially.
In this script, the bulk method of Elasticsearch is used to boost performance.

To modify the parameter, see the config.ini file and the section [02-load].
"""
import configparser
import glob
import gzip
import json
import logging
import os

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from tenacity import *
from tqdm import tqdm


@retry(stop=stop_after_attempt(3), wait=wait_fixed(45))
def bulk_helper(es, data):
    """
    Just a small helper to simplify code and make use of the retry decorator.
    """
    bulk(es, data, max_retries=10, initial_backoff=5, chunk_size=2000)


def remove_already_processed_docs(pointer, file_list):
    index = file_list.index(pointer)
    return file_list[index+1:]


def main():
    config = configparser.ConfigParser()
    config.read('config.ini')

    host = config['elasticsearch']['Host']
    port = config['elasticsearch']['Port']
    index_name = config['elasticsearch']['IndexName']

    es = Elasticsearch(host, port=port)

    archives = glob.glob(config['general']['ArchivePath'] + '*')
    archives.sort()

    files_with_errors = []
    if os.path.exists('.loader_lastfile'):
        with open('.loader_lastfile', 'r') as f:
            last_file = f.readline().replace('\n', '')
        archives = remove_already_processed_docs(last_file, archives)

    for filename in tqdm(archives):
        with gzip.open(filename) as f:
            lines = f.readlines()

            def provide(lines):
                for idx, line in enumerate(lines):
                    try:
                        data = json.loads(line)
                    except:
                        files_with_errors.append({'file': filename, 'line': idx})
                        continue
                    yield {
                        "_index": index_name,
                        "_op_type": "update",
                        "_id": data['id'],
                        "doc": data,
                        "doc_as_upsert": True
                    }

            bulk_helper(es, provide(lines))
            # bulk(es, provide(), max_retries=10, initial_backoff=5, chunk_size=2000)
        with open('.loader_lastfile', 'w') as f:
            f.write(filename)

    os.remove('.loader_lastfile')
    logging.info('Finished')
    logging.info('{} errors occurred'.format(len(files_with_errors)))
    with open('02-errors.json', 'w') as f:
        json.dump(files_with_errors, f)


if __name__ == "__main__":
    main()
