import importlib
import re
import os
import fnmatch
from zipfile import ZipFile, BadZipfile
from masc.scraper import ScraperEngine


def get_class(dotted_name, default_package):
    *splat, class_name = dotted_name.split('.')

    if len(splat) > 0:
        adapter_pkg = str.join('.', splat)
    else:
        adapter_pkg = default_package

    package_inst = importlib.import_module(adapter_pkg)
    return getattr(package_inst, class_name)


def crawl(args):
    adapter_cls_inst = None
    try:
        adapter_cls_inst = get_class(args.adapter, 'masc.adapter')
    except AttributeError:
        print("Adapter not found")
        exit(-1)

    adapter = adapter_cls_inst(args.url)

    scraper = ScraperEngine(adapter, None)
    scraper.crawl(args)

def build(args):
    format_cls_inst = None
    try:
        format_cls_inst = get_class(args.format, 'masc.format')
    except AttributeError:
        print("Adapter not found")
        exit(-1)

    output = format_cls_inst(None)

    scraper = ScraperEngine(None, output)
    scraper.build(args)

def download(args):
    adapter_cls_inst = None
    format_cls_inst = None
    try:
        adapter_cls_inst = get_class(args.adapter, 'masc.adapter')
        format_cls_inst = get_class(args.format, 'masc.format')
    except AttributeError:
        print("Adapter not found")
        exit(-1)

    adapter = adapter_cls_inst(args.url)
    output = format_cls_inst(adapter)

    scraper = ScraperEngine(adapter, output)
    scraper.run(args)

def fix_path(args):
    def fix_file(name):
        print("Fixing {}".format(name))
        pattern = re.compile(r"^ch(?P<chap>\d+)-p(?P<page>\d+).jpg$")

        tmp_name = "{}.old".format(name)
        os.rename(name, tmp_name)
        old_file = ZipFile(tmp_name, mode='r')
        new_file = ZipFile(name, mode='w')

        for file in old_file.filelist:
            match = pattern.match(file.filename)
            if match is None:
                # print("Object {} does not match pattern".format(file.filename))
                new_file.writestr(file.filename, old_file.read(file.filename))
            else:
                chap, page = match.group('chap', 'page')
                new_name = "ch{:03d}-p{:03d}.jpg".format(int(chap), int(page))
                # print("Renaming {} to {}".format(file.filename, new_name))
                new_file.writestr(new_name, old_file.read(file.filename))

        old_file.close()
        new_file.close()
        os.remove(tmp_name)

    for dirpath, dirnames, filenames in os.walk(args.path):
        for filename in fnmatch.filter(filenames, '*.cbz'):
            path = os.path.join(dirpath, filename)
            try:
                fix_file(path)
            except BadZipfile:
                print("Error with file {}".format(path))
