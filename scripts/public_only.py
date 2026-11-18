#!/usr/bin/env python3
"""Remove admin-only artifacts from GitHub Pages public/ before deployment.

Run after build_pipeline.py and patch_static_links.py. Never treat noindex or
hidden links as authentication: admin pages are removed from the deployment.
"""
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / 'public'
BASE = 'https://piqpaqpoq.github.io/piqpaqpoq/'


def main():
    home = PUBLIC / 'index.html'
    if not home.is_file():
        raise SystemExit('Missing public/index.html: cannot safely deploy')
    content = home.read_text(encoding='utf-8')
    # The pipeline inserts this navigation directly after </header>.
    nav = re.compile(r'<!-- PPQ PIPELINE NAV -->\s*<nav\b[^>]*>.*?</nav>', re.S | re.I)
    content, count = nav.subn('', content)
    # Ensure no homepage links to admin tools remain (even if markup changes).
    admin_links = re.compile(r'<a\b[^>]*\bhref\s*=\s*(["\'])' +
                             re.escape(BASE) + r'(?:discover|insights)/?(?:index\.html)?\1[^>]*>.*?</a>',
                             re.S | re.I)
    content, removed = admin_links.subn('', content)
    home.write_text(content, encoding='utf-8')

    # Approved product pages, when any, inherit the old pipeline's header links.
    fixed_pages = 0
    products = PUBLIC / 'products'
    if products.is_dir():
        for file in products.glob('*.html'):
            page = file.read_text(encoding='utf-8')
            updated = admin_links.sub('', page)
            if updated != page:
                file.write_text(updated, encoding='utf-8')
                fixed_pages += 1

    # Never publish either administrator UI or verification-candidate JSON.
    for d in ('discover', 'insights'):
        target = PUBLIC / d
        if target.exists():
            shutil.rmtree(target) if target.is_dir() else target.unlink()
    for rel in ('data/discovery-candidates.json',
                'data/verified-build-status.json',
                'assets/js/ppq_local_insights.js'):
        p = PUBLIC / rel
        if p.exists():
            p.unlink()

    # Guard against future build changes accidentally reintroducing the tools.
    banned = [PUBLIC / p for p in ('discover', 'insights',
                                   'data/discovery-candidates.json',
                                   'data/verified-build-status.json',
                                   'assets/js/ppq_local_insights.js')]
    if any(p.exists() for p in banned):
        raise SystemExit('Private artifacts still present in public/: deployment aborted')
    if nav.search(content) or admin_links.search(content):
        raise SystemExit('Admin links still present in public index: deployment aborted')
    print('Public-only deployment ready; nav sections:', count,
          '; links removed:', removed, '; product pages cleaned:', fixed_pages)


if __name__ == '__main__':
    main()
