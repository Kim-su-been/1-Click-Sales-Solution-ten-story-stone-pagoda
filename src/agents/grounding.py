"""Grounding — FC 대본 문장의 Knowledge 근거 연결·판정.

GROUNDING 스텝: 만들어진 FC 대본(script)에서 지식 문서(knowledge/) 근거가 필요한
주장(갱신·보장·보험료)을 찾아 evidenceRef 를 부여하고, grounding_status 를 판정한다.
- SECTION: knowledge md 파싱, 키워드 검색(문자열 기반, LLM 사용 안 함)
- 대본의 문장이 지식 문서 근거(evidenceRef)를 가질 수 있는지 판별
Grounding and Safety Agent 의 일부 로직을 담당한다.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.knowledge_search import (
    KnowledgeSection,
    load_knowledge_index,
    search_sections,
    section_by_ref,
)
from src.runtime_models import (
    Evidence,
    GroundingStatus,
    StepResult,
    WorkflowState,
)

_KB_FILES = [
    "product-guide.md",
    "terms.md",
    "renewal-faq.md",
    "sales-cautions.md",
]


@dataclass
class GroundingItem:
    claim: str
    evidence_ref: str | None
    grounded: bool


@dataclass
class GroundingResult:
    items: list[GroundingItem]
    status: GroundingStatus


def discover_knowledge(knowledge_dir: Path, filenames: list[str] | None = None) -> list[KnowledgeSection]:
    return load_knowledge_index(knowledge_dir, filenames or _KB_FILES)


def _known_claim_keywords() -> list[str]:
    return ["갱신", "보험료", "보장", "계약", "추가 보장", "약관", "심리", "보험금"]


def _is_fc_line(line: str) -> bool:
    """FC 발화 라인 여부 ([FC] 또는 [FC-001] 형식)."""
    stripped = line.strip()
    return stripped.startswith("[FC") and "]" in stripped


def extract_claim_sentences(script_text: str) -> list[str]:
    """대본에서 FC 발화 문장을 추출. (간단 문장 분할: ., ?, ! 기준 join)"""
    sentences: list[str] = []
    for line in script_text.splitlines():
        if not line.strip():
            continue
        speaker, _, body = line.partition("]")
        if not _is_fc_line(line):
            continue
        for part in body.replace("?", ".").replace("!", ".").split("."):
            part = part.strip()
            if part and any(k in part for k in _known_claim_keywords()):
                sentences.append(part)
    return sentences


def run_grounding(
    script_text: str,
    sections: list[KnowledgeSection],
) -> tuple[GroundingResult, StepResult]:
    """대본 문장마다 관련 knowledge 섹션을 찾아 evidenceRef 를 부여.

    grounding_status:
      - 모든 claim 이 근거를 가지면 GROUNDED
      - 근거가 없는 claim 이 하나라도 있으면 MISSING
    """
    items: list[GroundingItem] = []
    for claim in extract_claim_sentences(script_text):
        hits = search_sections(sections, claim, limit=1)
        ref = hits[0].evidence_ref if hits else None
        items.append(GroundingItem(claim=claim, evidence_ref=ref, grounded=ref is not None))

    status = GroundingStatus.GROUNDED if items and all(i.grounded for i in items) else (
        GroundingStatus.MISSING if items else GroundingStatus.MISSING
    )
    evidence = Evidence(
        artifact_type="grounding_report",
        source=WorkflowState.GROUNDING,
        summary=f"grounding_status={status}, claims={len(items)}",
        payload={
            "items": [
                {"claim": i.claim, "evidence_ref": i.evidence_ref} for i in items
            ]
        },
    )
    step = StepResult(
        state=WorkflowState.GROUNDING,
        step_name="grounding",
        summary=(
            f"claims={len(items)}, grounded={sum(1 for i in items if i.grounded)}, "
            f"status={status}"
        ),
        evidence=[evidence],
    )
    return GroundingResult(items=items, status=status), step


def default_grounding(
    script_text: str | None,
    knowledge_dir: Path,
) -> tuple[GroundingResult, StepResult]:
    """실행 편의 함수: knowledge 디렉토리에서 섹션 로드 후 grounding."""
    sections = discover_knowledge(knowledge_dir)
    return run_grounding(script_text or "", sections)