import datetime as dt
import importlib.util
import pathlib
import unittest

spec = importlib.util.spec_from_file_location("rss", pathlib.Path(__file__).with_name("collect_rss.py"))
rss = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rss)
NOW = dt.datetime(2026, 11, 17, 0, 0, tzinfo=dt.timezone.utc)
SOURCE = {"url": "https://news.google.com/rss/search?q=CU", "category": "편의점", "topic": "신제품·신메뉴"}


def fixture(items):
    return ("<rss><channel>" + items + "</channel></rss>").encode()


def entry(title, link="https://example.com/article", date="Mon, 16 Nov 2026 10:00:00 +0900", source="언론사"):
    return f"<item><title>{title}</title><link>{link}</link><pubDate>{date}</pubDate><source>{source}</source></item>"


class RssTests(unittest.TestCase):
    def test_stale_missing_future_dates_are_not_new_products(self):
        xml = fixture(entry("유효 기사") + entry("오래된 기사", date="Mon, 02 Nov 2026 10:00:00 +0900")
                      + entry("날짜 없음", date="") + entry("미래 기사", date="Fri, 20 Nov 2026 10:00:00 +0900"))
        items = rss.parse_feed(xml, SOURCE, NOW, 7)
        self.assertEqual([x["title"] for x in items], ["유효 기사"])
        self.assertNotIn("launchDate", items[0])
        self.assertNotIn("price", items[0])

    def test_blocked_sources_and_hiring_are_excluded(self):
        xml = fixture(entry("CU 채용", link="https://example.com/job")
                      + entry("퍅미 상품", link="https://example.com/item")
                      + entry("CU 신상", link="https://pyakmi.com/products/613")
                      + entry("CU 새 메뉴", source="Pyakmi"))
        self.assertEqual(rss.parse_feed(xml, SOURCE, NOW, 7), [])

    def test_duplicate_links_and_titles_merge_topics(self):
        first = rss.parse_feed(fixture(entry("CU 신메뉴 - 언론사", link="https://example.com/a?utm_source=x")), SOURCE, NOW, 7)[0]
        second = dict(first, url="https://example.com/a", topics=["할인·쿠폰·증정"])
        third = dict(first, url="https://other.example.com/same", topics=["협업·굿즈·팝업"])
        merged = rss.merge_items([first, second, third], NOW, 7)
        self.assertEqual(len(merged), 1)
        self.assertEqual(len(merged[0]["topics"]), 3)
        self.assertEqual(merged[0]["url"], "https://example.com/a")

    def test_invalid_feed_is_not_successful_empty_result(self):
        with self.assertRaises(ValueError):
            rss.parse_feed(b"<html>blocked</html>", SOURCE, NOW, 7)

    def test_unsafe_xml_is_rejected(self):
        with self.assertRaises(ValueError):
            rss.parse_feed(b'<!DOCTYPE rss [<!ENTITY x "test">]><rss><channel/></rss>', SOURCE, NOW, 7)

    def test_bad_links_are_excluded(self):
        self.assertEqual(rss.parse_feed(fixture(entry("CU 신상", link="javascript:alert(1)")), SOURCE, NOW, 7), [])


if __name__ == "__main__":
    unittest.main()
