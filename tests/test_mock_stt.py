"""Mock STT 테스트 — Transcript 반환 + STT_COMPLETED 실행기록."""
from __future__ import annotations

from src.tools.mock_stt import MockSttTool


def test_transcribe_returns_transcript(tmp_db):
    from pathlib import Path

    probe = Path(__file__).resolve().parents[1] / "data" / "demo" / "consultation-transcript.txt"
    stt = MockSttTool(tmp_db, transcript_path=probe)
    res = stt.transcribe("sess-stt")
    assert res.event_type == "STT_COMPLETED"
    assert res.success is True
    assert "transcript" in res.extra
    assert len(res.extra["transcript"]) > 100


def test_stt_logged_in_execution(tmp_db):
    from pathlib import Path

    probe = Path(__file__).resolve().parents[1] / "data" / "demo" / "consultation-transcript.txt"
    stt = MockSttTool(tmp_db, transcript_path=probe)
    stt.transcribe("sess-stt2")
    logs = tmp_db.get_executions("sess-stt2")
    assert any(e["event_type"] == "STT_COMPLETED" for e in logs)


def test_stt_idempotent(tmp_db):
    from pathlib import Path

    probe = Path(__file__).resolve().parents[1] / "data" / "demo" / "consultation-transcript.txt"
    stt = MockSttTool(tmp_db, transcript_path=probe)
    r1 = stt.transcribe("sess-stt3")
    r2 = stt.transcribe("sess-stt3")
    assert r1.execution_id == r2.execution_id
    assert r2.extra.get("reused") is True