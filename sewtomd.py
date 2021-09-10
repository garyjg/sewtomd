#! /bin/env python

import sys
import logging
import argparse
from bs4 import BeautifulSoup
import subprocess as sp


logger = logging.getLogger(__name__)


def delete_tags(soup, name, **args):
    for tag in soup.find_all(name, **args):
        logger.debug("deleting: %s", repr(tag))
        tag.decompose()


def main(argv):
    parser = argparse.ArgumentParser("sewtomd.py")
    parser.add_argument("html", help="HTML input file")
    parser.add_argument("markdown",
                        help="Write output to markdown path.")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG)

    with open(args.html) as htmldoc:
        soup = BeautifulSoup(htmldoc, "html.parser")

    headers = soup.find_all(['h' + str(i) for i in range(1, 6)])
    logger.debug("headers: %s", headers)

    # Remove <div class='metadata'>
    delete_tags(soup, 'div', class_='page-metadata')
    # Remove <div id="footer" role="contentinfo">
    delete_tags(soup, 'div', id='footer')
    # Remove <div id="breadcrumb-section">
    delete_tags(soup, 'div', id="breadcrumb-section")

    # Run the html through pandoc to get github-flavored markdown:
    #
    cmd = "pandoc --strip-comments --standalone --from html-native_divs-native_spans --to gfm".split()
    output = open(args.markdown, "w")
    pd = sp.Popen(cmd, shell=False, stdin=sp.PIPE, stdout=output)
    pd.stdin.write(soup.encode("utf8"))
    pd.stdin.close()


if __name__ == "__main__":
    main(sys.argv[1:])

