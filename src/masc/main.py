import importlib
from masc.scraper import ScraperEngine


def get_class(dotted_name, default_package):
    *splat, class_name = dotted_name.split('.')

    if len(splat) > 0:
        adapter_pkg = str.join('.', splat)
    else:
        adapter_pkg = default_package

    package_inst = importlib.import_module(adapter_pkg)
    return getattr(package_inst, class_name)


def masc(args):

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
