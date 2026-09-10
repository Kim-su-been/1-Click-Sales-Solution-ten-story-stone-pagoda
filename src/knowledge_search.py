"""Knowledge 문서 파싱·검색 — Markdown 을 section 단위로 분해하고 키워드/규칙 기반 검색.

Vector DB·LLM 을 사용하지 않는다.
document_id(data/knowledge/<file>)와 section_id(앵커 {#...})를 보존해
evidenceRef: data/knowledge/<file>#<section> 를 생성한다.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path


def nfc(s: str) -> str:
    """Unicode NFC 정규화."""
    return unicodedata.normalize("NFC", s) if s else s


@dataclass
class KnowledgeSection:
    document_id: str          # data/knowledge/product-guide.md
    section_id: str           # ts2001-renewal
    heading: str
    body: str                 # 섹션 본문(원문, NFC)
    evidence_ref: str         # data/knowledge/product-guide.md#ts2001-renewal

    def text(self) -> str:
        return f"{self.heading}\n{self.body}"


ANCHOR_RE = re.compile(r"\{#([A-Za-z0-9_\-]+)\}")
HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*(?:\{#([A-Za-z0-9_\-]+)\})?$")


def parse_markdown_sections(file_path: Path) -> list[KnowledgeSection]:
    """md 파일을 섹션 단위로 파싱. 앵커가 있는 heading 을 section 시작점으로 사용.

    앵커가 없는 문단은 직전 섹션의 body 로 합친다.
    """
    raw = file_path.read_text(encoding="utf-8")
    raw = nfc(raw)
    document_id = f"data/knowledge/{file_path.name}"

    # 헤더 분해: (heading_text, anchor, start_line)
    lines = raw.splitlines()
    anchors: list[tuple[str, str | None, int]] = []
    for idx, line in enumerate(lines):
        m = re.match(r"^(#{1,6})\s+(.+?)\s*$", line.strip())
        if not m:
            continue
        # 인라인 {#anchor} 추출
        body = m.group(2)
        a = ANCHOR_RE.search(body)
        anchor = a.group(1) if a else None
        text = ANCHOR_RE.sub("", body).strip()
        anchors.append((text, anchor, idx))

    sections: list[KnowledgeSection] = []
    for i, (heading, anchor, start) in enumerate(anchors):
        end = anchors[i + 1][2] if i + 1 < len(anchors) else len(lines)
        body_lines = lines[start + 1:end]
        body = "\n".join(l for l in body_lines if l.strip())
        if not anchor:
            # 앵커 없는 heading → 직전 섹션에 흡수(연속 문단)
            if sections:
                sections[-1].body += "\n" + body
            continue
        sections.append(KnowledgeSection(
            document_id=document_id,
            section_id=anchor,
            heading=heading,
            body=body,
            evidence_ref=f"{document_id}#{anchor}",
        ))
    return sections


def load_knowledge_index(knowledge_dir: Path, filenames: list[str]) -> list[KnowledgeSection]:
    sections: list[KnowledgeSection] = []
    for name in filenames:
        p = knowledge_dir / name
        if p.exists():
            sections.extend(parse_markdown_sections(p))
    return sections


_KEYWORD_GROUPS: dict[str, list[str]] = {
    "renewal": ["갱신", "renewal", "갱신 예정", "보험료 재산정", "사전 안내"],
    "coverage": ["보장", "보장 내용", "입원", "지급", "보험금"],
    "premium": ["보험료", "재산정", "변동"],
    "safety": ["금지", "주의", "위협", "과장", "근거"],
    "notice": ["안내", "가이드", "설명서"],
}


def search_sections(
    sections: list[KnowledgeSection],
    query: str,
    limit: int = 5,
) -> list[KnowledgeSection]:
    """쿼리와 관련된 section 을 키워드 출현 수 기준으로 반환 (정렬, 최대 limit)."""
    q = nfc(query.lower())
    scored: list[tuple[int, KnowledgeSection]] = []
    for sec in sections:
        hay = nfc((sec.heading + " " + sec.body).lower())
        score = 0
        for keyword in _KEYWORD_GROUPS.get("renewal", []):
            if keyword.lower() in hay:
                score += 2
        for keyword in _KEYWORD_GROUPS.get("premium", []):
            if keyword.lower() in hay:
                score += 1
        for tk in re.findall(r"[가-힣A-Za-z0-9]+", q):
            if tk and tk in hay:
                score += 1
        if score > 0:
            scored.append((score, sec))
    scored.sort(key=lambda x: (-x[0], x[1].evidence_ref))
    return [s for _, s in scored[:limit]]


def section_by_ref(sections: list[KnowledgeSection], evidence_ref: str) -> KnowledgeSection | None:
    for s in sections:
        if s.evidence_ref == nfc(evidence_ref):
            return s
    return None