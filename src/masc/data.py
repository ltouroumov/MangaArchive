
class Metadata(object):
    def __init__(self, title, slug):
        self.title = title
        self.slug = slug
        self.cover_url = None


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
        return r"Page(url='{}', number={}, image_url='{}')".format(self.url, self.number, self.image_url)
