#!/usr/bin/env python3
"""Keep newly generated static editorial/tool links out of the homepage SPA router.

The SPA's linkFix() adds onclick handlers to same-origin links unless
`data-native` is present. That makes /discover and /insights render a bogus
SPA route ('undefined') instead of loading the real HTML pages.
This script modifies only the deployed public/index.html, not the source.
"""
from html.parser import HTMLParser
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / 'public' / 'index.html'
PREFIX = 'https://piqpaqpoq.github.io/piqpaqpoq/'
STATIC_PATHS = (
    'discover/',
    'insights/',
    'new-products/2026/',
)
STATIC_PRODUCT_RE = re.compile(r'^products/[a-z0-9-]+\.html(?:[?#].*)?$', re.I)


class NativeLinks(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.static_count = 0
        self.existing_native = 0
        self.rewrites = []

    def handle_starttag(self, tag, attrs):
        if tag != 'a':
            return
        attrs = dict(attrs)
        href = attrs.get('href') or ''
        relative = href[len(PREFIX):] if href.startswith(PREFIX) else ''
        is_static = bool(relative) and (
            any(relative.startswith(x) for x in STATIC_PATHS)
            or bool(STATIC_PRODUCT_RE.match(relative))
        )
        if is_static:
            self.static_count += 1
            if attrs.get('data-native') is not None:
                self.existing_native += 1


def main():
    if not FILE.is_file():
        raise SystemExit('Expected generated public/index.html before link patch')
    source = FILE.read_text(encoding='utf-8')
    doc = NativeLinks()
    doc.feed(source)
    # Transform only static routes emitted by build_seo.py/build_pipeline.py.
    # Do not touch SPA internal navigation, current product cards, or external links.
    pattern = re.compile(r'<a\b[^>]*>', re.I)
    replaced = 0

    def patch(m):
        nonlocal replaced
        tag = m.group()
        hrefmatch = re.search(r'\bhref\s*=\s*(["\'])(.*?)\1', tag, re.I | re.S)
        if not hrefmatch:
            return tag
        href = hrefmatch.group(2)
        relative = href[len(PREFIX):] if href.startswith(PREFIX) else ''
        relevant = bool(relative) and (
            any(relative.startswith(x) for x in STATIC_PATHS)
            or bool(STATIC_PRODUCT_RE.match(relative))
        )
        if not relevant or re.search(r'\bdata-native\b', tag, re.I):
            return tag
        replaced += 1
        return tag[:-1] + ' data-native="true">'

    result = pattern.sub(patch, source)
    if not doc.static_count:
        raise SystemExit('Static links missing from homepage; check prior builders')
    if replaced + doc.existing_native < doc.static_count:
        raise SystemExit('Not all static anchors were marked native')
    FILE.write_text(result, encoding='utf-8')
    print(f'Static links on homepage: {doc.static_count}, newly fixed: {replaced}')


if __name__ == '__main__':
    main()
