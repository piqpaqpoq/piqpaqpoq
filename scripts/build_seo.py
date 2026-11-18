#!/usr/bin/env python3
# Build crawlable static editorial pages at deploy time; do not change source index.html
from pathlib import Path
from html import escape as esc
from datetime import date
import json, re

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'public'
BASE='https://piqpaqpoq.github.io/piqpaqpoq/'
D=json.loads((ROOT/'data/seo-products-2026w3.json').read_text(encoding='utf-8'))
PRODS=D['products']
WEEK='new-products/2026/11/week-3.html'
STYLE='''
:root{--ink:#193957;--muted:#657b90;--blue:#1467b8;--line:#d9e6f2;--bg:#f5f9fd;--light:#eaf3fd}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;font:16px/1.72 system-ui,-apple-system,'Noto Sans KR',sans-serif;color:var(--ink);background:var(--bg)}
a{color:var(--blue);text-underline-offset:3px}a:focus-visible{outline:3px solid #b04a9f}header{background:#fff;border-bottom:1px solid var(--line);padding:17px max(20px,calc((100% - 1080px)/2))}header a{text-decoration:none;font-weight:900;color:var(--ink);font-size:21px}
.wrap{max-width:1050px;margin:auto;padding:32px 20px 75px}.crumb{font-size:13px;color:var(--muted);margin-bottom:20px}.crumb a{color:inherit}
h1{font-size:clamp(29px,5vw,43px);line-height:1.27;letter-spacing:-.045em;margin:16px 0}h2{font-size:23px;margin:34px 0 13px;letter-spacing:-.03em}.lead{font-size:18px;max-width:740px;color:#3d5873}.meta{color:var(--muted);font-size:13px}.pill{display:inline-block;background:#e3eefb;color:#175a98;border-radius:100px;padding:5px 12px;font-size:12px;font-weight:700}.panel{background:#fff;border:1px solid var(--line);border-radius:16px;padding:24px;margin:18px 0}.facts{width:100%;border-collapse:collapse}.facts th,.facts td{text-align:left;padding:14px 10px;border-bottom:1px solid var(--line);vertical-align:top}.facts th{width:34%;color:#526c83;font-weight:600}.cards{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}.card{background:#fff;border:1px solid var(--line);border-radius:16px;padding:24px}.card h2{margin:8px 0}.card p{margin:9px 0}.tag{font-size:12px;color:#366f9f}.button{display:inline-block;background:var(--blue);color:#fff;text-decoration:none;padding:12px 18px;border-radius:10px;font-weight:700;margin-top:7px}.button.secondary{background:#eaf3fd;color:#1d5790}.note{background:#fff7e7;border-left:3px solid #e0a23c;padding:13px 17px;font-size:14px}.source{overflow-wrap:anywhere;font-size:14px}.source li{margin-bottom:9px}.check li{padding:3px 0}.foot{border-top:1px solid var(--line);padding-top:20px;margin-top:40px;color:var(--muted);font-size:13px}.ribbon{border-radius:12px;background:#e9f3ff;padding:16px;margin-top:20px}small{font-size:12px}@media(max-width:650px){.cards{grid-template-columns:1fr}.panel{padding:18px}.wrap{padding:24px 16px 60px}.facts th{width:38%}}
'''
def head(title,desc,path,structured):
    url=BASE+path
    return f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} | PIQ PAQ POQ</title><meta name="description" content="{esc(desc,quote=True)}">
