"""공통 테스트 픽스처 — 임시 RuntimeDB 를 생성해 Tool 테스트 간 격리한다."""
from __future__ import annotations

import pytest


@pytest.fixture()
def tmp_db(tmp_path):
    from src.runtime_db import RuntimeDB

    db = RuntimeDB(tmp_path / "demo.db")
    yield db
    db.close()


@pytest.fixture()
def safety_rules():
    import json
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "config" / "safety_rules.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    return raw["safety_rules"]


# --- 대표 스크립트 ---
COMPLIANT_SCRIPT = (
    "갱신 예정일이 다가와 갱신 조건을 미리 안내드립니다. "
    "갱신 시 보험료가 재산정될 수 있습니다."
)
REJECTED_SCRIPT = (
    "지금 바꾸지 않으면 보장이 크게 줄어듭니다. "
    "이 상품은 보험료가 절대 오르지 않습니다. "
    "세상에서 가장 좋은 보장입니다."
)