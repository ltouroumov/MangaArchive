import re
import requests
import argparse
import pickle
import os.path
import hashlib
from bs4 import BeautifulSoup
from ebooklib import epub


def for_each(iterator, func):
    for item in iterator:
        func(item)


def chunkify(seq, len):
    """A generator to divide a sequence into chunks of n units."""
    while seq:
        yield seq[:len]
        seq = seq[len:]


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


class ScraperEngine(object):

    @staticmethod
    def can_handle(url):
        raise NotImplementedError

    def __init__(self, url):
        self.base_url = url
        self.slug = None
        self.title = None
        self.cover_url = None

    def get_meta(self, manga_url):
        raise NotImplementedError

    def get_chapters(self, manga_url):
        raise NotImplementedError

    def get_pages(self, chapter):
        raise NotImplementedError

    def get_image(self, page):
        raise NotImplementedError

    def build_volume(self, volume):
        ebook = epub.EpubBook()
        ebook_id = '%s-v%s' % (self.slug, volume.number)
        ebook.set_identifier(ebook_id)
        ebook_title = "Volume {} - {}".format(volume.number, self.title)
        ebook.set_title(ebook_title)
        print("===", ebook_title, "===")
        # ebook.set_cover('cover.jpg', fetch_image(self.cover_url))

        spine_chapters = []
        for chapter in sorted(volume.chapters, key=lambda chap: chap.number):
            eb_chapter, images = self.build_chapter(chapter)
            ebook.add_item(eb_chapter)
            for_each(images, ebook.add_item)
            spine_chapters.append(eb_chapter)

        ebook.add_item(epub.EpubNav())

        ebook.toc = [epub.Section('Chapters')] + spine_chapters
        ebook.spine = ['nav'] + spine_chapters

        filename = ebook_id + ".epub"
        epub.write_epub(filename, ebook)
        print("Written", filename)

    def build_chapter(self, chapter):
        print("#", chapter.title)
        chap = epub.EpubHtml()
        chap.title = chapter.title
        chap.file_name = 'chap-%s.html' % chapter.number
        chap_html = list()
        images = list()

        for page in chapter.pages:
            img = epub.EpubImage()
            img.file_name = 'ch{}-p{}.jpg'.format(chapter.number, page.number)
            if page.image_url is None:
                page.image_url = self.get_image(page)
            img.content = fetch_image(page.image_url)
            chap_html.append('<img src="{}" />'.format(img.file_name))
            images.append(img)

        chap.content = str.join("\n", chap_html)
        return chap, images

    def run(self, rebuild_cache=False):
        self.get_meta(manga_url=self.base_url)

        cache_name = self.slug + '.cache'
        if not rebuild_cache and os.path.exists(cache_name):
            print("Loading from cache")
            volumes = pickle.load(open(cache_name, mode="rb"))
        else:
            print("Building cache")
            volumes = dict()
            chapters = self.get_chapters(manga_url=self.base_url)
            for chapter in chapters:
                pages = self.get_pages(chapter)
                for page in pages:
                    # page.image_url = self.get_image(page)
                    chapter.add_page(page)

                if chapter.volume not in volumes:
                    volumes[chapter.volume] = Volume(chapter.volume)
                volumes[chapter.volume].add_chapter(chapter)

            pickle.dump(volumes, open(cache_name, mode="wb+"))

        print("Building Volumes")
        for volume in sorted(volumes.values(), key=lambda vol: vol.number):
            self.build_volume(volume)
            pickle.dump(volumes, open(cache_name, mode="wb+"))
            pass


class Volume(object):
    def __init__(self, number):
        self.number = number
        self.chapters = list()

    def add_chapter(self, chapter):
        self.chapters.append(chapter)

    def __repr__(self):
        return r"Volume({}, chapters={})".format(self.number, len(self.chapters))


class Chapter(object):
    def __init__(self, url, title, number, volume=None):
        self.url = url
        self.title = title
        self.number = number
        self.volume = volume
        self.pages = list()

    def add_page(self, page):
        self.pages.append(page)

    def __repr__(self):
        return r"Chapter('{}', url='{}', number={}, volume={}, pages={})".format(self.title,
                                                                                 self.url,
                                                                                 self.number,
                                                                                 self.volume,
                                                                                 len(self.pages))


class Page(object):
    def __init__(self, url, number):
        self.url = url
        self.image_url = None
        self.number = number

    def __repr__(self):
        return r"Page(url='{}', number={})".format(self.url, self.number)


class MangafoxScraper(ScraperEngine):
    url_pattern = re.compile(r"http://mangafox.\w+/manga/(?P<slug>[a-z_]+)(/v(?P<volume>\w+)/c(?P<chapter>\d+)/(?P<page>\d+).html)?")

    @staticmethod
    def can_handle(url):
        return re.match(MangafoxScraper.url_pattern, url)

    def __init__(self, url):
        super().__init__(url)
        match = self.url_pattern.match(url)
        if match is None:
            raise RuntimeError("URL does not match mangafox pattern")

        self.slug = match.group('slug')

    def build_url(self, volume=None, chapter=None, page=None, root=False):
        if root:
            pattern = r"http://mangafox.me/manga/{slug}/"
        elif volume is None:
            pattern = r"http://mangafox.me/manga/{slug}/vTBD/c{chapter}/{page}.html"
        else:
            pattern = r"http://mangafox.me/manga/{slug}/v{volume}/c{chapter}/{page}.html"

        return pattern.format(slug=self.slug, volume=volume, chapter=chapter, page=page)

    def make_chapter(self, link):
        title = link.parent.find('span', 'title')
        match = self.url_pattern.match(link["href"])
        chap, vol = match.group('chapter', 'volume')
        return Chapter(url=link['href'],
                       title=str(title.string),
                       number=chap,
                       volume=vol)

    def make_page(self, option, chapter):
        page_no = int(option['value'])
        return Page(url=self.build_url(volume=chapter.volume, chapter=chapter.number, page=page_no),
                    number=page_no)

    def get_meta(self, manga_url):
        html = fetch_html(manga_url)
        self.title = html.find('h1').string
        self.cover_url = html.find('div','cover').img['src']

    def get_chapters(self, manga_url):
        html = fetch_html(manga_url)
        chapters_links = map(self.make_chapter,
                             html.find_all('a', "tips"))
        return list(chapters_links)

    def get_pages(self, chapter):
        html = fetch_html(chapter.url)
        page_numbers = filter(lambda page: page.number != 0,
                              map(lambda option: self.make_page(option, chapter),
                                  html.find('select', 'm').find_all('option')))
        return list(page_numbers)

    def get_image(self, page):
        html = fetch_html(page.url)
        return html.find('img', id='image')['src']


parser = argparse.ArgumentParser()
parser.add_argument('manga', metavar='url', help='URL of the manga')
parser.add_argument('--chapters', default=[], help="Specify chapters to build")
parser.add_argument('--rebuild', action='store_true', default=False, help="Rebuild chapter cache")
parser.add_argument('--scraper', default='auto', help='scraper engine to use (default: infer from url)')

args = parser.parse_args()

scrapers = [MangafoxScraper]
scraper = None

for scraper_cls in scrapers:
    if scraper_cls.can_handle(args.manga):
        scraper = scraper_cls(args.manga)

if scraper is None:
    print("Not matching scraper found")

scraper.run(args.rebuild)
