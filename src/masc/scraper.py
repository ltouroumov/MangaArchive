import pickle
from multiprocessing import Pool
from masc.util import *
from pprint import pprint


class SiteAdapter(object):
    """
    Abstracts the website for the scraper
    """
    def __init__(self, url):
        self.manga_url = url

    def get_meta(self):
        """
        Fetch metadata from manga index
        :return: Metadata
        """
        raise NotImplementedError

    def get_chapters(self):
        """
        Return the list of `Chapter` objects
        :return: [Chapter]
        """
        raise NotImplementedError

    def get_pages(self, chapter):
        """
        Return the list of `Page` objects for `chapter`
        :param chapter: Chapter
        :return: [Page]
        """
        raise NotImplementedError

    def get_image(self, page):
        """
        Get the image url for `page`
        :param page: Page
        :return: image_url
        """
        raise NotImplementedError


class FormatAdapter(object):
    def __init__(self, adapter):
        self.adapter = adapter

    def file_format(self):
        """
        Return the file extension for this adapter
        :return: a string
        """
        raise NotImplementedError

    def build_volume(self, filename, volume, metadata):
        """
        Build a volume and save it to disk
        (this method must be thread-safe)

        :param filename: Target filename
        :param volume: Volume descriptor
        :param metadata: Series metadata
        """
        raise NotImplementedError


class ScraperEngine(object):
    """
    Scrape and build an ebook per volume
    """

    def __init__(self, adapter, format):
        """
        Creates the scraping engine

        :param adapter: SiteAdapter instance
        :param format: FormatAdapter instance
        """
        self.adapter = adapter
        self.format = format
        self.metadata = None
        self.dir = '.'

    def build_volume(self, volume):
        """
        Build an ebook for a volume

        :param volume: Volume object to build from
        :return: None
        """
        try:
            ebook_id = '%s-v%s' % (self.metadata.slug, volume.number)
            filename = os.path.join(self.dir, ebook_id + self.format.file_format())
            try:
                os.makedirs(self.dir)
            except FileExistsError:
                pass

            if os.path.exists(filename):
                print(filename, "already exists")
                return

            self.format.build_volume(filename, volume, self.metadata)

            print("Written", filename)
        except Exception as ex:
            import traceback
            print("Exception in build_volume")
            traceback.print_exc()

    def run(self, args):
        if args.out is not None:
            self.dir = args.out

        self.metadata = self.adapter.get_meta()

        cache_name = self.metadata.slug + '.cache'
        if not args.rebuild and os.path.exists(cache_name):
            print("Loading from cache")
            volumes = pickle.load(open(cache_name, mode="rb"))
        else:
            print("Building cache")
            volumes = dict()
            chapters = self.adapter.get_chapters()
            for chapter in chapters:
                pages = self.adapter.get_pages(chapter)
                for page in pages:
                    # page.image_url = self.get_image(page)
                    chapter.add_page(page)

                if chapter.volume not in volumes:
                    volumes[chapter.volume] = Volume(chapter.volume)
                volumes[chapter.volume].add_chapter(chapter)

            pickle.dump(volumes, open(cache_name, mode="wb+"))

        print("Building Volumes")
        sorted_volumes = sorted(volumes.values(), key=lambda vol: vol.number)
        # pprint(sorted_volumes)

        if args.parallel is None:
            for_each(sorted_volumes, self.build_volume)
        else:
            with Pool(processes=args.parallel) as pool:
                pool.map(self.build_volume, sorted_volumes)

        pickle.dump(volumes, open(cache_name, mode="wb+"))


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