<link rel="canonical" href="{esc(url,quote=True)}"><meta name="robots" content="index,follow,max-snippet:-1">
<meta property="og:type" content="article"><meta property="og:title" content="{esc(title,quote=True)}"><meta property="og:description" content="{esc(desc,quote=True)}"><meta property="og:url" content="{esc(url,quote=True)}">
<script type="application/ld+json">{json.dumps(structured,ensure_ascii=False).replace('<','\\u003c')}</script>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-4Q7P01BEHT"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-4Q7P01BEHT');</script>
<script defer src="{BASE}assets/js/ppq_analytics_events.js"></script>
<style>{STYLE}</style></head><body><header><a href="{BASE}">PIQ PAQ POQ <small>신상 &amp; 이슈</small></a></header><main class="wrap">'''
def trail():return f'<nav class="crumb" aria-label="현재 위치"><a href="{BASE}">홈</a> / <a href="{BASE+WEEK}">11월 셋째 주 신상</a></nav>'
def wrap(text): return text+'</main></body></html>'
def product_page(p):
 path='products/'+p['slug']+'.html';title=f"{p['brand']} {p['name']} 가격·출시 정보";desc=p['summary']
 schema={'@context':'https://schema.org','@type':'Article','headline':title,'description':desc,'datePublished':D['updated'],'dateModified':D['updated'],'inLanguage':'ko-KR','mainEntityOfPage':{'@type':'WebPage','@id':BASE+path},'author':{'@type':'Organization','name':'PIQ PAQ POQ'},'publisher':{'@type':'Organization','name':'PIQ PAQ POQ'},'about':{'@type':'Thing','name':p['name']}}
 facts=''.join(f'<tr><th>{esc(k)}</th><td>{esc(v)}</td></tr>' for k,v in p['facts'])
 check=''.join(f'<li>{esc(x)}</li>' for x in p['check'])
 ref=''.join(f'<li><a href="{esc(p[u],quote=True)}" target="_blank" rel="noopener noreferrer">{esc(p[n])}</a></li>' for u,n in [('source','source_name'),('secondary','secondary_name')])
 h=head(title,desc,path,schema)+trail()+f'''<span class="pill">{esc(p['brand'])} · {esc(p['category'])}</span><h1>{esc(p['question'])}</h1><p class="lead">{esc(p['summary'])}</p><p class="meta">발표일 {esc(p['announcement'])} · 정보 확인일 {D['updated']} · 판매/할인 조건은 방문 전 재확인</p>
