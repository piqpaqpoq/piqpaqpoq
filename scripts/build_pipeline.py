#!/usr/bin/env python3
"""RSS discovery -> verification queue -> approved static product pages -> local analytics workspace.

Safety rule: RSS article titles are NEVER published as verified product facts.
GitHub Pages has no private datastore: analytics CSV is imported in-browser and not uploaded.
"""
from __future__ import annotations
import json, html, re
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'public'
BASE='https://piqpaqpoq.github.io/piqpaqpoq/'
TODAY=datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()

CSS='''
:root{--bg:#f5f9fd;--surface:#fff;--ink:#163457;--muted:#61768a;--line:#dce8f6;--brand:#0056a8;--tint:#eaf3ff;--warn:#fff5db}
*{box-sizing:border-box}body{margin:0;color:var(--ink);background:var(--bg);font:16px/1.6 system-ui,-apple-system,'Noto Sans KR',sans-serif}
a{color:var(--brand)}a:focus-visible,button:focus-visible,input:focus-visible,select:focus-visible{outline:3px solid #6e9dd3;outline-offset:2px}
.wrap{max-width:1080px;margin:0 auto;padding:24px 18px 85px}.head{background:#fff;border-bottom:1px solid var(--line);padding:18px max(18px,calc((100% - 1080px)/2))}
.head a{text-decoration:none;font-size:21px;font-weight:850}.nav{display:flex;flex-wrap:wrap;gap:14px;margin-top:7px;font-size:14px}
h1{line-height:1.25;letter-spacing:-.04em;font-size:clamp(27px,4vw,38px)}h2{font-size:22px;line-height:1.4;margin:0 0 15px}.lead{color:var(--muted);font-size:16px;max-width:820px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(245px,1fr));gap:14px}.card,.panel{background:white;border:1px solid var(--line);border-radius:15px;padding:22px}.panel{margin-top:20px}
.pill{display:inline-block;border-radius:30px;background:var(--tint);color:var(--brand);font-size:12px;font-weight:800;padding:5px 10px}
.warn{background:var(--warn);border:1px solid #e9d29b;padding:13px;border-radius:10px;font-size:14px}.muted{color:var(--muted);font-size:14px}
input,select,button{padding:10px 12px;border:1px solid var(--line);border-radius:9px;font-size:15px;max-width:100%}button{background:var(--brand);color:white;cursor:pointer;border:none}.filters{display:flex;flex-wrap:wrap;gap:10px;margin:20px 0}
table{border-collapse:collapse;width:100%;font-size:14px;min-width:540px}td,th{padding:11px;text-align:left;border-bottom:1px solid var(--line)}th{background:#f6f9fd}.scroll{overflow:auto}.stat{font-size:26px;font-weight:850;margin:2px 0}.small{font-size:12px;color:var(--muted)}
label{display:block;font-weight:650;margin-bottom:6px}li{margin-bottom:9px}.footer{border-top:1px solid var(--line);margin-top:40px;padding-top:24px;font-size:13px;color:var(--muted)}
@media(max-width:600px){.card,.panel{padding:17px}.filters>*{flex:1;min-width:145px}}
'''

def h(x):return html.escape(str(x),quote=True)
def write(path,text):
    f=OUT/path;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(text,encoding='utf-8')
def read_json(p,default):
    try:return json.loads((ROOT/p).read_text(encoding='utf-8'))
    except (FileNotFoundError,json.JSONDecodeError):return default

