import importlib
from masc.scraper import ScraperEngine

def masc(args):
    *splat, adapter_cls = args.adapter.split('.')

    if len(splat) > 0:
        adapter_pkg = str.join('.', splat)
    else:
        adapter_pkg = 'masc.adapter'

    adapter_pkg_inst = importlib.import_module(adapter_pkg)
    adapter = None
    try:
        adapter_cls_inst = getattr(adapter_pkg_inst, adapter_cls)
        adapter = adapter_cls_inst(args.url)
    except AttributeError:
        print("Adapter not found")
        exit(-1)

    scraper = ScraperEngine(adapter)
    scraper.run(args)