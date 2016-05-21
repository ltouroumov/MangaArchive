import re
import json
from masc.scraper import *
from masc.util import fetch_html


def auto(url):
    if 'mangafox.me' in url:
        return MangafoxAdapter(url)
    if 'http://dynasty-scans.com/' in url:
        return DynastyScansAdapter(url)
    else:
        raise RuntimeError("Unkown adapter")


def mangafox(url):
    return MangafoxAdapter(url)


class MangafoxAdapter(SiteAdapter):
    url_pattern = re.compile(r"http://mangafox.\w+/manga/(?P<slug>[a-z0-9_]+)((/v(?P<volume>[^/]+))?/c(?P<chapter>[^/]+)/((?P<page>[^/]+).html)?)?")

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
            pattern = r"http://mangafox.me/manga/{slug}/c{chapter}/{page}.html"
        else:
            pattern = r"http://mangafox.me/manga/{slug}/v{volume}/c{chapter}/{page}.html"

        return pattern.format(slug=self.slug, volume=volume, chapter=chapter, page=page)

    def make_chapter(self, link):
        title = link.parent.find('span', 'title')
        url = link['href']
        match = self.url_pattern.match(url)
        chap, vol = match.group('chapter', 'volume')
        if chap is None:
            raise RuntimeError("{} does not contain a chapter number".format(url))
        return Chapter(url=link['href'],
                       title=str(title.string) if title is not None else "Chapter {}".format(chap),
                       number=str(chap),
                       volume=str(vol) if vol is not None else None)

    def make_page(self, option, chapter):
        page_no = int(option['value'])
        return Page(url=self.build_url(volume=chapter.volume, chapter=chapter.number, page=page_no),
                    number=page_no)

    def get_meta(self):
        html = fetch_html(self.manga_url)
        meta = Metadata(slug=self.slug, title=str(html.find('h1').string))
        meta.cover_url = str(html.find('div', 'cover').img['src'])
        return meta

    def get_chapters(self):
        html = fetch_html(self.manga_url)
        chapters_links = map(self.make_chapter,
                             html.find_all('a', "tips"))
        return list(chapters_links)

    def get_pages(self, chapter):
        html = fetch_html(chapter.url)
        select_tag = html.find('select', 'm')
        if select_tag is None:
            raise RuntimeError("{} does not contain a select.m".format(chapter.url))
        page_numbers = filter(lambda page: page.number != 0,
                              map(lambda option: self.make_page(option, chapter),
                                  select_tag.find_all('option')))
        return list(page_numbers)

    def get_image(self, page):
        html = fetch_html(page.url)
        img = html.find('img', id='image')
        if img is None:
            raise RuntimeError("{} does not contain an img#image".format(page.url))

        return img['src']


class DynastyScansAdapter(SiteAdapter):
    url_pattern = re.compile(r"http://dynasty-scans.com/series/(?P<slug>[a-zA-Z0-9_]+)")

    def __init__(self, url):
        super().__init__(url)
        match = self.url_pattern.match(url)
        if match is None:
            raise RuntimeError("URL does not match dynasty-scans pattern")

        self.slug = match.group('slug')

    def build_url(self, path):
        pattern = r"http://dynasty-scans.com{path}"
        return pattern.format(path=path)

    def get_meta(self):
        html = fetch_html(self.manga_url)
        meta = Metadata(slug=self.slug, title=str(html.find('h2', 'tag-title').b))
        meta.cover_url = str(html.find('img', 'thumbnail')['src'])

        return meta

    def get_chapters(self):
        html = fetch_html(self.manga_url)
        chapters_tag = html.find('dl', 'chapter-list')
        current_volume = '00'
        index = 1
        chapters = list()
        for tag in chapters_tag:
            if tag.name == 'dt':
                _, num = str(tag.string).split(' ', maxsplit=1)
                current_volume = num
            elif tag.name == 'dd':
                url = tag.a['href']
                chapter = Chapter(url=url, title=str(tag.a.string), number=index, volume=current_volume)
                chapters.append(chapter)
                index += 1

        return chapters

    def get_pages(self, chapter):
        html = fetch_html(self.build_url(path=chapter.url))
        script = str(html.find(lambda el: el.name == 'script' and not el.has_attr('src') and 'pages' in str(el)))

        start_idx = script.find('var pages = [')
        end_idx = script.rfind(';')

        json_str = script[start_idx + 12:end_idx]
        json_obj = json.loads(json_str)
        pages = list()
        page_num = 1
        for page_obj in json_obj:
            pages.append(Page(url=self.build_url(chapter.url + "#" + page_obj['name']),
                              number=page_num,
                              image_url=self.build_url(page_obj['image'])))
            page_num += 1

        return pages

    def get_image(self, page):
        return page.image_url