def document(title,desc,path,body,robots='index,follow'):
    url=BASE+path
    return f'''<!doctype html><html lang="ko"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{h(title)} | PIQ PAQ POQ</title><meta name="description" content="{h(desc)}"><meta name="robots" content="{h(robots)}"><link rel="canonical" href="{h(url)}"><meta property="og:title" content="{h(title)}"><meta property="og:description" content="{h(desc)}"><meta property="og:url" content="{h(url)}"><style>{CSS}</style><script async src="https://www.googletagmanager.com/gtag/js?id=G-4Q7P01BEHT"></script><script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-4Q7P01BEHT');</script><script defer src="{BASE}assets/js/ppq_analytics_events.js"></script></head><body><header class="head"><a href="{BASE}">PIQ PAQ POQ</a><nav class="nav"><a href="{BASE}">홈</a><a href="{BASE}new-products/2026/11/week-3.html">11월 신상</a><a href="{BASE}discover/">신상품 발견</a><a href="{BASE}insights/">성과 분석</a></nav></header><main class="wrap">{body}<footer class="footer">PIQ PAQ POQ · 사실 확인 후 발행 · 쇼핑/광고 링크 사용 시 명시적으로 고지합니다.</footer></main></body></html>'''

def as_dt(x):
    try:
        d=datetime.fromisoformat(str(x).replace('Z','+00:00'))
        if not d.tzinfo:d=d.replace(tzinfo=timezone.utc)
        return d.astimezone(timezone.utc)
    except (ValueError,TypeError):return None

def domain_ok(url):
    try:
        u=urlparse(url);return u.scheme=='https' and bool(u.netloc)
    except (TypeError,ValueError):return False

BRANDS=[('CU',r'(?<![a-z])CU(?![a-z])|\b씨유\b'),('GS25',r'GS\s?25|지에스25'),('세븐일레븐',r'세븐일레븐|7-?ELEVEN'),('이마트24',r'이마트\s?24')]
INTENT=re.compile(r'신제품|신상품|신상|신메뉴|출시|선보|단독|새로|협업',re.I)

def candidates():
    data=read_json('data/rss-news.json',{'items':[]})
    now=datetime.now(timezone.utc)
    found=[];seen=set()
    for x in data.get('items',[]):
        title=str(x.get('title','')).strip();url=str(x.get('url','')).strip();d=as_dt(x.get('publishedAt') or x.get('date'))
        if not title or not domain_ok(url) or not d or not (now-timedelta(days=8)<=d<=now+timedelta(hours=8)):continue
        brand=next((name for name,pattern in BRANDS if re.search(pattern,title,re.I)),None)
        if not brand or not INTENT.search(title):continue
        # Repeated titles and duplicate source URLs are suppressed.
        key=(brand,re.sub(r'\s+','',title.lower())[:125])
        if key in seen:continue
        seen.add(key)
        found.append({'id':str(x.get('id') or len(found)), 'brand':brand,'title':title[:240],
                      'url':url,'publishedAt':d.isoformat(),'source':str(x.get('source','원문 확인 필요'))[:80],
                      'status':'검증 대기','sourceType':'RSS 기사 · 공식 확인 전'})
    found.sort(key=lambda x:x['publishedAt'],reverse=True)
    return {'updatedAt':now.isoformat(),'count':len(found),'items':found[:120]}

