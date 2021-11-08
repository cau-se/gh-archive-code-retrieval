""" Load data from archives to Elasticsearch

This script opens all archive files, extracts them, and loads the contained data to Elasticsearch sequentially.

To modify the parameter, see the config.ini file and the section [02-load].
"""
import configparser
import glob
import gzip
import json

import pandas as pd
from elasticsearch import Elasticsearch
from pandarallel import pandarallel


def main():
    config = configparser.ConfigParser()
    config.read('config.ini')

    pandarallel.initialize(nb_workers=int(config['02-load']['Worker']), progress_bar=True)

    host = config['elasticsearch']['Host']
    port = config['elasticsearch']['Port']
    index_name = config['elasticsearch']['IndexName']

    es = Elasticsearch(host, port=port)

    archives = pd.DataFrame(glob.glob(config['general']['ArchivePath'] + '*'))

    def load(filename):
        with gzip.open(filename) as f:
            lines = f.readlines()
            for line in lines:
                data = json.loads(line)
                es.index(index=index_name, body=data)
        return filename

    archives[0].parallel_apply(load)


if __name__ == "__main__":
    main()
