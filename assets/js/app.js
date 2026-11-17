'use strict';
(() => {
  const $ = (s) => document.querySelector(s);
  const $$ = (s) => Array.from(document.querySelectorAll(s));
  const CATEGORY = { food: '먹거리', beauty: '뷰티·패션', life: '생활·여행' };
  const KEY = 'piqpaqpoq-saved-v1';
  let items = [], category = 'all', query = '', sort = 'new', visible = 12;
  let saved;
  try { saved = new Set(JSON.parse(localStorage.getItem(KEY) || '[]')); } catch { saved = new Set(); }
  const asText = (x) => String(x ?? '');
  const cleanDate = (s) => { const t = Date.parse(s); return Number.isFinite(t) ? new Date(t).toLocaleDateString('ko-KR', {year:'numeric',month:'2-digit',day:'2-digit'}) : '날짜 미확인'; };
  const validLink = (url) => { try { const u = new URL(url); return ['https:','http:'].includes(u.protocol) ? u.href : null; } catch { return null; } };
  const normalize = (x) => ({ id: asText(x.id || x.url), title: asText(x.title), url: validLink(x.url), source: asText(x.source || '원문'), publishedAt: asText(x.publishedAt || x.published_at), category: CATEGORY[x.category] ? x.category : 'life' });
  function updateSaved() { $('#saved-count').textContent = String(saved.size); try { localStorage.setItem(KEY, JSON.stringify([...saved])); } catch {} }
  function setCategory(c) { category = c; visible = 12; $$('.nav-link').forEach(b => b.classList.toggle('active', b.dataset.nav === c)); render(); }
  function card(item) {
    const article = document.createElement('article'); article.className = 'news-card';
    const top = document.createElement('div'); top.className = 'card-top';
    const pill = document.createElement('span'); pill.className = 'pill'; pill.textContent = CATEGORY[item.category];
    const date = document.createElement('time'); date.className = 'card-date'; date.textContent = cleanDate(item.publishedAt); if(item.publishedAt) date.dateTime = item.publishedAt;
    top.append(pill,date);
    const link = document.createElement('a'); link.className = 'card-title'; link.textContent = item.title; link.href = item.url || '#'; link.target = '_blank'; link.rel = 'noopener noreferrer'; if (!item.url) { link.removeAttribute('href'); link.removeAttribute('target'); }
    const bottom = document.createElement('div'); bottom.className = 'card-bottom';
    const source = document.createElement('span'); source.className = 'source'; source.textContent = item.source;
    const save = document.createElement('button'); save.className = 'save'; save.type = 'button'; save.setAttribute('aria-pressed', saved.has(item.id) ? 'true' : 'false'); save.textContent = saved.has(item.id) ? '★ 저장됨' : '☆ 저장';
    save.addEventListener('click', () => { if (saved.has(item.id)) saved.delete(item.id); else saved.add(item.id); updateSaved(); render(); });
    bottom.append(source,save); article.append(top,link,bottom); return article;
  }
  function render() {
    let filtered = items.filter(x => (category === 'all' || category === 'saved' && saved.has(x.id) || x.category === category) && (!query || (x.title+' '+x.source).toLocaleLowerCase().includes(query)));
    filtered.sort((a,b) => sort === 'title' ? a.title.localeCompare(b.title,'ko') : sort === 'old' ? Date.parse(a.publishedAt || 0)-Date.parse(b.publishedAt || 0) : Date.parse(b.publishedAt || 0)-Date.parse(a.publishedAt || 0));
    const cards = $('#cards'); cards.replaceChildren(...filtered.slice(0,visible).map(card));
    $('#count').textContent = String(filtered.length); $('#empty').hidden = filtered.length > 0; $('#more').hidden = filtered.length <= visible;
    $('#filter-name').textContent = category === 'all' ? '전체 카테고리' : category === 'saved' ? '내가 저장한 소식' : CATEGORY[category];
    $('#highlights').hidden = category === 'saved'; updateSaved();
  }
  $$('.nav-link').forEach(b => b.addEventListener('click', () => setCategory(b.dataset.nav)));
  $$('[data-filter]').forEach(b => b.addEventListener('click', () => { setCategory(b.dataset.filter); $('#feed-title').scrollIntoView({behavior:'smooth',block:'start'}); }));
  $('#search').addEventListener('input', e => { query = e.target.value.trim().toLocaleLowerCase(); visible=12; render(); });
  $('#sort').addEventListener('change', e => { sort=e.target.value; render(); });
  $('#reset').addEventListener('click', () => { query=''; $('#search').value=''; setCategory('all'); });
  $('#more').addEventListener('click', () => { visible+=12; render(); });
  function calc() { const n=Math.max(1,Math.floor(Number($('#quantity').value)||1)), paid=Number($('#deal').value), price=Math.max(0,Number($('#price').value)||0); const pay=Math.floor(n/(paid+1))*paid+Math.min(n%(paid+1),paid); const fmt=v=>Math.round(v).toLocaleString('ko-KR'); $('#calc-result').textContent = `${n}개 구매 시 ${pay}개 가격 결제 · ${n-pay}개 무료 · 총 ${fmt(pay*price)}원 (일반가 대비 ${fmt((n-pay)*price)}원 절약)`; }
  ['deal','quantity','price'].forEach(id => $('#'+id).addEventListener('input',calc)); calc();
  fetch('data/rss-news.json',{cache:'no-store'}).then(r=>{if(!r.ok) throw Error(`HTTP ${r.status}`); return r.json();}).then(data=>{
    items = (Array.isArray(data.items) ? data.items : []).map(normalize).filter(x=>x.title && x.url);
    const checked = data.checkedAt && !Number.isNaN(Date.parse(data.checkedAt)) ? new Date(data.checkedAt).toLocaleString('ko-KR') : '아직 수집되지 않음';
    $('#update-label').textContent = '수집 시각: '+checked; $('#total-label').textContent = `${items.length.toLocaleString('ko-KR')}개의 발견`;
    if (data.feeds?.some(x=>x.status==='error')) { const n=data.feeds.filter(x=>x.status==='error').length; $('#notice').hidden=false; $('#notice').textContent=`일부 피드(${n}개) 수집에 실패했습니다. 이전 정상 수집 결과는 보존될 수 있습니다.`; }
    render();
  }).catch(err=>{ $('#update-label').textContent='데이터 연결 확인 필요'; $('#notice').hidden=false; $('#notice').textContent='수집 데이터 파일을 읽지 못했습니다. data/rss-news.json 경로를 확인해 주세요. ('+err.message+')'; render(); });
})();
