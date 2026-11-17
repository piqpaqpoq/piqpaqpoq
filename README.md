# 픽팩폭 · PIQ PAQ POQ

이 저장소는 **직접 업로드용 재구성 패키지**입니다. 기존 ChatGPT Sites의 원본 소스를 완전히 복제한 파일이 아닙니다.

- `index.html`: 모바일 대응 사이트 홈
- `assets/css/style.css`: 디자인
- `assets/js/app.js`: 검색·분류·보관함·행사 계산기·RSS 목록 표시
- `assets/characters/`: 픽이·팩이·폭이 SVG (사용자가 제공한 파일)
- `automation/rss-sources.json`: RSS 15개 설정 (실제 응답 여부는 환경에 따라 다름)
- `automation/collect_rss.py`: 최근 7일 기사 제목·링크·발행일 수집
- `automation/test_collect_rss.py`: 수집기 테스트
- `data/rss-news.json`: 사이트에서 읽는 결과 데이터 (처음에는 비어 있음)
- `.github/workflows/rss.yml`: 수동 실행용 GitHub Actions

## 바로 시작

1. 이 ZIP을 컴퓨터에서 **압축 해제**합니다.
2. 압축을 푼 폴더 **안의 모든 파일과 폴더**를 GitHub 저장소 루트에 업로드합니다. ZIP 자체를 업로드하지 마세요.
3. GitHub의 `Actions` → `PIQPAQPOQ RSS Collector` → `Run workflow` → `mode: check`로 테스트합니다.
4. 성공하면 `mode: collect`로 수집합니다. `data/rss-news.json`이 업데이트됩니다.
5. 정적 웹사이트로 배포할 때 `index.html`이 있는 **루트**를 배포 디렉터리로 지정합니다. GitHub에 업로드만 하면 사이트가 자동으로 열리지는 않습니다.

## 주의

- GitHub 저장소는 **비공개로 유지**해도 됩니다. 다만 정적 사이트 호스팅은 별도로 연결해야 합니다.
- 기존 ChatGPT Sites URL에는 GitHub의 JSON이 **자동 반영되지 않습니다**. 별도의 배포/데이터 연결이 필요합니다.
- Actions 예약 실행은 **꺼져 있습니다**. 과금 차단 및 무료 사용량을 확인한 뒤 설정하세요.
- RSS 피드 15개는 구성만 완료된 상태입니다. 실제 수집 성공을 확인한 뒤 운영하세요.
- 뉴스 검색 결과는 공식 발표나 할인 조건을 검증한 결과가 아닙니다. 상품 가격·행사 조건·재고는 원문에서 확인하세요.
- 기사 본문이나 이미지는 수집·저장하지 않습니다. 출처 표시는 이용 허락이 아닙니다.
- 기존 Sites의 방문자 수, 서버 저장 자료, 기존 페이지의 세부 기능은 이 패키지에 포함되지 않습니다.
