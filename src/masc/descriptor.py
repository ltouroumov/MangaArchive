from xml.etree import ElementTree
from masc.data import *


class Descriptor(object):
    def __init__(self):
        self.metadata = None
        self.volumes = dict()

    def add_volume(self, volume):
        self.volumes[volume.number] = volume

    @staticmethod
    def load(path):
        self = Descriptor()
        xml = ElementTree.parse(path)
        root = xml.getroot()

        metadata_tag = root.find('metadata')
        self.metadata = Metadata(title=str(metadata_tag.find('title').text),
                                 slug=str(metadata_tag.get('slug')))
        self.metadata.cover_url = str(metadata_tag.find('cover').text)

        for volume_tag in root.findall('volume'):
            volume = Volume(number=str(volume_tag.get('number')))

            for chapter_tag in volume_tag.findall('chapter'):
                chapter = Chapter(url=str(chapter_tag.get('url')),
                                  title=str(chapter_tag.find('title').text),
                                  number=str(chapter_tag.get('number')))
                chapter.volume = volume.number

                for page_tag in chapter_tag.findall('page'):
                    page = Page(url=None,
                                number=str(page_tag.get('number')))
                    page.image_url = str(page_tag.get('url'))
                    chapter.add_page(page)

                volume.add_chapter(chapter)

            self.add_volume(volume)

        return self

    def save(self, path):
        descriptor = ElementTree.Element('descriptor')

        metadata_tag = ElementTree.SubElement(descriptor, 'metadata')
        metadata_tag.set('slug', self.metadata.slug)
        title_tag = ElementTree.SubElement(metadata_tag, 'title')
        title_tag.text = str(self.metadata.title)
        cover_tag = ElementTree.SubElement(metadata_tag, 'cover')
        cover_tag.set('url', self.metadata.cover_url)

        for vid, volume in self.volumes.items():
            volume_tag = ElementTree.SubElement(descriptor, 'volume')
            volume_tag.set('number', str(vid))
            for chapter in volume.chapters:
                chapter_tag = ElementTree.SubElement(volume_tag, 'chapter')
                chapter_tag.set('number', str(chapter.number))
                chapter_tag.set('url', str(chapter.url))

                title_tag = ElementTree.SubElement(chapter_tag, 'title')
                title_tag.text = str(chapter.title)

                for page in chapter.pages:
                    page_tag = ElementTree.SubElement(chapter_tag, 'page')
                    page_tag.set('number', str(page.number))
                    page_tag.set('url', str(page.image_url))

        tree = ElementTree.ElementTree(descriptor)
        tree.write(path)
