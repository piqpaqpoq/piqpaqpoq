#!/usr/bin/env python3
"""Best-effort publisher article thumbnails for a bounded number of recent RSS items.

Google News RSS doesn't include article images. Never invent an image, never use a
publisher's generic homepage photo, and do not make 329 page requests per deploy.
The optional googlenewsdecoder dependency can resolve opaque Google News URLs.
"""
import concurrent.futures
import html
import ipaddress
import json
import os
import re
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
MAX_ITEMS=int(os.environ.get('PPQ_THUMBNAIL_LIMIT','48'))
TIMEOUT=6
MAX_HTML=450_000

# Exact, independently identified publisher articles (only these matches).
VERIFIED_ORIGINALS=[
  ('뉴스1','컴포즈커피','옐로우 홀리데이','https://www.news1.kr/industry/distribution/6356182'),
  ('뉴스1','파리바게뜨','베리밤 딥초코','https://www.news1.kr/industry/distribution/6356101'),
  ('싱글리스트','파리바게뜨','베리밤 딥초코','https://www.slist.kr/news/articleView.html?idxno=782362'),
]

def public_https(value):
    try:
        u=urllib.parse.urlsplit(value)
        if u.scheme!='https' or not u.hostname or u.username or u.password:return False
        host=u.hostname.lower()
        if host in ('localhost','127.0.0.1') or host.endswith(('.local','.internal')):return False
        try:
            ip=ipaddress.ip_address(host)
            return ip.is_global
        except ValueError:return '.' in host
    except (ValueError,TypeError):return False

class Metadata(HTMLParser):
    def __init__(self):super().__init__();self.images=[]
    def handle_starttag(self,tag,attrs):
        if tag!='meta':return
        a=dict((k.lower(),v) for k,v in attrs if k and v)
        prop=(a.get('property') or a.get('name') or '').lower()
        if prop in ('og:image:secure_url','og:image','twitter:image','twitter:image:src'):
            self.images.append((prop,html.unescape(a.get('content',''))))

def image_from_html(page,url):
    p=Metadata();p.feed(page)
    for prop in ('og:image:secure_url','og:image','twitter:image','twitter:image:src'):
        for key,value in p.images:
            if key!=prop:continue
            absolute=urllib.parse.urljoin(url,value)
            if public_https(absolute) and not any(x in absolute.lower() for x in ('favicon','default_logo','logo.png','noimage','placeholder','blank.gif')):
                return absolute
    return ''

def get_page(url):
    if not public_https(url):return '', ''
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; PIQPAQPOQArticlePreview/1.0)','Accept':'text/html,application/xhtml+xml'})
    with urllib.request.urlopen(req,timeout=TIMEOUT) as resp:
        final=resp.geturl()
        if not public_https(final):return '', ''
        if 'text/html' not in resp.headers.get('Content-Type','text/html').lower():return '', ''
        return resp.read(MAX_HTML).decode('utf-8','replace'),final

def original_url(item):
    url=item.get('originalUrl','')
    if public_https(url) and 'news.google.com' not in urllib.parse.urlsplit(url).hostname:return url
    title=item.get('title','');source=item.get('source','')
    for publisher,first,second,verified in VERIFIED_ORIGINALS:
        if source==publisher and first in title and second in title:return verified
    url=item.get('url','')
    if not public_https(url):return ''
    if urllib.parse.urlsplit(url).hostname!='news.google.com':return url
    try:
        from googlenewsdecoder import new_decoderv1
        result=new_decoderv1(url,interval=0)
        decoded=result.get('decoded_url','') if isinstance(result,dict) else ''
        if public_https(decoded) and urllib.parse.urlsplit(decoded).hostname!='news.google.com':return decoded
    except Exception:return ''
    return ''

def enrich(item):
    if public_https(item.get('image','')):return item
    original=original_url(item)
    if not original:return item
    try:
        page,final=get_page(original)
        if not page:return item
        image=image_from_html(page,final)
        if image:
            return dict(item,image=image,originalUrl=final)
    except (OSError,TimeoutError,ValueError,UnicodeError):pass
    return item

def main():
    p=ROOT/'data/discover.json'
    d=json.loads(p.read_text(encoding='utf-8'))
    items=d.get('items',[])
    if not isinstance(items,list):raise ValueError('invalid discover.json items')
    count=min(MAX_ITEMS,len(items))
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        enriched=list(pool.map(enrich,items[:count]))
    d['items']=enriched+items[count:]
    p.write_text(json.dumps(d,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
    print('Thumbnail enrichment:',sum(bool(x.get('image')) for x in enriched),'/',count,'recent items with verified image URLs')

if __name__=='__main__':
    main()
