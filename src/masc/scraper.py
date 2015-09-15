from multiprocessing import Pool
from masc.util import *
from masc.descriptor import *
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
        self.descriptor = None
        self.dir = '.'

    def build_volume(self, volume):
        """
        Build an ebook for a volume

        :param volume: Volume object to build from
        :return: None
        """
        try:
            ebook_id = '%s-v%s' % (self.descriptor.metadata.slug, volume.number)
            filename = os.path.join(self.dir, ebook_id + self.format.file_format())
            try:
                os.makedirs(self.dir)
            except FileExistsError:
                pass

            if os.path.exists(filename):
                print(filename, "already exists")
                return

            self.format.build_volume(filename, volume, self.descriptor.metadata)

            print("Written", filename)
        except Exception as ex:
            import traceback
            print("Exception in build_volume")
            traceback.print_exc()

    def crawl(self, args):
        self.descriptor = Descriptor()
        self.descriptor.metadata = self.adapter.get_meta()

        print("Crawling ...")
        chapters = self.adapter.get_chapters()
        for chapter in chapters:
            print("Chapter {}".format(chapter.number))
            pages = self.adapter.get_pages(chapter)
            for page in pages:
                page.image_url = self.adapter.get_image(page)
                chapter.add_page(page)

            if chapter.volume not in self.descriptor.volumes:
                self.descriptor.volumes[chapter.volume] = Volume(chapter.volume)
            self.descriptor.volumes[chapter.volume].add_chapter(chapter)

        if args.out is None:
            cache_name = "{}.xml".format(self.descriptor.metadata.slug)
        else:
            cache_name = "{}.xml".format(args.out)

        self.descriptor.save(cache_name)

    def build(self, args):
        if args.out is not None:
            self.dir = args.out

        if self.descriptor is None:
            self.descriptor = Descriptor.load(args.descriptor)

        print("Building ...")
        sorted_volumes = sorted(self.descriptor.volumes.values(), key=lambda vol: vol.number)

        # filter volumes
        if len(args.volumes) > 0:
            print("Filtering volumes {}".format(args.volumes))
            sorted_volumes = filter(lambda vol: vol.number in args.volumes, sorted_volumes)

        if args.parallel is None:
            for_each(sorted_volumes, self.build_volume)
        else:
            with Pool(processes=args.parallel) as pool:
                pool.map(self.build_volume, sorted_volumes)

    def run(self, args):
        if args.out is not None:
            self.dir = args.out

        cache_name = os.path.join(self.dir, "{}.xml".format(self.adapter.slug))
        if not args.rebuild and os.path.exists(cache_name):
            print("Loading from cache")
            self.descriptor = Descriptor.load(cache_name)
        else:
            self.crawl(args)

        self.build(args)
        self.descriptor.save(cache_name)
