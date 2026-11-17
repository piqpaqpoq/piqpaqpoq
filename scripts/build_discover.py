#!/usr/bin/env python3
"""Build original PIQ PAQ POQ page-compatible news data from existing RSS collection."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
raw = json.loads((ROOT / 'data' / 'rss-news.json').read_text(encoding='utf-8'))
items = []
for item in raw.get('items', []):
    categories = item.get('categories') or []
    topics = item.get('topics') or []
    published = item.get('publishedAt') or item.get('date')
    if not published or not item.get('title') or not item.get('url'):
        continue
    items.append({
        'id': item.get('id') or item['url'],
        'title': item['title'],
        'url': item['url'],
        'date': published,
        'source': item.get('source', '원문 출처 확인'),
        'category': categories[0] if categories else '업종 전체',
        'topic': topics[0] if topics else '신제품·신메뉴',
        'topics': topics,
        'linkType': item.get('linkType', '원문 링크'),
        'launchDate': None,
    })
items.sort(key=lambda x: x['date'], reverse=True)
config_path = ROOT / 'automation' / 'rss-sources.json'
config = json.loads(config_path.read_text(encoding='utf-8')) if config_path.exists() else {'feeds': []}
config_feeds = {f.get('id'): f for f in config.get('feeds', [])}
sources = []
for feed in raw.get('feeds', []):
    config_feed = config_feeds.get(feed.get('id'), {})
    name = config_feed.get('name') or (config_feed.get('category', 'RSS') + ' · ' + config_feed.get('topic', '소식'))
    count = feed.get('items', 0)
    status = ('연결됨 · ' + str(count) + '건') if feed.get('status') == 'ok' else '연결 실패 · 확인 필요'
    sources.append({'name': name, 'status': status})
output = {'items': items, 'sources': sources, 'checkedAt': raw.get('checkedAt')}
output_path = ROOT / 'data' / 'discover.json'
output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_text(json.dumps(output, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
print(f'Converted {len(items)} RSS items and {len(sources)} feed statuses')