def review_queue(data):
    cards=''.join(f'''<article class="card candidate" data-brand="{h(x['brand'])}" data-text="{h(x['title'].lower())}"><span class="pill">{h(x['brand'])} · 검증 대기</span><h2 style="font-size:18px;margin:12px 0">{h(x['title'])}</h2><p class="muted">{h(x['source'])} · {h(x['publishedAt'][:10])}</p><p><a href="{h(x['url'])}" target="_blank" rel="noopener noreferrer">보도 원문 열기</a></p><p class="small">가격·출시일·공식 여부를 확정한 상품이 아닙니다.</p></article>''' for x in data['items'])
    body=f'''<p class="pill">DISCOVER · 수집 후 검증 대기</p><h1>이번 주 편의점 신상, 확인 전 기사</h1><p class="lead">CU·GS25·세븐일레븐·이마트24 관련 RSS 제목에서 신상품 후보를 자동 발견합니다. <strong>기사 내용은 신상품 확정 자료가 아닙니다.</strong> 가격과 출시일은 개별 공식 자료를 확인한 뒤에만 확정 발행합니다.</p><div class="warn">검색용 상품 상세 페이지는 운영자가 reviewed=true, 공식 출처, 출시일 및 가격 근거를 검증한 후에만 생성합니다. 기사 원문을 복제하지 않습니다.</div><div class="filters"><input type="search" id="keyword" placeholder="브랜드·상품명 검색" aria-label="검색"><select id="brand" aria-label="편의점 필터"><option value="">모든 브랜드</option>{''.join(f'<option>{h(b)}</option>' for b,_ in BRANDS)}</select></div><p class="muted" id="counter">{len(data['items'])}건 후보 · 수집 시각 {h(data['updatedAt'][:16])} UTC</p><section class="grid" id="list">{cards or '<p class="muted">최근 8일간 일치하는 후보가 없습니다.</p>'}</section><script>(function(){{const q=document.querySelector('#keyword'),b=document.querySelector('#brand'),n=document.querySelector('#counter');function update(){{let c=0;document.querySelectorAll('.candidate').forEach(e=>{{let yes=(!b.value||e.dataset.brand===b.value)&&(!q.value||e.dataset.text.includes(q.value.toLowerCase()));e.hidden=!yes;if(yes)c++}});n.textContent=c+'건 표시 · 후보는 아직 검증 전입니다.'}}q.addEventListener('input',update);b.addEventListener('change',update)}})();</script>'''
    write('discover/index.html', document('편의점 신상 발견·검증 대기', 'CU GS25 세븐일레븐 이마트24 최근 신상품 관련 기사 발견 목록. 공식 확인 전 후보만 표시합니다.', 'discover/',body,robots='noindex,follow'))

def verify(entry):
    if not isinstance(entry,dict) or entry.get('reviewed') is not True:return 'reviewed 필수'
    slug=str(entry.get('slug',''))
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',slug):return 'slug 영문 소문자/숫자/하이픈만 허용'
    if not all(str(entry.get(x,'')).strip() for x in ['brand','name','summary','price','releaseDate','officialUrl','verifiedAt','proof']):return '필수 사실 필드 누락'
    if not domain_ok(entry['officialUrl']):return '공식 출처 URL HTTPS 필요'
    if entry['brand'] not in ['CU','GS25','세븐일레븐','이마트24']:return '지원하지 않는 브랜드'
    for key in ['verifiedAt','releaseDate']:
        try:datetime.strptime(entry[key],'%Y-%m-%d')
        except (ValueError,TypeError):return key+' 날짜 형식 오류'
    if entry['verifiedAt']>TODAY:return '미래 검증일'
    if entry['verifiedAt'] < (datetime.now(ZoneInfo("Asia/Seoul")).date()-timedelta(days=31)).isoformat():return '검증일 31일 초과'
    if len(entry['summary'])<45 or len(entry['proof'])<20:return '근거·설명 부족'
    # This is a structural check, not an automated fact-check or official-site visit.
    return None