<section class="panel" aria-label="가격과 출시 정보"><h2>가격·출시 핵심 정보</h2><table class="facts"><tbody>{facts}</tbody></table><p class="note">{esc(p['price_note'])}</p></section>
<section><h2>구매 전 알아둘 점</h2><p>{esc(p['why'])}</p><ul class="check">{check}</ul></section>
<section class="panel"><h2>이 정보의 출처</h2><p>브랜드 발표, 이를 인용한 보도와 실제 매장 판매 조건은 서로 다를 수 있습니다. 직접 구매·시식 후기로 표현하지 않습니다.</p><ol class="source">{ref}</ol></section>
<section><h2>함께 확인할 정보</h2><p>같은 주에 발표된 다른 신상품과 가격을 비교할 수 있습니다.</p><a class="button secondary" href="{BASE+WEEK}">2026년 11월 셋째 주 신상품 보기</a></section>
<footer class="foot">PIQ PAQ POQ 편집 정보 · 정보 확인 기준일 {D['updated']} · 가격·재고·행사는 점포 사정에 따라 변경될 수 있습니다.</footer>'''
 return path,wrap(h)
def weekly_page():
 title='2026년 11월 셋째 주 편의점 신상｜CU 디카페인·세븐일레븐 꼬막비빔밥';desc='2026년 11월 16~22일 편의점 신상 중 19일까지 확인된 2종. CU get커피 디카페인 가격, 세븐일레븐 꼬막비빔밥 출시일과 BC카드 할인 조건을 원문과 함께 확인하세요.'
 schema={'@context':'https://schema.org','@type':'CollectionPage','name':title,'description':desc,'inLanguage':'ko-KR','url':BASE+WEEK,'dateModified':D['updated'],'hasPart':[{'@type':'WebPage','name':p['name'],'url':BASE+'products/'+p['slug']+'.html'} for p in PRODS]}
 cards=''.join(f'''<article class="card"><span class="pill">{esc(p['brand'])}</span><p class="tag">{esc(p['tag'])}</p><h2><a href="{BASE}products/{esc(p['slug'])}.html">{esc(p['name'])}</a></h2><p><strong>{esc(p['price_main'])}</strong></p><p>{esc(p['summary'])}</p><p class="meta">발표 {esc(p['announcement'])} · 출시 {esc(p['release'])}</p><a class="button" href="{BASE}products/{esc(p['slug'])}.html">가격·출시 조건 확인</a></article>''' for p in PRODS)
 h=head(title,desc,WEEK,schema)+trail()+f'''<span class="pill">2026.11.16–11.22 · 확인일 {D['updated']}</span><h1>이번 주 편의점 신상,<br>가격보다 먼저 볼 조건</h1><p class="lead">11월 셋째 주 신상품 가운데 <strong>11월 19일까지 출처와 가격을 확인할 수 있는 2종</strong>을 골랐습니다. 발표·출시·할인 시작일을 혼동하지 않도록 구분했습니다.</p><div class="ribbon">이번 주 확인 상품 {len(PRODS)}종 · 가격 표기는 확인한 출처 기준 · 다른 브랜드는 미확인 상품을 억지로 채우지 않았습니다.</div><section><h2>확인된 신상품 {len(PRODS)}종</h2><div class="cards">{cards}</div></section><section class="panel"><h2>어떤 사람에게 유용할까?</h2><p><strong>퇴근 후 커피를 찾는 사람:</strong> CU 디카페인 판매 점포를 먼저 확인하세요. <strong>점심값을 비교하는 사람:</strong> 세븐일레븐 비빔밥은 기본가와 BC카드 할인 적용가를 구분해야 합니다.</p><p>신상품 가격은 단순 숫자보다 <strong>사용 조건</strong>과 함께 읽어야 실제 지출 판단에 도움이 됩니다.</p></section><section class="panel"><h2>검증 방법</h2><p>공식 기업 발표 또는 해당 기업 발표를 인용한 언론 보도에서 제품명·가격·출시 시점을 교차 확인했습니다. 보도 이후 점포별 운영 상황은 다를 수 있으며 미확인 사항은 확정적으로 적지 않았습니다.</p><p>이 페이지는 2026년 11월 19일 현재까지 확인된 정보를 담고 있습니다. 이후 20~22일 출시 상품은 포함되지 않았습니다.</p></section><footer class="foot">PIQ PAQ POQ · 편의점 신상품 정보는 확인 시점에 따라 변경될 수 있습니다.</footer>'''
 return WEEK,wrap(h)
def write(path,text):
 dest=OUT/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(text,encoding='utf-8')
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 paths=[]
 for p in PRODS:
  path,content=product_page(p);write(path,content);paths.append(path)
 path,content=weekly_page();write(path,content);paths.insert(0,path)
 home=OUT/'index.html'
 if not home.exists():raise RuntimeError('run after workflow copies index.html')
 s=home.read_text(encoding='utf-8')
 # Do not replace source index.html. Insert a self-contained, visible and crawlable section into deployed output.
 marker='<!-- PPQ 2026 NOV WEEK3 SEO SECTION -->'
 if marker not in s:
  section=f'''{marker}<section aria-label="2026년 11월 셋째 주 편의점 신상품" style="max-width:1300px;margin:22px auto;padding:18px 24px;border:1px solid #c8ddef;border-radius:16px;background:#edf5ff;font:15px/1.6 system-ui,sans-serif;color:#163457"><h2 style="font-size:20px;margin:0 0 8px">11월 셋째 주 신상 · 가격부터 확인</h2><p style="margin:0 0 10px">CU 디카페인 커피 1,800원부터 · 세븐일레븐 꼬막비빔밥 5,200원 (BC카드 조건 충족 시 3,900원)</p><a href="{BASE+WEEK}" style="font-weight:700;color:#0056a8">11월 셋째 주 편의점 신상, 조건까지 보기 →</a><div style="margin-top:8px;font-size:13px"><a href="{BASE}products/cu-getcoffee-decaf-2026.html">CU get커피 디카페인 가격</a> · <a href="{BASE}products/seven-eleven-sikyung-cockle-bibimbap-2026.html">세븐일레븐 꼬막비빔밥 할인 조건</a></div></section>'''
  s=s.replace('</header>','</header>'+section,1)
 if '<meta name="description"' not in s:
  s=s.replace('<head>','<head><meta name="description" content="CU·GS25·세븐일레븐·이마트24 편의점 신상품과 공식 행사, 발표일·가격·할인 조건을 출처와 함께 확인하는 PIQ PAQ POQ.">',1)
 if '<link rel="canonical"' not in s:
  s=s.replace('<head>','<head><link rel="canonical" href="'+BASE+'">',1)
 home.write_text(s,encoding='utf-8')
 urls=[BASE]+[BASE+p for p in paths]
 xml='<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+''.join('  <url><loc>'+esc(u)+'</loc></url>\n' for u in urls)+'</urlset>\n'
 write('sitemap.xml',xml)
 print('seo pages:',*[str(x) for x in paths],sep='\n - ')
 print('sitemap URLs:',len(urls))
if __name__=='__main__':main()
