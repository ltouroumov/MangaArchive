import argparse
import sys

if __name__ == "__main__":
    try:
        import ebooklib
        import bs4
        import requests
    except ImportError:
        print("Requires packages ebooklib, requests and beautifulsoup4")
        exit(-1)

    if sys.hexversion < 0x03030000:
        print("Your python version is not supported (python 3.3+ required)")
        exit(-1)

    main_parser = argparse.ArgumentParser()
    subparsers = main_parser.add_subparsers(dest='mode')

    crawl_parser = argparse.ArgumentParser(add_help=False)
    crawl_parser.add_argument('--adapter', default='auto', help='Adapter class (default: auto)')
    crawl_parser_impl = subparsers.add_parser('crawl', parents=[crawl_parser], help='Builds an XML descriptor from an URL')
    crawl_parser_impl.add_argument('url', help='URL of the manga')
    crawl_parser_impl.add_argument('--out', default=None, help='Output file')

    build_parser = argparse.ArgumentParser(add_help=False)
    build_parser.add_argument('--format', default='ebook', help='Output format (ebook, cbz)')
    build_parser.add_argument('--out', default=None, help='Output directory (default: current)')
    build_parser.add_argument('--parallel', default=None, type=int, help='Number of concurrent threads (default: none)')
    build_parser.add_argument('--volumes', default=[], nargs='*', help="Specify chapters to build")
    build_parser_impl = subparsers.add_parser('build', parents=[build_parser], help='Downloads files from an XML descriptor')
    build_parser_impl.add_argument('descriptor', help='Name of the descriptor file')

    dl_parser = subparsers.add_parser('download', parents=[crawl_parser, build_parser], aliases=['dl'], help='Combines "crawl"+"build"')
    dl_parser.add_argument('url', help='URL of the manga')
    dl_parser.add_argument('--rebuild', action='store_true', default=False, help="Rebuild chapter cache")

    fix_parser = subparsers.add_parser('fix', help='Fix CBZ files in a path')
    fix_parser.add_argument('path', metavar='path', default='.', help='path to search CBZ files')

    args = main_parser.parse_args()

    from masc.main import download, fix_path, crawl, build

    if args.mode in ('download', 'dl'):
        download(args)
    elif args.mode == 'crawl':
        crawl(args)
    elif args.mode == 'build':
        build(args)
    elif args.mode == 'fix':
        fix_path(args)
    else:
        print("Unkown mode {}".format(args.mode))