def approved_pages():
    data=read_json('data/verified-products.json',{'products':[]})
    accepted=[];rejected=[];slugs=set()
    for p in data.get('products',[]):
        reason=verify(p)
        if p.get('slug') in slugs:reason='slug 중복'
        if reason:rejected.append({'slug':str(p.get('slug','?')),'reason':reason});continue
        slugs.add(p['slug']);accepted.append(p)
        path='products/'+p['slug']+'.html'
        title=p.get('seoTitle') or f"{p['brand']} {p['name']} 가격·출시일·판매 조건"
        facts=[('상품명',p['name']),('브랜드',p['brand']),('출시일',p['releaseDate']),('가격',p['price']),('확인일',p['verifiedAt'])]
        rows=''.join(f'<tr><th>{h(k)}</th><td>{h(v)}</td></tr>' for k,v in facts)
        external=f'<p><a href="{h(p["officialUrl"])}" rel="noopener noreferrer" target="_blank">공식 원문에서 출시·가격 조건 확인</a></p>'
        body=f'''<p class="pill">{h(p['brand'])} · 운영자 검증</p><h1>{h(title)}</h1><p class="lead">{h(p['summary'])}</p><section class="panel"><h2>출시·가격 핵심 정보</h2><div class="scroll"><table>{rows}</table></div></section><section class="panel"><h2>출처와 확인 근거</h2><p>{h(p['proof'])}</p>{external}<p class="muted">판매 여부·재고·할인 조건은 실제 점포에서 달라질 수 있습니다. 직접 사용 후기나 구매 경험을 주장하지 않습니다.</p></section><p><a href="{BASE}new-products/2026/11/week-3.html">11월 셋째 주 신상 확인</a></p>'''
        page=document(title,p['summary'][:155],path,body)
        schema={'@context':'https://schema.org','@type':'Article','headline':title,
                'datePublished':p['verifiedAt'],'dateModified':p['verifiedAt'],
                'description':p['summary'],'inLanguage':'ko-KR',
                'mainEntityOfPage':{'@type':'WebPage','@id':BASE+path},
                'author':{'@type':'Organization','name':'PIQ PAQ POQ'},
                'about':{'@type':'Product','name':p['name'],'brand':{'@type':'Brand','name':p['brand']}}}
        jsonld=json.dumps(schema,ensure_ascii=False).replace('<','\\u003c')
        page=page.replace('</head>','<script type=\"application/ld+json\">'+jsonld+'</script></head>',1)
        write(path,page)
    # This file is used only for diagnostics, never silently turns RSS into verified content.
    write('data/verified-build-status.json',json.dumps({'approved':len(accepted),'rejected':rejected},ensure_ascii=False,indent=2))
    return accepted

def local_dashboard():
    body='''<span class="pill">INSIGHTS · 운영자용 로컬 분석</span><h1>콘텐츠 클릭·수익 성과 분석</h1><p class="lead">GA4 이벤트 CSV와 제휴 실적 CSV를 이 브라우저에서 직접 불러와 비교합니다. <strong>서버에 업로드하거나 공개하지 않습니다.</strong> 가짜 방문자·매출은 표시하지 않습니다.</p><div class="warn">이 페이지는 공개 주소이지만 파일 선택 전에는 데이터가 없습니다. 실적 원본 CSV를 GitHub 저장소에 업로드하지 마세요. 이 도구는 자동 GA4 API 연동이 아니며 로컬 분석 보조 도구입니다.</div>
<section class="panel"><h2>1. GA4 외부 클릭 집계 가져오기</h2><p class="muted">권장 CSV 열: event_name,link_type,link_domain,page_section,event_count,content_slug,period. GA4 탐색 분석에서 내보낸 CSV는 열 이름이 다를 수 있으므로 표준 형식으로 정리해 사용하세요.</p><input id="ga" aria-label="GA4 CSV 선택" type="file" accept=".csv,text/csv"><p id="ga-status" class="muted">데이터 없음</p></section>
<section class="panel"><h2>2. 제휴 실적 가져오기 (선택)</h2><p class="muted">권장 CSV 열: content_slug,clicks,orders,revenue,commission,period. 판매 보고서의 개인 정보는 제외한 뒤 불러오세요.</p><input id="affiliate" aria-label="제휴 CSV 선택" type="file" accept=".csv,text/csv"><p id="affiliate-status" class="muted">데이터 없음</p></section>
<section class="grid" aria-label="요약 지표"><div class="card"><div class="small">GA4 외부 클릭</div><div class="stat" id="clicks">—</div></div><div class="card"><div class="small">제휴 주문 건수</div><div class="stat" id="orders">—</div></div><div class="card"><div class="small">제휴 수수료 (원)</div><div class="stat" id="commission">—</div></div></section>
<section class="panel"><h2>3. 링크 유형별 클릭</h2><div class="scroll"><table><thead><tr><th>링크 유형</th><th>외부 클릭</th><th>비중</th></tr></thead><tbody id="types"><tr><td colspan="3">분석할 파일을 선택하세요.</td></tr></tbody></table></div></section>
<section class="panel"><h2>4. 콘텐츠별 비교 (같은 slug가 있을 때)</h2><div class="scroll"><table><thead><tr><th>콘텐츠 slug</th><th>클릭</th><th>주문</th><th>수수료(원)</th></tr></thead><tbody id="by-content"><tr><td colspan="4">분석할 파일을 선택하세요.</td></tr></tbody></table></div><p class="muted">출처가 다른 클릭과 주문은 개별 방문자의 전환으로 결합할 수 없습니다. 같은 콘텐츠 식별자가 있는 경우 합계 비교만 수행합니다.</p></section>
<section class="panel"><h2>5. 검색 결과 제목 개선 체크</h2><ol><li>상품명과 브랜드명이 제목 앞에 있는가?</li><li>가격을 쓸 경우 실제 기본가와 조건부 할인을 구분했는가?</li><li>출시일·할인 기간·재고처럼 클릭 전에 알아야 할 조건을 넣었는가?</li><li>과장된 1위·역대급·무조건 최저가를 검증 없이 쓰지 않았는가?</li><li>Search Console에서 노출이 충분히 쌓인 뒤 CTR을 비교하는가?</li></ol><p class="muted">동일 기간/유사 검색어/노출 순위의 차이를 고려하지 않은 CTR 비교만으로 좋은 제목을 단정하지 않습니다.</p></section>
<script src="../assets/js/ppq_local_insights.js" defer></script>'''
    write('insights/index.html',document('운영자 클릭·제휴 수익 분석','GA4 외부 링크 클릭과 제휴 수익 CSV를 브라우저에서만 분석하는 운영자 도구','insights/',body,robots='noindex,nofollow'))

