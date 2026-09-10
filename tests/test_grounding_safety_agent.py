"""Gate 2: Grounding and Safety Agent 테스트.

- Contact Reason 생성 (RENEWAL_PRENOTICE · D-32)
- 전화·문자·카카오톡 초안 생성
- KNOWLEDGE_DOCUMENT 근거 연결 (실제 Knowledge 앵커)
- 근거 없는 스크립트 차단 (safety-reject 시나리오)
- 기존 Safety 상태 계약 준수 (COMPLIANT/REJECTED)
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.data_loader import DataLoader
from src.safety_rules import build_rule_table, check_safety
from src.agents.grounding_safety import run_grounding_safety

ROOT = Path(__file__).resolve().parents[1]
KB = ROOT / "data" / "knowledge"


@pytest.fixture(scope="module")
def loader():
    return DataLoader().load_all()


@pytest.fixture(scope="module")
def safety_rules():
    raw = json.loads((ROOT / "config" / "safety_rules.json").read_text(encoding="utf-8"))
    return raw["safety_rules"]


class TestGroundingSafetyAgent:
    def test_contact_reason_renewal_prenotice(self, loader, safety_rules):
        cust = loader.customers["CUST-001"]
        out = run_grounding_safety(cust, loader.contracts_of("CUST-001"), KB, safety_rules)
        assert out.contact_reason["code"] == "RENEWAL_PRENOTICE"
        assert "D-32" in out.contact_reason["text"]

    def test_three_channel_scripts(self, loader, safety_rules):
        cust = loader.customers["CUST-001"]
        out = run_grounding_safety(cust, loader.contracts_of("CUST-001"), KB, safety_rules)
        assert set(out.scripts.keys()) == {"CALL_FIRST_OPENING", "SMS", "KAKAO"}
        for ch in out.scripts.values():
            assert ch["text"]
            assert ch["sentence_evidence"]

    def test_knowledge_document_evidence_and_real_anchor(self, loader, safety_rules):
        cust = loader.customers["CUST-001"]
        out = run_grounding_safety(cust, loader.contracts_of("CUST-001"), KB, safety_rules)
        for ch in out.scripts.values():
            for se in ch["sentence_evidence"]:
                assert se["evidenceType"] == "KNOWLEDGE_DOCUMENT"
                assert se["evidenceRef"].startswith("data/knowledge/")
                # 실제 문서 앵커 존재 확인
                self._assert_anchor_exists(se["evidenceRef"])

    @staticmethod
    def _assert_anchor_exists(ref: str) -> None:
        fname, _, anchor = ref.replace("data/knowledge/", "").partition("#")
        text = (KB / fname).read_text(encoding="utf-8")
        assert "{#" + anchor + "}" in text, f"앵커 없음: {ref}"

    def test_safety_reject_blocks_ungrounded(self, safety_rules):
        rejected = (
            "지금 바꾸지 않으면 보장이 크게 줄어듭니다. "
            "이 상품은 보험료가 절대 오르지 않습니다. "
            "세상에서 가장 좋은 보장입니다."
        )
        result = check_safety(rejected, build_rule_table(safety_rules), [])
        assert result.decision == "REJECTED"
        assert len(result.violations) == 3

    def test_final_scripts_are_compliant(self, loader, safety_rules):
        cust = loader.customers["CUST-001"]
        out = run_grounding_safety(cust, loader.contracts_of("CUST-001"), KB, safety_rules)
        assert out.safety_review.decision == "COMPLIANT"
        assert out.safety_review.violations == []

    def test_matches_contact_script_expected_structure(self, loader, safety_rules):
        cust = loader.customers["CUST-001"]
        out = run_grounding_safety(cust, loader.contracts_of("CUST-001"), KB, safety_rules)
        # contact-script-expected 의 grounding_docs 와 구조 비교(값이 아닌 키)
        assert "code" in out.contact_reason
        assert "text" in out.contact_reason
        assert "pick_basis" in out.contact_reason
        assert out.contact_reason["code"] == "RENEWAL_PRENOTICE"