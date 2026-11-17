import sys
import tempfile
import json
import unittest
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_offers import validate_offer, build, press_candidates, official_url

TODAY = date(2026, 11, 17)


def valid():
    return {
        "id": "offer-1", "brand": "CU", "title": "테스트 증정 행사", "price": 2000,
        "paid": 1, "free": 1, "startDate": "2026-11-01", "endDate": "2026-11-30",
        "conditions": "일부 점포 제외 및 재고 소진 시 종료", "verifiedAt": "2026-11-17",
        "officialUrl": "https://cu.bgfretail.com/event/plus.do?item=123", "reviewed": True,
    }


class OfferBuildTests(unittest.TestCase):
    def test_verified_math(self):
        x, reason = validate_offer(valid(), TODAY)
        self.assertFalse(reason)
        self.assertEqual(x["total"], 2000)
        self.assertEqual(x["qty"], 2)
        self.assertEqual(x["each"], 1000)

    def test_fake_domain_rejected(self):
        x = valid(); x["officialUrl"] = "https://cu.bgfretail.com.evil.example/event"
        self.assertIsNone(validate_offer(x, TODAY)[0])

    def test_unreviewed_rejected(self):
        x = valid(); x["reviewed"] = False
        self.assertIsNone(validate_offer(x, TODAY)[0])

    def test_expired_rejected(self):
        x = valid(); x["endDate"] = "2026-11-16"
        self.assertIsNone(validate_offer(x, TODAY)[0])

    def test_stale_verification_rejected(self):
        x = valid(); x["verifiedAt"] = "2026-10-01"
        self.assertIsNone(validate_offer(x, TODAY)[0])

    def test_news_not_verified(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "discover.json").write_text(json.dumps({"items":[{"title":"스타벅스 할인 쿠폰 행사", "url":"https://news.example/story", "source":"언론", "date":"2026-11-16T00:00:00+09:00"}]}), encoding="utf-8")
            (root / "official-offers-curated.json").write_text('{"items":[]}', encoding="utf-8")
            x = build(root, TODAY)
            self.assertEqual(len(x["items"]), 0)
            self.assertEqual(len(x["candidates"]), 1)
            self.assertEqual(x["candidates"][0]["status"], "언론 보도 · 공식 확인 대기")

    def test_duplicate_official_source_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "official-offers-curated.json").write_text(json.dumps({"items": [valid(), valid()]}), encoding="utf-8")
            x = build(root, TODAY)
            self.assertEqual(len(x["items"]), 1)
            self.assertEqual(len(x["rejected"]), 1)


if __name__ == '__main__':
    unittest.main()