JS=r'''(function(){'use strict';
// Files stay within browser; there are no fetch/XHR/network calls or persistence.
const $=id=>document.getElementById(id), rows={ga:[],affiliate:[]};
function parseCSV(text){const data=[],out=[];let field='',line=[],quoted=false;for(let i=0;i<text.length;i++){let c=text[i];if(c==='"'){if(quoted&&text[i+1]==='"'){field+='"';i++;}else quoted=!quoted;}else if(c===','&&!quoted){line.push(field);field='';}else if((c==='\n'||c==='\r')&&!quoted){if(c==='\r'&&text[i+1]==='\n')i++;line.push(field);if(line.some(x=>x.trim()))data.push(line);line=[];field='';}else field+=c;}line.push(field);if(line.some(x=>x.trim()))data.push(line);if(!data.length)return [];let heads=data.shift().map(x=>x.replace(/^\uFEFF/,'').trim().toLowerCase());for(const row of data){const o={};heads.forEach((h,i)=>o[h]=(row[i]||'').trim());out.push(o);}return out;}
function num(v){const x=Number(String(v||'0').replace(/,/g,''));return Number.isFinite(x)&&x>=0?x:0;}
function fmt(n){return Math.round(n).toLocaleString('ko-KR')}
function trow(cells){const tr=document.createElement('tr');cells.forEach(v=>{const td=document.createElement('td');td.textContent=String(v);tr.appendChild(td)});return tr;}
function render(){const ga=rows.ga.filter(x=>x.event_name==='ppq_outbound_click'),af=rows.affiliate;const sum=(arr,key)=>arr.reduce((n,x)=>n+num(x[key]),0);const clicks=sum(ga,'event_count'),orders=sum(af,'orders'),commission=sum(af,'commission');$('clicks').textContent=rows.ga.length?fmt(clicks):'—';$('orders').textContent=af.length?fmt(orders):'—';$('commission').textContent=af.length?fmt(commission):'—';
const byType={};ga.forEach(x=>{const k=x.link_type||'미분류';byType[k]=(byType[k]||0)+num(x.event_count)});let target=$('types');target.textContent='';Object.entries(byType).sort((a,b)=>b[1]-a[1]).forEach(([k,v])=>target.appendChild(trow([k,fmt(v),clicks?(100*v/clicks).toFixed(1)+'%':'0%'])));if(!target.children.length)target.appendChild(trow(['이벤트 없음 또는 CSV 형식 확인','—','—']));
const map={};ga.forEach(x=>{const k=x.content_slug||'식별자 없음';(map[k]??={clicks:0,orders:0,commission:0}).clicks+=num(x.event_count)});af.forEach(x=>{const k=x.content_slug||'식별자 없음';let obj=(map[k]??={clicks:0,orders:0,commission:0});obj.orders+=num(x.orders);obj.commission+=num(x.commission)});target=$('by-content');target.textContent='';Object.entries(map).sort((a,b)=>b[1].clicks-a[1].clicks).forEach(([k,v])=>target.appendChild(trow([k,fmt(v.clicks),fmt(v.orders),fmt(v.commission)])));if(!target.children.length)target.appendChild(trow(['데이터 없음','—','—','—']));}
['ga','affiliate'].forEach(k=>{$(k).addEventListener('change',async e=>{const file=e.target.files[0];if(!file)return;if(file.size>2_000_000){$(k+'-status').textContent='2MB 이하 파일만 선택하세요';return}try{const result=parseCSV(await file.text());const required=k==='ga'?['event_name','link_type','event_count']:['content_slug','orders','commission'];if(!result.length||required.some(x=>!(x in result[0])))throw Error('열 이름을 확인하세요: '+required.join(', '));rows[k]=result;$(k+'-status').textContent=result.length+'행을 이 브라우저에서만 읽었습니다.';render();}catch(err){rows[k]=[];$(k+'-status').textContent='형식 확인 필요: '+err.message;render();}})});})();'''

