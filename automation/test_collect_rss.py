import datetime as dt
import unittest
from collect_rss import parse_date, extract_entries, unique_recent

NOW = dt.datetime(2026, 11, 17, 3, 0, tzinfo=dt.timezone.utc)
FEED = {'id':'test','name':'테스트','category':'food'}


class TestCollector(unittest.TestCase):
    def test_rfc_date(self):
        self.assertEqual(parse_date('Tue, 17 Nov 2026 02:00:00 GMT'), NOW - dt.timedelta(hours=1))

    def test_iso_date(self):
        self.assertEqual(parse_date('2026-11-17T02:00:00Z'), NOW - dt.timedelta(hours=1))

    def test_rss_recent_only(self):
        xml = b'''<rss><channel><item><title>New product</title><link>https://example.com/1</link><pubDate>Tue, 17 Nov 2026 02:00:00 GMT</pubDate></item><item><title>Old product</title><link>https://example.com/2</link><pubDate>Sun, 01 Nov 2026 02:00:00 GMT</pubDate></item></channel></rss>'''
        rows = extract_entries(xml, FEED, NOW, 7)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['title'], 'New product')

    def test_atom(self):
        xml = b'''<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>New</title><link href="https://example.com/1"/><updated>2026-11-17T02:00:00Z</updated></entry></feed>'''
        self.assertEqual(len(extract_entries(xml, FEED, NOW, 7)), 1)

    def test_duplicates(self):
        row = {'url':'https://example.com/1','publishedAt':'2026-11-17T02:00:00Z'}
        self.assertEqual(len(unique_recent([row,row],NOW,7,10)),1)

    def test_future_rejected(self):
        row = {'url':'https://example.com/1','publishedAt':'2026-11-19T02:00:00Z'}
        self.assertEqual(len(unique_recent([row],NOW,7,10)),0)


if __name__ == '__main__':
    unittest.main()
