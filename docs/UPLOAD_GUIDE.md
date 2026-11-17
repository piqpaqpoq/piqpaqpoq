# GitHub 직접 업로드 위치 안내

저장소: `https://github.com/piqpaqpoq/piqpaqpoq`

ZIP 압축을 푼 뒤 아래 **구조 그대로** 저장소 최상위에 넣습니다.

```text
piqpaqpoq/
├─ index.html                       ← 저장소 최상위
├─ README.md                        ← 저장소 최상위
├─ .gitignore                       ← 저장소 최상위
├─ assets/
│  ├─ css/style.css
│  ├─ js/app.js
│  └─ characters/
│     ├─ piqi.svg
│     ├─ paqi.svg
│     └─ poqi.svg
├─ automation/
│  ├─ collect_rss.py
│  ├─ rss-sources.json
│  └─ test_collect_rss.py
├─ data/
│  └─ rss-news.json
├─ .github/
│  └─ workflows/rss.yml             ← Actions 설정
└─ docs/
   └─ UPLOAD_GUIDE.md
```

## 업로드

1. GitHub 저장소 `Code` 탭 → `Add file` → `Upload files`.
2. ZIP이 아니라 압축을 푼 폴더 안의 파일·폴더를 업로드합니다. 숨김 폴더 `.github`가 포함됐는지 확인하세요.
3. `Commit changes`를 누릅니다.
4. `Actions` 탭 → `PIQPAQPOQ RSS Collector` → `Run workflow` → `check` → 실행.
5. `check` 성공 후 `collect` 실행 → `data/rss-news.json`에 데이터가 생겼는지 확인합니다.

**주의:** 휴대전화의 GitHub 웹 업로드는 중첩 폴더 업로드가 불편할 수 있습니다. 가능하면 컴퓨터 브라우저에서 압축 해제 후 업로드하세요. `.github`가 누락되면 워크플로가 보이지 않습니다.

## 자동 실행은 나중에

`rss.yml`의 `schedule` 세 줄은 주석 상태입니다. 과금 차단 설정을 확인한 후 주석을 제거하면 한국시간 매일 07시, 13시, 19시에 예약됩니다. GitHub 예약 실행은 몇 분 이상 지연될 수 있습니다.

## 배포는 별도

GitHub에 파일을 넣는 것은 **백업 및 코드 저장**입니다. 웹사이트 배포가 아닙니다. 현재 ChatGPT Sites 주소는 별도로 유지되며, 이 JSON을 자동으로 읽지 않습니다. 정적 배포가 필요하면 Cloudflare Pages 같은 별도 호스팅을 설정해야 합니다.
