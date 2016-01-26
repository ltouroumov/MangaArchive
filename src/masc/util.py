import os.path
import requests
import hashlib
from bs4 import BeautifulSoup


DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.111 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, sdch',
    'Accept-Language': 'en-US,en;q=0.8,fr;q=0.6',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive'
}


class FetchError(Exception):
    def __init__(self, status, url):
        self.status = status
        self.url = url

    def __str__(self):
        return "FetchError({} at {})".format(self.status, self.url)


def fetch_cached(url):
    cache = str.join(os.path.sep, ['cache'] + list(chunkify(hashlib.sha1(url.encode('utf-8')).hexdigest(), 8)))

    if os.path.exists(cache):
        return open(cache, mode='rb').read()
    else:
        resp = requests.get(url, headers=DEFAULT_HEADERS)
        if resp.status_code != 200:
            raise FetchError(resp.status_code, url)

        os.makedirs(os.path.dirname(cache))
        open(cache, mode='wb+').write(resp.content)
        return resp.content


def fetch_html(url, cached=False):
    if cached:
        resp = str(fetch_cached(url))
    else:
        resp = requests.get(url, headers=DEFAULT_HEADERS)
        if resp.status_code != 200:
            raise FetchError(resp.status_code, url)

        resp = resp.text
    return BeautifulSoup(resp, "lxml")


def for_each(iterator, func):
    for item in iterator:
        func(item)


def chunkify(seq, len):
    """A generator to divide a sequence into chunks of n units."""
    while seq:
        yield seq[:len]
        seq = seq[len:]


def merge(*dicts):
    ret = dict()
    for dic in dicts:
        ret.update(dic)
    return ret
