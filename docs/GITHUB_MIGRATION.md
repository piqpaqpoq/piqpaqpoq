# GitHub 이전 현황

- 이전일: 2026.11.17
- 대상: piqpaqpoq/piqpaqpoq, Private, main
- 원본 Sites 프로젝트: appgprj_6af930a083708191ba0d0c71ecd84b67
- 원본 소스 커밋: fdd77c4b924a63487cbc1e7620d5ae6b464b1290
- 방식: 최신 소스 스냅샷 복사. 기존 Git 커밋 이력 전체를 합친 것은 아닙니다.
- page.html, worker/index.js, assets/characters 및 기존 스크립트·설정을 그대로 복사했습니다.
- 기존 GitHub 프로필 README는 보존했고, Sites README는 docs/SITES_README.md에 두었습니다.
- 토큰·환경 변수 값·서버 방문자 식별값·문의 기록은 포함하지 않았습니다.

## 검증
- RSS 날짜·중복·차단 출처·XML 검증 테스트 6개 통과
- npm run build 및 npm run validate 통과
- 첫 RSS 수집: 15개 중 15개 피드 성공, 기사 메타데이터 329건
- 카페·커피 할인 피드의 일시 오류는 개별 재시도로 복구했습니다.

## 남은 연결
- 공개 서비스는 기존 Sites에서 계속 운영됩니다.
- GitHub 커밋이 Sites에 자동 배포되지는 않습니다.
- GitHub data/rss-news.json은 아직 공개 사이트로 자동 전달되지 않습니다.
- 방문자 집계·공식 행사 스냅샷 등 서버 데이터는 기존 저장소에 남아 있습니다.
- 하루 3회 예약은 무료 사용량·초과 사용 중단 설정 확인 후 적용합니다.
- GitHub Actions 실행 #1의 check 작업 성공을 확인했습니다(2026.11.17 09:26 한국시간). collect 작업은 실행하지 않았습니다. 이번에 추가한 사이트 빌드 단계는 로컬 검증만 완료했습니다.

## 로컬 실행
```sh
python3 -m unittest discover -s automation -p 'test_*.py' -v
npm run build
npm run validate
python3 automation/collect_rss.py
```
