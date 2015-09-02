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

    parser = argparse.ArgumentParser()
    parser.add_argument('url', metavar='url', help='URL of the manga')
    parser.add_argument('adapter', default='MangafoxAdapter', help='Adapter class')
    parser.add_argument('--format', default='ebook', help='Output format (ebook, cbz)')
    parser.add_argument('--out', default=None, help='Output directory (default: current)')
    parser.add_argument('--parallel', default=None, type=int, help='Number of concurrent threads (default: none)')
    parser.add_argument('--chapters', default=[], help="Specify chapters to build")
    parser.add_argument('--rebuild', action='store_true', default=False, help="Rebuild chapter cache")

    args = parser.parse_args()

    from masc.main import masc
    masc(args)
