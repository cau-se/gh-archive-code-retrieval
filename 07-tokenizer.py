"""Train a tokenizer with our java files.

This script uses the retrieved files to train a custom tokenizer.
"""
import argparse
import json
import logging
import os.path

from tokenizers import Tokenizer
from tokenizers.models import WordPiece
from tokenizers.pre_tokenizers import PreTokenizer
from tokenizers.pre_tokenizers import Whitespace
from tokenizers.trainers import WordPieceTrainer

from JavaPreTokenizer import JavaPreTokenizer


def main(file_name):
    tokenizer = Tokenizer(WordPiece(unk_token='[UNK]'))
    tokenizer.pre_tokenizer = PreTokenizer.custom(JavaPreTokenizer())
    with open('specials.json') as fp:
        special_tokens = json.load(fp)

    logging.info('loading file names')
    with open('train-sample.json') as fp:
        files = json.load(fp)
    with open('test-sample.json') as fp:
        files = files + json.load(fp)
    logging.info('commence training')

    mapped_files = list(map(lambda x: x['filename'] + 'utf-8', files))
    filtered_files = list(filter(lambda x: os.path.isfile(x), mapped_files))
    trainer = WordPieceTrainer(vocab_size=15000, special_tokens=special_tokens)
    tokenizer.train(filtered_files, trainer=trainer)
    tokenizer.pre_tokenizer = Whitespace()
    tokenizer.save(file_name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Train a tokenizer with our java files.')
    parser.add_argument('file_name', type=str,
                        help='The file name to which the tokenizer will be stored.')
    args = parser.parse_args()
    main(vars(args)['file_name'])
