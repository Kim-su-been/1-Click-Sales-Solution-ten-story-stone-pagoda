"""Mock STT Tool — 실제 음성 인식 대신 data/demo/consultation-transcript.txt 를 반환.

출력에 STT_COMPLETED 실행기록을 포함한다.
"""
from __future__ import annotations

from pathlib import Path

from src.runtime_db import RuntimeDB
from src.tools.interfaces import STT_COMPLETED, SttTool, ToolExecutionResult

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TRANSCRIPT_PATH = PROJECT_ROOT / "data" / "demo" / "consultation-transcript.txt"


class MockSttTool(SttTool):
    """STT Mock Adapter."""

    def __init__(self, db: RuntimeDB | None = None, transcript_path: Path | None = None) -> None:
        self.db = db or RuntimeDB()
        self.transcript_path = transcript_path or TRANSCRIPT_PATH

    def transcribe(self, session_id: str) -> ToolExecutionResult:
        if not self.transcript_path.exists():
            raise FileNotFoundError(f"Transcript 없음: {self.transcript_path}")
        text = self.transcript_path.read_text(encoding="utf-8")
        record = self.db.record_execution(
            session_id, "stt", STT_COMPLETED, True,
            result_ref=str(self.transcript_path),
        )
        return ToolExecutionResult(
            execution_id=record["execution_id"],
            session_id=session_id,
            tool_name="stt",
            event_type=STT_COMPLETED,
            success=True,
            executed_at=record["executed_at"],
            result_ref=record["result_ref"],
            extra={
                "transcript": text,
                "transcript_path": str(self.transcript_path),
                "chars": len(text),
                "reused": record.get("reused", False),
            },
        )