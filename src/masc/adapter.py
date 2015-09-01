import re
from masc.scraper import *
from masc.util import fetch_html


def mangafox(url):
    return MangafoxAdapter(url)


class MangafoxAdapter(SiteAdapter):
    url_pattern = re.compile(r"http://mangafox.\w+/manga/(?P<slug>[a-z_]+)((/v(?P<volume>[^/]+))?/c(?P<chapter>[^/]+)/(?P<page>[^/]+).html)?")

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
                       title=str(title.string) if title is not None else "Chapter {}".format(chap),
                       number=str(chap),
                       volume=str(vol) if vol is not None else str(chap))

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
