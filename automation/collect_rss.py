"""Collect configured news RSS metadata only. No paid API and no article scraping."""
import concurrent.futures
import datetime as dt
import email.utils
import hashlib
import html
import json
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

UTC = dt.timezone.utc
ROOT = Path(__file__).resolve().parent.parent
BLOCKED = ("pyakmi", "퍅미")
EXCLUDED = ("채용", "구인", "창업설명회")


def clean(value):
    return html.unescape(re.sub(r"<[^>]*>", "", value or "")).strip()


def canonical_url(value):
    parts = urllib.parse.urlsplit(value.strip())
    host = (parts.hostname or "").lower()
    if parts.scheme != "https" or not host or any(x in host for x in BLOCKED):
        raise ValueError("unsupported article URL")
    pairs = [(k, v) for k, v in urllib.parse.parse_qsl(parts.query, keep_blank_values=True)
             if not k.lower().startswith("utm_") and k.lower() not in ("gclid", "fbclid")]
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, parts.path,
                                   urllib.parse.urlencode(pairs), ""))


def parse_feed(xml, source, now, days):
    if len(xml) > 2_000_000 or b"\x00" in xml or re.search(br"<!\s*(?:DOCTYPE|ENTITY)", xml, re.I):
        raise ValueError("unsupported XML")
    root = ET.fromstring(xml)
    if root.tag != "rss" or root.find("channel") is None:
        raise ValueError("not an RSS feed")
    results = []
    for item in root.findall("./channel/item"):
        title = clean(item.findtext("title"))
        publisher = clean(item.findtext("source")) or urllib.parse.urlsplit(source["url"]).hostname
        if not title or any(x in (title + " " + publisher).lower() for x in BLOCKED + EXCLUDED):
            continue
        try:
            date = email.utils.parsedate_to_datetime(item.findtext("pubDate") or "")
            if date.tzinfo is None:
                continue
            date = date.astimezone(UTC)
            if not now - dt.timedelta(days=days) <= date <= now + dt.timedelta(minutes=5):
                continue
            url = canonical_url(item.findtext("link") or "")
        except (ValueError, TypeError, OverflowError):
            continue
        results.append({
            "id": hashlib.sha256(url.encode()).hexdigest()[:24],
            "title": title, "url": url, "source": publisher,
            "publishedAt": date.isoformat(),
            "categories": [source["category"]], "topics": [source["topic"]],
            "linkType": "Google 뉴스 경유" if urllib.parse.urlsplit(url).hostname == "news.google.com" else "기사 링크",
        })
    return results


def title_key(item):
    title = item["title"]
    publisher = item.get("source", "")
    if publisher and title.endswith(" - " + publisher):
        title = title[:-(len(publisher) + 3)]
    return re.sub(r"[\W_]+", "", title.casefold())


def merge_items(items, now, days):
    merged, by_url, by_title = [], {}, {}
    for item in items:
        try:
            when = dt.datetime.fromisoformat(item["publishedAt"]).astimezone(UTC)
            if not now - dt.timedelta(days=days) <= when <= now + dt.timedelta(minutes=5):
                continue
            url = canonical_url(item["url"])
        except (KeyError, ValueError, TypeError):
            continue
        key = title_key(item)
        target = by_url.get(url) or (by_title.get(key) if key else None)
        if target is None:
            target = dict(item, url=url, categories=list(item.get("categories", [])),
                          topics=list(item.get("topics", [])))
            merged.append(target)
        else:
            target["categories"] = sorted(set(target["categories"] + item.get("categories", [])))
            target["topics"] = sorted(set(target["topics"] + item.get("topics", [])))
        by_url[url] = target
        if key:
            by_title[key] = target
    return sorted(merged, key=lambda x: (x["publishedAt"], x["id"]), reverse=True)


def fetch_feed(source, config, now):
    parsed = urllib.parse.urlsplit(source["url"])
    if parsed.scheme != "https" or parsed.hostname != "news.google.com":
        raise ValueError("only configured Google News RSS is supported")
    request = urllib.request.Request(source["url"], headers={
        "User-Agent": "PIQPAQPOQ-RSS/1.0",
        "Accept": "application/rss+xml, application/xml, text/xml",
    })
    with urllib.request.urlopen(request, timeout=config["timeout_seconds"]) as response:
        final = urllib.parse.urlsplit(response.geturl())
        if final.scheme != "https" or final.hostname != "news.google.com":
            raise ValueError("unexpected RSS redirect")
        xml = response.read(config["max_bytes"] + 1)
    if len(xml) > config["max_bytes"]:
        raise ValueError("feed too large")
    return parse_feed(xml, source, now, config["days"])


def main():
    config = json.loads((ROOT / "automation/rss-sources.json").read_text())
    now = dt.datetime.now(UTC)
    destination = ROOT / "data/rss-news.json"
    old = json.loads(destination.read_text()) if destination.exists() else {"items": []}
    results, status, successful = [], [], 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        jobs = {pool.submit(fetch_feed, source, config, now): source for source in config["feeds"]}
        for job in concurrent.futures.as_completed(jobs):
            source = jobs[job]
            try:
                items = job.result()
                results.extend(items)
                status.append({"id": source["id"], "status": "ok", "items": len(items)})
                successful += 1
            except Exception as error:
                status.append({"id": source["id"], "status": "failed", "error": type(error).__name__})
    if successful == 0:
        print("All feeds failed. Previous data preserved.", file=sys.stderr)
        return 1
    merged = merge_items(results + old.get("items", []), now, config["days"])
    payload = {
        "checkedAt": now.isoformat(), "days": config["days"],
        "dateBasis": "기사 게시일. 상품 출시일이나 행사 유효기간이 아닙니다.",
        "items": merged, "feeds": sorted(status, key=lambda x: x["id"]),
    }
    destination.parent.mkdir(exist_ok=True)
    temporary = destination.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(destination)
    print(f"Feeds successful: {successful}/{len(config['feeds'])}; items: {len(merged)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

