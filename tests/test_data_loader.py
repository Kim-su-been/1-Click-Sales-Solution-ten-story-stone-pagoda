"""Data Loader 테스트 — 로딩·참조·spk 매핑·NFC·Evidence 규약."""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

import pytest

from src.data_loader import DataLoader, DataLoadingError, get_loader


@pytest.fixture(scope="module")
def loader() -> DataLoader:
    return get_loader()


def test_json_files_parse(project_root: Path) -> None:
    json_files = [
        "data/seed/customers.json",
        "data/seed/contracts.json",
        "data/seed/scoring_rules.json",
        "data/expected/daily_pick_expected.json",
        "data/expected/contact-script-expected.json",
        "data/expected/safety-reject-expected.json",
        "data/expected/session-analysis-expected.json",
        "data/expected/crm-record-expected.json",
        "data/expected/next-action-expected.json",
    ]
    for rel in json_files:
        p = project_root / rel
        assert p.exists(), f"missing {rel}"
        json.loads(p.read_text(encoding="utf-8"))


def test_customers_loaded(loader: DataLoader) -> None:
    assert len(loader.customers) == 5, "고객 5명 로딩"
    assert "CUST-001" in loader.customers
    assert loader.customers["CUST-001"].name == "김동양"


def test_contracts_reference_valid(loader: DataLoader) -> None:
    cust_ids = set(loader.customers.keys())
    for c in loader.contracts:
        assert c.customer_id in cust_ids, f"contract {c.contract_id} -> {c.customer_id}"


def test_kim_contracts(loader: DataLoader) -> None:
    kim_contracts = loader.contracts_of("CUST-001")
    ids = {c.contract_id for c in kim_contracts}
    assert "CTR-101" in ids
    assert "CTR-102" in ids
    rider = [c for c in kim_contracts if c.rider_flag][0]
    assert rider.renewal_date == "2026-10-11"


def test_daily_pick_is_kim_90(loader: DataLoader) -> None:
    pick = loader.pick
    assert pick["customer_id"] == "CUST-001"
    assert pick["name"] == "김동양"
    assert pick["rescue_score"] == 90


def test_display_values(loader: DataLoader) -> None:
    cust = loader.get_customer("CUST-001")
    renewal = next(c.renewal_date for c in loader.contracts_of("CUST-001") if c.renewal_date)
    assert loader.days_until(renewal) == 32          # D-32
    assert loader.months_elapsed(cust.last_contacted_at) == 14  # 14개월
    assert loader.months_elapsed(cust.fc_changed_at) == 11      # 11개월


def test_ineligible_excluded_from_pick(loader: DataLoader) -> None:
    pick_id = loader.pick["customer_id"]
    for row in loader.pick_candidate_rows:
        if row["eligibility"] == "INELIGIBLE":
            assert row["customer_id"] != pick_id
            assert row["rescue_score"] is None
            assert row["exclusion_reason"]
    assert pick_id == "CUST-001"
    # Eligibility 조건: 동의 없음(CUST-002)·민원(CUST-003)
    assert loader.customers["CUST-002"].is_eligible is False
    assert loader.customers["CUST-003"].is_eligible is False


def test_transcript_spk_mapping(loader: DataLoader) -> None:
    assert len(loader.transcript) >= 16
    # #spk:6 은 transcript의 6번째 발화 (파일 줄 번호 아님)
    u6 = loader.utter_by_spk(6)
    assert u6 is not None
    assert u6.spk_index == 6
    assert "보장" in u6.text or "보험" in u6.text
    # 모든 expected #spk:N 이 유효 범위여야 함
    max_idx = len(loader.transcript)


def test_spk_refs_in_range(loader: DataLoader) -> None:
    refs = []

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == "evidenceRef" and isinstance(v, str):
                    m = re.search(r"#spk:(\d+)$", v.strip())
                    if m:
                        refs.append(int(m.group(1)))
                else:
                    walk(v)
        elif isinstance(o, list):
            for x in o:
                walk(x)

    for data in [loader.session_analysis, loader.crm_record, loader.next_action]:
        walk(data)
    assert refs, "transcript 참조가 존재해야 함"
    for idx in refs:
        assert 1 <= idx <= len(loader.transcript), f"spk:{idx} out of range"


def test_evidence_text_matches_transcript(loader: DataLoader) -> None:
    """모든 TRANSCRIPT evidenceText 는 transcript 발화 원문과 일치해야 한다."""
    lines = [u.line for u in loader.transcript]
    import re as _re

    def walk(o):
        out = []
        if isinstance(o, dict):
            if "evidenceText" in o and isinstance(o["evidenceText"], str):
                out.append(o["evidenceText"])
            for v in o.values():
                out += walk(v)
        elif isinstance(o, list):
            for x in o:
                out += walk(x)
        return out

    all_ev = []
    for data in [loader.session_analysis, loader.crm_record, loader.next_action]:
        all_ev += walk(data)
    for t in all_ev:
        norm = _re.sub(r"^\[[^\]]+\]\s*", "", t).strip()
        assert any(norm in l for l in lines), f"evidenceText not in transcript: {t[:40]}"


def test_nfc_normalized(loader: DataLoader) -> None:
    texts = [loader.customers["CUST-001"].name, loader.contact_script["customer_name"]]
    for t in texts:
        assert unicodedata.normalize("NFC", t) == t
    # knowledge 본문도 NFC
    for fname, body in loader.knowledge_docs.items():
        assert unicodedata.normalize("NFC", body) == body, f"{fname} not NFC"


def test_no_execution_log_in_expected(loader: DataLoader) -> None:
    for data in [
        loader.contact_script,
        loader.safety_reject,
        loader.session_analysis,
        loader.crm_record,
        loader.next_action,
    ]:
        assert "EXECUTION_LOG" not in json.dumps(data, ensure_ascii=False)


def test_crm_is_draft(loader: DataLoader) -> None:
    crm = loader.crm_record
    assert crm["status"] in ("DRAFT", "PENDING_FC_CONFIRM")
    assert crm["phase"] == "FC_REVIEW"
    assert crm["auto_finalized"] is False
    assert crm["fc_confirm_required"] is True


def test_next_action_due_20260917(loader: DataLoader) -> None:
    na = loader.next_action
    candidate = na["calendar_candidate"]
    assert candidate["due_datetime"].startswith("2026-09-17T")
    hour = int(candidate["due_datetime"][11:13])
    assert 13 <= hour <= 18  # 오후


def test_missing_file_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import src.config as cfg

    monkeypatch.setattr(cfg, "CUSTOMERS_PATH", tmp_path / "nope.json")
    dl = DataLoader()
    with pytest.raises(DataLoadingError):
        dl.load_all()


def test_knowledge_notice(loader: DataLoader) -> None:
    notice = "본 문서는 1-Pick Rescue Agent 해커톤 시연을 위한 가상 자료이며 실제 보험상품의 약관 또는 상품설명서가 아닙니다."
    for fname, body in loader.knowledge_docs.items():
        assert body.splitlines()[0] == notice, f"{fname} 고지문 누락"


@pytest.fixture
def project_root() -> Path:
    from src.config import PROJECT_ROOT

    return PROJECT_ROOT