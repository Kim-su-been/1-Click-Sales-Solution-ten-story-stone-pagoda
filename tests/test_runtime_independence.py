"""Runtime 독립성(Gate 5) — Runtime 코드가 Golden Expected 를 읽지 않고,
결과 결정용 상수(CUST-001/김동양/2026-09-17/특정 #spk)를 하드코딩하지 않았는지
정적 검사한다. (테스트 · scripts/qa 는 예외)
"""
from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

RUNTIME_GLOBS = [
    "agents/**/*.py",
    "src/**/*.py",
    "ui/**/*.py",
    "app.py",
]

FORBIDDEN = [
    "data/expected/",            # Expected JSON을 읽는 경로 참조
    "expected",                   # 예외: tests/scripts 만
    "CUST-001",                   # 결과 결정용 하드코딩 금지
    "김동양",
    "2026-09-17",
]

# Golden Expected의 완성된 결과 문장 (요약/제목) — Runtime 하드코딩 금지
GOLDEN_SNIPPETS = [
    "갱신형 특약 갱신(2026-10-11) 안내를 들은 후",
    "김동양 고객 재상담(기존 계약 보장내용 점검)",
]


def _runtime_files() -> list[Path]:
    files: list[Path] = []
    for glob in RUNTIME_GLOBS:
        files.extend(sorted((ROOT / (glob.split("/")[0])).rglob("*.py")) if glob != "app.py"
                     else [ROOT / "app.py"])
    # 중복 제거 (app.py 별도)
    seen: set[Path] = set()
    out = []
    for f in files:
        if f not in seen:
            seen.add(f)
            out.append(f)
    return out


class TestRuntimeIndependence:
    def test_all_runtime_files_exist(self):
        files = _runtime_files()
        assert len(files) >= 10

    def test_no_expected_json_reference(self):
        bad: list[str] = []
        for f in _runtime_files():
            text = f.read_text(encoding="utf-8")
            if "data/expected/" in text or 'data/expected"' in text or "data/expected']" in text:
                bad.append(str(f))
        assert bad == [], f"Runtime 이 Expected 경로 참조: {bad}"

    def test_no_forbidden_hardcoded_values(self):
        bad: list[str] = []
        for f in _runtime_files():
            if f.name in {"test_runtime_independence.py"}:
                continue
            text = f.read_text(encoding="utf-8")
            for token in ["CUST-001", "김동양", "2026-09-17"]:
                if token in text:
                    bad.append(f"{f}: {token}")
        assert bad == [], f"Runtime 에 하드코딩 값: {bad}"

    def test_no_golden_summary_snippet(self):
        bad: list[str] = []
        for f in _runtime_files():
            text = f.read_text(encoding="utf-8")
            for snippet in GOLDEN_SNIPPETS:
                if snippet in text:
                    bad.append(f"{f}: {snippet[:20]}")
        assert bad == [], f"Runtime 이 Golden 완성 문장 하드코딩: {bad}"

    def test_demo_as_of_date_in_config(self):
        cfg = (ROOT / "src" / "config.py").read_text(encoding="utf-8")
        assert 'DEMO_AS_OF_DATE = "2026-09-09"' in cfg