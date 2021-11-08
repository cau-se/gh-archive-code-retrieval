"""Create a sample list of java files

This script analyses all java files, count the included tokens, and filters the files depending in the amount of tokens.
The result is a json file including the final sample.

Lower and upper bound for the filtering can be set in config.ini under section [06-sample]
"""
import configparser
import logging
import os
from multiprocessing import Pool

import javalang
import pandas as pd
from javalang.tokenizer import LexerError
from tqdm import tqdm


def process(file_name):
    """
    Opens a file and counts the tokens.
    Returns a object with filename and the token count depicted as len.
    If filename is a directory, a len of 0 will be returned.
    """
    if os.path.isdir(file_name) or not os.path.isfile(file_name):
        return {'filename': file_name, 'len': 0}
    with open(file_name, encoding="ISO-8859-1") as f:
        data = f.read()
    try:
        tokens = list(javalang.tokenizer.tokenize(data))
    except LexerError:
        tokens = []
    return {'filename': file_name, 'len': len(tokens)}


def main():
    config = configparser.ConfigParser()
    config.read('config.ini')

    upper = config['06-sample']['UpperBound']
    lower = config['06-sample']['LowerBound']

    logging.info('Load javafiles list')
    files = []
    with open('java-files.txt') as fp:
        for line in fp:
            files.append('git' + line[1:].replace('\n', ''))

    logging.info('Start tokenize processes')
    pool = Pool(processes=28)
    results = []
    for elem in tqdm(pool.imap_unordered(process, files), total=len(files)):
        results.append(elem)
    df = pd.DataFrame.from_dict(results)
    df.describe()
    df = df[((df['len'] > lower) & df['len'] < upper)]
    df.describe()
    df = df.sample(frac=0.5)
    train = df.sample(frac=0.7, random_state=42)
    test = df.drop(train.index)

    train.to_json('train-sample.json', orient='records')
    test.to_json('test-sample.json', orient='records')

if __name__ == "__main__":
    main()
