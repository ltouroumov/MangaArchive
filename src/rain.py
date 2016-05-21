import requests
import re
from bs4 import BeautifulSoup
from masc.data import *
from masc.descriptor import Descriptor
from masc.util import fetch_html

base_url = "http://rain.thecomicseries.com"
current = fetch_html(base_url, cached=True)

chap_rx = re.compile(r"^Ch.? (?P<chap>\d+): (?P<name>.+)$")
title_rx = re.compile(r"^Comic (?P<num>\d+) - (?P<name>.+)$")

chapters = dict()

pages = current.find("select", class_="comicnavlink")
for page_opt in pages.find_all('option'):
    page = fetch_html(base_url + str(page_opt['value']), cached=True)
    chap_tag = page.find(class_='headingsub').find('a')
    if chap_tag is None:
        chap_str = "Ch. 0: Unkown"
    else:
        chap_str = str(chap_tag.string)

    title_str = str(page.find(class_='heading').string)
    image_str = str(page.find(id='comicimage').get('src'))

    match1 = chap_rx.match(chap_str)
    if match1 is None:
        chap_num, chap_name = ['000', 'Unkown']
    else:
        chap_num, chap_name = match1.group('chap', 'name')
        chap_num = "{:0>3s}".format(chap_num)

    match2 = title_rx.match(title_str)
    if match2 is None:
        page_num = "000"
    else:
        page_num = match2.group('num')
        page_num = "{:0>3s}".format(page_num)

    if chap_num not in chapters:
        chapters[chap_num] = Chapter(url=None, title=chap_name, number=chap_num)
    chapter = chapters[chap_num]

    page = Page(url=None, number=page_num)
    page.image_url = image_str
    chapter.add_page(page)

    print("{} - {}: {}".format(chap_num, chap_name, page_num))

descriptor = Descriptor()
descriptor.metadata = Metadata(title="Rain", slug="rain")
descriptor.metadata.cover_url = "..."
volume = Volume(number="0")
volume.chapters = list(sorted(chapters.values(), key=lambda chap: chap.number))
descriptor.add_volume(volume)
descriptor.save("rain.xml")
