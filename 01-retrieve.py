"""Retrieve data from GH Archive

This script allows to download an arbitrary amount of GH Archive files.
Time ranges can be specified in the config.ini under [01-retrieve] with
shell-like ranges. See also: https://www.gharchive.org/

Ranges will be unfolded and all files downloaded correspondingly.
"""
import configparser
import logging
import re
import urllib.request
from datetime import datetime, timedelta
from itertools import product

import progressbar


bar_wrap = [None]
current_num = 0
max_num = 0
start_time = datetime.now()


def generate_combos(ranges):
    return product(*ranges)


def convert_to_range(group) -> range:
    start, end = group
    return range(int(start), int(end)+1)


def report_hook(count, block_size, total_size):
    bar = bar_wrap[0]
    if bar is None:
        bar = progressbar.ProgressBar(
            maxval=total_size,
            widgets=[
                'File #{} of {}: '.format(current_num+1, max_num),
                progressbar.Percentage(),
                ' ',
                progressbar.Bar(),
                ' ',
                'Total elapsed time: {}'.format(timedelta(seconds=(datetime.now()-start_time).seconds)),
            ])
        bar.start()
        bar_wrap[0] = bar
    bar.update(min(count * block_size, total_size))


def main():
    global bar_wrap, current_num, max_num, start_time
    config = configparser.ConfigParser()
    config.read('config.ini')

    url = config['01-retrieve']['URL']
    path = config['general']['ArchivePath']
    pattern = r'\{([0-9]*)\.\.([0-9]*)}'
    preformatted_url = re.sub(pattern.replace('*', '', 1), '{:d}', url)  # substitute patterns without leading zeros
    preformatted_url = re.sub(pattern, '{:02d}', preformatted_url)

    groups = re.findall(pattern, url)
    ranges = list(map(convert_to_range, groups))

    urls_to_retrieve = []
    for combo in generate_combos(ranges):
        urls_to_retrieve.append(preformatted_url.format(*combo))

    max_num = len(urls_to_retrieve)

    opener = urllib.request.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]  # Dirty hack, otherwise we get a 403, as GitHub blocks those
    urllib.request.install_opener(opener)

    for idx, url_to_retrieve in enumerate(urls_to_retrieve):
        current_num = idx
        filename = url_to_retrieve[url_to_retrieve.rfind('/'):]
        bar_wrap = [None]
        try:
            urllib.request.urlretrieve(url_to_retrieve, path + filename, reporthook=report_hook)
        except Exception as e:
            print(e, end=' at ')
            print(url_to_retrieve)
            continue

    logging.info('\nAll done')


if __name__ == "__main__":
    main()
