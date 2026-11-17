#!/usr/bin/env python3
"""Collect recent RSS/Atom headlines; standard-library only, no article body/images."""
import argparse
import datetime as dt
import email.utils
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'automation/rss-sources.json'
OUTPUT = ROOT / 'data/rss-news.json'
ATOM = '{http://www.w3.org/2005/Atom}'


def parse_date(value):
    if not value:
        return None
    try:
        d = email.utils.parsedate_to_datetime(value)
    except (TypeError, ValueError, IndexError):
        try:
            d = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=dt.timezone.utc)
    return d.astimezone(dt.timezone.utc)


def text_of(node, name):
    element = node.find(name)
    return ''.join(element.itertext()).strip() if element is not None else ''


def extract_entries(data, feed, now, days):
    root = ET.fromstring(data)
    entries = root.findall('.//item')
    is_atom = False
    if not entries:
        entries = root.findall(f'.//{ATOM}entry')
        is_atom = True
    if not entries:
        raise ValueError('No RSS items or Atom entries')
    out = []
    lower = now - dt.timedelta(days=days)
    for entry in entries:
        if is_atom:
            title = text_of(entry, f'{ATOM}title')
            published = text_of(entry, f'{ATOM}published') or text_of(entry, f'{ATOM}updated')
            links = entry.findall(f'{ATOM}link')
            link = next((x.attrib.get('href', '') for x in links if x.attrib.get('rel', 'alternate') == 'alternate'), '')
        else:
            title = text_of(entry, 'title')
            published = text_of(entry, 'pubDate') or text_of(entry, '{http://purl.org/dc/elements/1.1/}date')
            link = text_of(entry, 'link')
        title = re.sub(r'\s+', ' ', title).strip()
        date = parse_date(published)
        parsed = urllib.parse.urlparse(link)
        if not title or not date or not lower <= date <= now + dt.timedelta(hours=6):
            continue
        if parsed.scheme not in ('http', 'https') or not parsed.netloc:
            continue
        digest = hashlib.sha256(link.encode('utf-8')).hexdigest()[:20]
        out.append({'id': digest, 'title': title[:300], 'url': link, 'source': feed['name'], 'publishedAt': date.isoformat(), 'category': feed['category']})
    return out


def fetch_feed(feed, now, days):
    request = urllib.request.Request(feed['url'], headers={'User-Agent': 'Mozilla/5.0 (compatible; PIQPAQPOQ-NewsCollector/1.0; +https://github.com/piqpaqpoq/piqpaqpoq)', 'Accept': 'application/rss+xml, application/atom+xml, application/xml, text/xml, */*'})
    with urllib.request.urlopen(request, timeout=14) as response:
        data = response.read(3_000_001)
        if len(data) > 3_000_000:
            raise ValueError('RSS response too large')
    return extract_entries(data, feed, now, days)


def unique_recent(items, now, days, limit):
    found = {}
    for raw in items:
        if not isinstance(raw, dict):
            continue
        d = parse_date(raw.get('publishedAt'))
        if not d or not now - dt.timedelta(days=days) <= d <= now + dt.timedelta(hours=6):
            continue
        url = raw.get('url', '')
        if not isinstance(url, str) or urllib.parse.urlparse(url).scheme not in ('http', 'https'):
            continue
        key = url.split('#', 1)[0].strip()
        if not key or key in found:
            continue
        found[key] = raw
    return sorted(found.values(), key=lambda x: x['publishedAt'], reverse=True)[:limit]


def load_previous():
    try:
        return json.loads(OUTPUT.read_text(encoding='utf-8'))
    except (FileNotFoundError, json.JSONDecodeError, UnicodeError):
        return {'items': [], 'feeds': []}


def write_atomic(payload):
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=OUTPUT.parent, prefix='.rss-', suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
            f.write('\n')
        os.replace(name, OUTPUT)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true', help='Validate configuration without network requests')
    args = parser.parse_args()
    config = json.loads(CONFIG.read_text(encoding='utf-8'))
    feeds = config['feeds']
    ids = [x['id'] for x in feeds]
    assert len(ids) == len(set(ids)), 'Duplicate feed ids'
    assert all(x['url'].startswith('https://') for x in feeds), 'Feeds must use HTTPS'
    assert all(x['category'] in ('food', 'beauty', 'life') for x in feeds), 'Unknown category'
    if args.check:
        print(f'OK: {len(feeds)} configured feeds, no network access')
        return
    now = dt.datetime.now(dt.timezone.utc)
    previous = load_previous()
    fresh, statuses = [], []
    ok = 0
    for feed in feeds:
        try:
            results = fetch_feed(feed, now, config['days'])
            fresh.extend(results)
            statuses.append({'id': feed['id'], 'status': 'ok', 'items': len(results)})
            ok += 1
            print(f"OK {feed['id']}: {len(results)} recent headlines")
        except (urllib.error.URLError, TimeoutError, ValueError, ET.ParseError, OSError) as exc:
            statuses.append({'id': feed['id'], 'status': 'error', 'error': str(exc)[:160]})
            print(f"FAIL {feed['id']}: {exc}")
    if ok == 0:
        raise SystemExit('All feeds failed; existing data was preserved')
    # Keep prior results within the same freshness window if a source is temporarily unavailable.
    items = unique_recent(fresh + previous.get('items', []), now, config['days'], config['max_items'])
    payload = {'checkedAt': now.isoformat(), 'days': config['days'], 'items': items, 'feeds': statuses}
    write_atomic(payload)
    print(f'Saved {len(items)} headlines from {ok}/{len(feeds)} responding feeds')


if __name__ == '__main__':
    main()
