/* PIQ PAQ POQ: categorizes outbound clicks for GA4 without personal data. */
(function () {
  'use strict';
  if (window.__ppqAnalyticsClickEvents) return;
  window.__ppqAnalyticsClickEvents = true;
  const shop = ['coupang.com','smartstore.naver.com','shopping.naver.com','11st.co.kr','gmarket.co.kr','auction.co.kr'];
  const social = ['youtube.com','youtu.be','instagram.com','tiktok.com','x.com','threads.net'];
  const matchHost = (host, d) => host === d || host.endsWith('.' + d);
  function classify(a, host) {
    const label = (a.textContent || '').replace(/\s+/g,' ').trim();
    if (shop.some(d => matchHost(host,d))) return 'shopping_link';
    if (/공식\s*(행사|홈페이지|웹사이트|인스타그램|스토어)|브랜드 홈페이지/.test(label)) return 'official_brand_link';
    if (/기사\s*원문|원문\s*보기|출처\s*원문|보도자료/.test(label)) return 'source_article_link';
    if (matchHost(host,'news.google.com')) return 'news_aggregator_link';
    if (social.some(d => matchHost(host,d))) return 'social_media_link';
    return 'other_external_link';
  }
  document.addEventListener('click', function (ev) {
    const origin = ev.target;
    if (!origin || !origin.closest) return;
    const anchor = origin.closest('a[href]');
    if (!anchor) return;
    let u;
    try { u = new URL(anchor.getAttribute('href'),location.href); } catch (_) { return; }
    if (!/^https?:$/.test(u.protocol) || u.origin === location.origin) return;
    if (typeof window.gtag !== 'function') return;
    window.gtag('event','ppq_outbound_click',{
      link_type: classify(anchor,u.hostname.toLowerCase()),
      link_domain: u.hostname.toLowerCase().slice(0,100),
      page_section: location.hash.slice(1,50) || 'home',
      transport_type: 'beacon'
    });
  }, {passive:true});
})();
