# 词语大树（Word Context Tree）

이번 업데이트로, 단순 CLI 프로토타입에서 **검색 + 트리맵 + 주변 단어 환경**을 보는 웹앱 형태까지 확장했습니다.

## 1) 대규모 단어 DB 접목 (CC-CEDICT)

전체급 사전 데이터와 접목하기 위해 CEDICT를 SQLite로 변환하는 스크립트를 추가했습니다.

```bash
python tools/word_tree/build_cedict_db.py
```

- 기본 다운로드 소스: CEDICT 공개 파일
- 기본 출력: `data/lexicon/cedict.db`

## 2) 서버 실행

```bash
python tools/word_tree/server.py --port 8787
```

실행 후 브라우저에서:

- `http://localhost:8787`

## 3) 첫 페이지 UX

첫 페이지에서 단어를 입력하면:

1. Treemap에서 해당 단어(노드)가 하이라이트(반짝임 스타일)됨
2. 클릭 시 주변 환경(부모/형제/자식 단어) 표시
3. 로컬 트리 + CEDICT + 위키백과/위키낱말사전 요약을 함께 보여줌

## 4) API

- `GET /api/tree` : 트리맵 데이터
- `GET /api/lookup?word=妈妈` :
  - 로컬 taxonomy 매칭 결과
  - 주변 맥락(parent/siblings/children)
  - CEDICT 결과
  - Wikipedia/Wiktionary 요약

## 5) 기존 CLI

CLI는 그대로 사용 가능합니다.

```bash
python tools/word_tree/trace_word.py 妈妈
python tools/word_tree/trace_word.py 看
```
