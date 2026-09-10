"""Transcript 파서 — 전화 상담 대본(전문가가 각색한 시나리오)을 발화 목록으로 파싱.

형식:
  [FC] 안녕하세요, 예금보험 상담센터입니다.
  [회원] 네, 안녕하세요.
  (audio)(long-pause) 등 비발화 메타 태그는 무시한다.

비발화(markup)가 아닌 줄은 발화로 본다. 화자 태그 [FC] / [회원] 을 speaker 로 저장한다.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from src.runtime_models import Turn


SPEAKER_FC = "FC"
SPEAKER_MEMBER = "회원"
_SPEAKER_RE = re.compile(r"^\[([^\]]+)\]\s*(.*)$")


@dataclass
class TranscriptParseResult:
    turns: list[Turn]
    non_speech: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def parse_transcript(text: str) -> TranscriptParseResult:
    turns: list[Turn] = []
    non_speech: list[str] = []
    warnings: list[str] = []

    lines = (text or "").splitlines()
    for idx, raw in enumerate(lines):
        line = raw.strip()
        if not line:
            continue
        # 비발화 메타(실제 음성 발화로 보지 않는 태그)
        if line.startswith("(") and line.endswith(")"):
            non_speech.append(line)
            continue

        m = _SPEAKER_RE.match(line)
        if not m:
            # 화자 태그가 없는 줄은 직전 화자에 이어 붙인다(추가 발화 연속).
            if turns:
                turns[-1].text += "\n" + line
            else:
                warnings.append(f"line {idx + 1}: 화자 태그가 없는 줄 무시 — {line[:40]}")
            continue

        speaker = m.group(1).strip()
        text = m.group(2).strip()
        if speaker not in {SPEAKER_FC, SPEAKER_MEMBER}:
            warnings.append(f"line {idx + 1}: 알 수 없는 화자 {speaker!r} — [회원]으로 취급")
            speaker = SPEAKER_MEMBER
        turns.append(Turn(speaker=speaker, text=text, seq=len(turns)))

    return TranscriptParseResult(turns=turns, non_speech=non_speech, warnings=warnings)


def turns_to_text(turns: list[Turn]) -> str:
    return "\n".join(f"[{t.speaker}] {t.text}" for t in turns)