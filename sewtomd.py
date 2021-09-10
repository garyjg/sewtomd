#! /bin/env python

"""
sewtomd.py filters HTML files exported from Confluence wiki pages and converts
them to markdown using pandoc.  Removing special div elements from the exported
html creates a cleaner markdown file from pandoc.
"""


import shutil
import sys
import logging
import argparse
from bs4 import BeautifulSoup
import subprocess as sp
from pathlib import Path


logger = logging.getLogger(__name__)


class ConfluenceConverter:

    html_path: Path
    resource_path: Path
    markdown_path: Path
    toc_depth: int

    def __init__(self) -> None:
        self.resource_path = None
        self.toc_depth = 2
        self.html_path = None
        self.markdown_path = None
        self.soup = None

    def set_html_path(self, path):
        "Setup the html input path and a resource path relative to that."
        self.html_path = Path(path)
        self.resource_path = self.html_path.parent

    def load_html(self):
        "Read the html input at path and parse into a soup tree."
        with open(self.html_path) as htmldoc:
            self.soup = BeautifulSoup(htmldoc, "html.parser")

    def set_markdown_path(self, mdpath):
        self.markdown_path = Path(mdpath)

    def delete_tags(self, name, **args):
        for tag in self.soup.find_all(name, **args):
            logger.debug("deleting: %s, id=%s, class=%s", tag.name,
                         tag.get('id'), tag.get('class'))
            tag.decompose()

    def rename_image(self, src, alt):
        """
        Given the alt and src attributes of an img, generate a new more
        descriptive file name.
        """
        # make sure src is a path
        src = Path(src)
        # use alt as the name if set, with the right extension
        srcfile = Path(src.name)
        if alt:
            dst = str(alt)
            dst = dst.replace(" ", "_")
            dst = Path(dst.replace("/", ""))
            if dst.suffix != srcfile.suffix:
                dst = Path(str(dst) + srcfile.suffix)
        else:
            dst = srcfile
        return dst

    def resolve_image(self, src) -> Path or None:
        "Return a Path where src exists locally, else None."
        srcp = None
        if src is not None:
            srcp = Path(src)
            if not srcp.exists():
                srcp = self.resource_path.joinpath(srcp)
            if not srcp.exists():
                srcp = None
            logger.info("src %s: %s", src,
                        f"found at path: {srcp}" if srcp else "not found")
        return srcp

    def modify_html(self):
        "Modify the html document to make it suitable for pandoc."
        headers = self.soup.find_all(['h' + str(i) for i in range(1, 6)])
        for h in headers:
            logger.debug("header: %s, content=%s", h.name, h.string)

        self.delete_tags('div', class_='page-metadata')
        self.delete_tags('div', id='footer')
        self.delete_tags('div', id="breadcrumb-section")
        self.delete_tags('div', class_="pageSection group")

        # Find all img tags and print the alt attribute.
        for img in self.soup.find_all('img'):
            alt = img.get('alt')
            # assuming src attribute will never be missing
            src = img.get('src')
            logger.info("Found img: alt='%s', src='%s', data-image-src='%s'",
                        alt, src, img.get('data-image-src'))
            # See if this path exists locally, perhaps relative to the
            # html path.
            src = self.resolve_image(src)
            if src:
                dst = self.rename_image(src, alt)
                logger.info("copying %s to %s...", src, dst)
                shutil.copy(src, dst)
                # And update the img location.
                img['src'] = str(dst)
                logger.debug("updated img tag: %s", repr(img))

    def write_markdown(self):
        "Run the html through pandoc to get github-flavored markdown"
        # The no-highlight omits the syntaxhighlighter-pre language selector
        # from confluence, since that looks useless and not portable.  We don't
        # use --extract-media because that downloads images whose src is a url.
        # Instead only locally existing files (ie attachments) are copied and
        # renamed when the html is filtered.
        cmd = str(f"pandoc --strip-comments --standalone "
                  f"--no-highlight "
                  f"--toc --toc-depth={self.toc_depth} "
                  f"--from html-native_divs-native_spans --to gfm")
        logger.info("Running pandoc: %s", cmd)
        args = cmd.split()
        output = self.markdown_path.open("w")
        pd = sp.Popen(args, shell=False, stdin=sp.PIPE, stdout=output)
        pd.stdin.write(self.soup.encode("utf8"))
        pd.stdin.close()


def main(argv):
    parser = argparse.ArgumentParser("sewtomd.py",
                                     description=__doc__)
    parser.add_argument("html", help="HTML input file")
    parser.add_argument("markdown",
                        help="Write output to markdown path.")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO)

    cc = ConfluenceConverter()
    cc.set_html_path(args.html)
    cc.set_markdown_path(args.markdown)
    cc.load_html()
    cc.modify_html()
    cc.write_markdown()


if __name__ == "__main__":
    main(sys.argv[1:])