def merge_sitemap(paths):
    xml=OUT/'sitemap.xml'
    if not xml.exists():return
    s=xml.read_text(encoding='utf-8')
    new=[]
    for path in paths:
        loc=BASE+path
        if '<loc>'+loc+'</loc>' not in s:new.append(f'  <url><loc>{html.escape(loc)}</loc></url>\n')
    if new:s=s.replace('</urlset>',''.join(new)+'</urlset>');xml.write_text(s,encoding='utf-8')

def add_site_nav():
    f=OUT/'index.html'
    if not f.exists():raise SystemExit('Deploy must copy index.html before build_pipeline')
    s=f.read_text(encoding='utf-8');marker='<!-- PPQ PIPELINE NAV -->'
    if marker not in s:
        block=(f'{marker}<nav aria-label="신상품 탐색과 성과 분석" style="margin:8px auto;max-width:1300px;padding:12px 22px;display:flex;flex-wrap:wrap;gap:16px;font:600 14px/1.7 system-ui,sans-serif">'
               f'<a href="{BASE}discover/">새 신상품 후보 확인</a><a href="{BASE}insights/">성과 분석 도구</a></nav>')
        s=s.replace('</header>','</header>'+block,1)
    f.write_text(s,encoding='utf-8')

def main():
    if not (OUT/'index.html').exists():raise SystemExit('Please run build_seo.py first')
    c=candidates();write('data/discovery-candidates.json',json.dumps(c,ensure_ascii=False,indent=2))
    review_queue(c)
    approved=approved_pages()
    local_dashboard()
    write('assets/js/ppq_local_insights.js',JS)
    merge_sitemap(['products/'+p['slug']+'.html' for p in approved])
    add_site_nav()
    print('discovery candidates:',c['count'],'verified product pages:',len(approved),'local analytics workspace: yes')
if __name__=='__main__':main()
