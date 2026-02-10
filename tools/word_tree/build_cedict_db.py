#!/usr/bin/env python3
"""CC-CEDICT 원문을 SQLite 사전 DB로 변환한다.

기본 사용:
  python tools/word_tree/build_cedict_db.py

옵션:
  --source: CEDICT 텍스트 파일 경로(없으면 자동 다운로드)
  --db: 출력 SQLite 경로
"""

from __future__ import annotations

import argparse
import gzip
import re
import sqlite3
import urllib.request
from urllib.error import URLError
from pathlib import Path

CEDICT_URL = "https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.txt.gz"
LINE_RE = re.compile(r"^(\S+)\s+(\S+)\s+\[(.*?)\]\s+/(.*)/$")


def download_cedict(dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(CEDICT_URL, dest)
    return dest


def open_source(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", errors="ignore")
    return path.open("r", encoding="utf-8", errors="ignore")


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY,
            traditional TEXT NOT NULL,
            simplified TEXT NOT NULL,
            pinyin TEXT,
            definitions TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_entries_simplified ON entries(simplified);
        CREATE INDEX IF NOT EXISTS idx_entries_traditional ON entries(traditional);
        CREATE INDEX IF NOT EXISTS idx_entries_pinyin ON entries(pinyin);
        """
    )


def import_cedict(source: Path, db_path: Path) -> int:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        init_db(conn)
        conn.execute("DELETE FROM entries")
        inserted = 0
        with open_source(source) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                m = LINE_RE.match(line)
                if not m:
                    continue
                traditional, simplified, pinyin, definitions = m.groups()
                conn.execute(
                    "INSERT INTO entries (traditional, simplified, pinyin, definitions) VALUES (?, ?, ?, ?)",
                    (traditional, simplified, pinyin, definitions.replace("/", "; ")),
                )
                inserted += 1
        conn.commit()
        return inserted
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="CC-CEDICT를 SQLite 사전 DB로 변환")
    parser.add_argument("--source", default="data/lexicon/cedict_ts.u8.gz", help="CEDICT 파일 경로")
    parser.add_argument("--db", default="data/lexicon/cedict.db", help="출력 SQLite 경로")
    args = parser.parse_args()

    source_path = Path(args.source)
    if not source_path.exists():
        print(f"CEDICT 원본이 없어 다운로드합니다: {source_path}")
        try:
            download_cedict(source_path)
        except URLError as e:
            raise SystemExit(
                "자동 다운로드 실패. 네트워크 제한/프록시 문제일 수 있습니다. "
                "--source 옵션으로 수동 다운로드한 CEDICT 파일 경로를 지정해 주세요. "
                f"원인: {e}"
            )

    count = import_cedict(source_path, Path(args.db))
    print(f"완료: {count}개 항목을 {args.db}에 저장했습니다.")


if __name__ == "__main__":
    main()
