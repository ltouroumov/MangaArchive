from masc.scraper import *
from masc.util import fetch_image
from ebooklib import epub
from zipfile import ZipFile


def ebook(adapter):
    return EbookAdapter(adapter)


def cbz(adapter):
    return ArchiveAdapter(adapter)


class EbookAdapter(FormatAdapter):
    def file_format(self):
        return '.epub'

    def build_volume(self, filename, volume, metadata):
        book = epub.EpubBook()
        book.set_identifier("%s-v%s" % (metadata.slug, volume.number))
        book_title = "Volume {} - {}".format(volume.number, metadata.title)
        book.set_title(book_title)
        # ebook.set_cover('cover.jpg', fetch_image(self.cover_url))

        spine_chapters = []
        sorted_chapters = sorted(volume.chapters, key=lambda chap: chap.number)
        # pprint(sorted_chapters)
        for chapter in sorted_chapters:
            eb_chapter, images = self.build_chapter(chapter)
            book.add_item(eb_chapter)
            for_each(images, book.add_item)
            spine_chapters.append(eb_chapter)

        book.add_item(epub.EpubNav())

        book.toc = [epub.Section('Chapters')] + spine_chapters
        book.spine = ['nav'] + spine_chapters

        epub.write_epub(filename, book)

    def build_chapter(self, chapter):
        """
        Create the epub objects and downloads images

        :param chapter: Chapter to build from
        :return: EpubHtml, [EpubImage]
        """
        print("{} - {}: {} ({} pages)".format(chapter.volume, chapter.number, chapter.title, len(chapter.pages)))
        chap = epub.EpubHtml()
        chap.title = chapter.title
        chap.file_name = 'chap-%s.html' % chapter.number
        chap_html = list()
        images = list()

        sorted_pages = sorted(chapter.pages, key=lambda p: p.number)
        # pprint(sorted_pages)
        for page in sorted_pages:
            img = epub.EpubImage()
            img.file_name = 'ch{}-p{}.jpg'.format(chapter.number, page.number)
            if page.image_url is None:
                page.image_url = self.adapter.get_image(page)
            img.content = fetch_image(page.image_url)
            chap_html.append('<img src="{}" />'.format(img.file_name))
            images.append(img)

        chap.content = str.join("\n", chap_html)
        return chap, images


class ArchiveAdapter(FormatAdapter):
    def file_format(self):
        return '.cbz'

    def build_volume(self, filename, volume, metadata):
        archive = ZipFile(filename, 'w')

        def build_chapter(chapter):
            print("{} - {}: {} ({} pages)".format(chapter.volume, chapter.number, chapter.title, len(chapter.pages)))

            sorted_pages = sorted(chapter.pages, key=lambda p: p.number)
            # pprint(sorted_pages)
            for page in sorted_pages:
                file_name = 'ch{}-p{}.jpg'.format(chapter.number, page.number)
                if page.image_url is None:
                    page.image_url = self.adapter.get_image(page)
                content = fetch_image(page.image_url)
                archive.writestr(file_name, content)

        sorted_chapters = sorted(volume.chapters, key=lambda chap: chap.number)
        # pprint(sorted_chapters)
        for chapter in sorted_chapters:
            build_chapter(chapter)

        archive.close()
