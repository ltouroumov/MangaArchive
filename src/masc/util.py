import os.path
import requests
import hashlib
from bs4 import BeautifulSoup


def fetch_image(url):
    cache = str.join(os.path.sep, ['cache'] + list(chunkify(hashlib.sha1(url.encode('utf-8')).hexdigest(), 8)))

    if os.path.exists(cache):
        return open(cache, mode='rb').read()
    else:
        resp = requests.get(url)
        if resp.status_code != 200:
            raise FileNotFoundError("URL does not exist")

        os.makedirs(os.path.dirname(cache))
        open(cache, mode='wb+').write(resp.content)
        return resp.content


def fetch_html(url):
    resp = requests.get(url)
    if resp.status_code != 200:
        raise FileNotFoundError("URL does not exist")

    return BeautifulSoup(resp.text, "lxml")


def for_each(iterator, func):
    for item in iterator:
        func(item)


def chunkify(seq, len):
    """A generator to divide a sequence into chunks of n units."""
    while seq:
        yield seq[:len]
        seq = seq[len:]
