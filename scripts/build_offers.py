#!/usr/bin/env python3
"""Build a conservative offers index for GitHub Pages.

Only explicitly reviewed, item-specific official source entries may appear in
`items`. RSS press articles become clearly marked verification candidates.
No news article is ever promoted to a verified official promotion automatically.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OFFICIAL_HOSTS = (
    "cu.bgfretail.com", "bgf.co.kr", "gsretail.com", "7-eleven.co.kr",
    "emart24.co.kr", "oliveyoung.co.kr", "starbucks.co.kr",
    "ediya.com", "paris.co.kr", "parisbaguette.com", "twosome.co.kr",
    "bhc.co.kr", "lotteeatz.com", "mcdonalds.co.kr", "burgerking.co.kr",
)
PROMO_WORDS = re.compile(r"1\s*\+\s*1|2\s*\+\s*1|3\s*\+\s*1|할인|증정|쿠폰|프로모션|세일|특가|반값|적립|사전예약|페이백|혜택")
RELEVANT_BRANDS = re.compile(r"CU|GS25|세븐일레븐|이마트24|스타벅스|파리바게뜨|올리브영|이디야|던킨|뚜레쥬르|배스킨라빈스|설빙|메가커피|컴포즈|버거킹|맥도날드|롯데리아|투썸|배민|네이버페이", re.I)
ANCHORS = ("헬로키티", "홀케이크", "포켓몬", "수능", "블랙프라이데이", "올영세일", "네이버페이", "크리스마스", "빼빼로", "사전예약", "신메뉴", "멤버십", "딸기", "쿠폰", "페이백")
STOP = {"할인", "증정", "쿠폰", "프로모션", "세일", "특가", "반값", "행사", "이벤트", "혜택", "진행", "출시", "시즌", "소식", "최대", "오늘", "신상", "유통업계", "기념", "브랜드", "사전예약", "판매", "11월", "2026년", "이달", "연말", "오는", "고객", "선보여", "한정"}


def read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def parse_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value) if re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(value)) else None
    except ValueError:
        return None


def official_url(url: str) -> bool:
    try:
        p = urlparse(url)
        host = (p.hostname or "").lower().rstrip(".")
        return p.scheme == "https" and any(host == h or host.endswith("." + h) for h in OFFICIAL_HOSTS) and p.path.strip("/") not in ("", "index", "index.html")
    except (TypeError, ValueError):
        return False


def validate_offer(row: dict, today: date) -> tuple[dict | None, str]:
    if not isinstance(row, dict) or row.get("reviewed") is not True:
        return None, "운영자 검토 미완료"
    for key in ("brand", "title", "conditions", "officialUrl"):
        if not isinstance(row.get(key), str) or not row[key].strip():
            return None, f"{key} 누락"
    url = row["officialUrl"].strip()
    if not official_url(url):
        return None, "개별 공식 URL 미확인 또는 비공식 도메인"
    start, end, checked = (parse_date(row.get(key, "")) for key in ("startDate", "endDate", "verifiedAt"))
    if not start or not end or not checked or start > end:
        return None, "행사 시작·종료·검증일 누락 또는 오류"
    if end < today:
        return None, "종료된 행사"
    if checked > today or checked < today - timedelta(days=14):
        return None, "최근 14일 이내 공식 원문 재검증 필요"
    try:
        paid, free, unit_price = int(row["paid"]), int(row["free"]), int(row["price"])
    except (KeyError, ValueError, TypeError):
        return None, "가격 또는 증정 수량 누락"
    if paid not in (1, 2, 3) or free != 1 or not 0 < unit_price <= 1_000_000:
        return None, "증정 유형 또는 가격 오류"
    if len(row["conditions"].strip()) < 5:
        return None, "행사 조건 설명 부족"
    total = paid * unit_price
    return {
        "id": str(row.get("id") or url), "brand": row["brand"].strip(),
        "title": row["title"].strip(), "paid": paid, "free": free,
        "price": unit_price, "total": total, "qty": paid + free,
        "each": round(total / (paid + free), 2),
        "volume": str(row.get("volume", "")).strip(),
        "startDate": start.isoformat(), "endDate": end.isoformat(),
        "period": f"{start.isoformat()} ~ {end.isoformat()}",
        "conditions": row["conditions"].strip(),
        "verifiedAt": checked.isoformat(), "url": url,
        "sourceType": "공식 원문 · 운영자 확인", "reviewed": True,
    }, ""


def words(text: str) -> set[str]:
    # Drop outlet suffix and common words; simple Korean headline similarity.
    text = re.sub(r"\s+[-–—]\s+[^-–—]{2,35}$", "", text)
    return {t for t in re.findall(r"[가-힣A-Za-z0-9]{2,}", text.lower()) if t not in STOP and len(t) > 1}


def press_candidates(items: list[dict], today: date, limit: int = 16) -> list[dict]:
    eligible = []
    for x in items:
        title = str(x.get("title") or "")
        if not PROMO_WORDS.search(title) or not RELEVANT_BRANDS.search(title):
            continue
        url = str(x.get("originalUrl") or x.get("url") or "")
        if urlparse(url).scheme not in ("http", "https"):
            continue
        raw_date = str(x.get("date") or x.get("publishedAt") or "")
        try:
            published = datetime.fromisoformat(raw_date.replace("Z", "+00:00")).date()
        except ValueError:
            continue
        if published < today - timedelta(days=14) or published > today + timedelta(days=1):
            continue
        eligible.append((published, x, words(title)))
    eligible.sort(key=lambda z: z[0], reverse=True)
    selected: list[dict] = []
    groups: list[set[str]] = []
    seen_signatures: set[str] = set()
    for published, x, toks in eligible:
        title = str(x.get("title") or "")
        brand = next((m.group(0).lower() for m in [RELEVANT_BRANDS.search(title)] if m), "")
        anchor = next((a for a in ANCHORS if a in title), "")
        signature = brand + ":" + anchor if brand and anchor else ""
        if signature and signature in seen_signatures:
            continue
        if any(len(toks & prev) / max(1, min(len(toks), len(prev))) >= 0.56 for prev in groups):
            continue
        if signature:
            seen_signatures.add(signature)
        groups.append(toks)
        selected.append({
            "title": str(x["title"])[:190], "url": str(x.get("originalUrl") or x["url"]),
            "source": str(x.get("source") or "언론사 미확인"),
            "publishedAt": published.isoformat(),
            "status": "언론 보도 · 공식 확인 대기",
        })
        if len(selected) >= limit:
            break
    return selected


def build(data: Path = DATA, today: date | None = None) -> dict:
    today = today or datetime.now(ZoneInfo("Asia/Seoul")).date()
    source = read_json(data / "official-offers-curated.json", {"items": []})
    entries = source.get("items", []) if isinstance(source, dict) else []
    items, rejected, urls = [], [], set()
    for n, entry in enumerate(entries):
        offer, reason = validate_offer(entry, today)
        if offer:
            if offer["url"] in urls:
                rejected.append({"entry": n + 1, "reason": "중복된 공식 행사 원문"})
                continue
            urls.add(offer["url"])
            items.append(offer)
        else:
            rejected.append({"entry": n + 1, "reason": reason})
    items.sort(key=lambda x: (x["endDate"], x["brand"], x["title"]))
    news = read_json(data / "discover.json", {"items": []})
    candidates = press_candidates(news.get("items", []), today)
    return {
        "items": items, "candidates": candidates,
        "checkedAt": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds"),
        "sources": [{"name": "운영자 검토한 공식 행사", "status": f"승인 {len(items)}건 · 제외 {len(rejected)}건"},
                    {"name": "RSS 언론 보도", "status": f"공식 확인 대기 {len(candidates)}건"}],
        "rejected": rejected, "rules": "공식 원문·조건·기간·가격·최근 14일 내 운영자 확인을 충족한 경우만 공식 행사에 표시. 뉴스는 별도 검증 대기 목록.",
    }


def main() -> int:
    result = build()
    DATA.mkdir(exist_ok=True)
    (DATA / "official-offers.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[offers] verified={len(result['items'])}, pending_press={len(result['candidates'])}, rejected={len(result['rejected'])}")
    for issue in result["rejected"]:
        print(f"[offers] excluded #{issue['entry']}: {issue['reason']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
