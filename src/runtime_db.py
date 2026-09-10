"""SQLite 기반 Mock Runtime 저장소.

데모 반복 실행을 위해 Demo session 단위로 실행 데이터(execution_logs·contact_attempts·
crm_records·calendar_events·feedback_events)를 저장한다.

- 고객 Seed·Knowledge 문서는 SQLite 로 이전하지 않는다 (기존 JSON/Markdown 사용).
- data/runtime/demo.db 는 Runtime 생성 파일이다 (.gitignore 에 추가 권장).
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "runtime" / "demo.db"


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_id(prefix: str, session_id: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:6]}-{session_id[-6:]}"


class RuntimeDB:
    """Tool 실행 결과를 저장하고 중복 실행을 방지한다."""

    def __init__(self, db_path: Path | str | None = None) -> None:
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._create_schema()

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------
    def _create_schema(self) -> None:
        with self._conn:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS execution_logs (
                    execution_id TEXT PRIMARY KEY,
                    session_id   TEXT NOT NULL,
                    tool_name    TEXT NOT NULL,
                    event_type   TEXT NOT NULL,
                    success      INTEGER NOT NULL,
                    executed_at  TEXT NOT NULL,
                    result_ref   TEXT,
                    error_code   TEXT,
                    error_message TEXT,
                    UNIQUE (session_id, event_type)
                )
                """
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS contact_attempts (
                    attempt_id  TEXT PRIMARY KEY,
                    session_id  TEXT NOT NULL,
                    customer_id TEXT NOT NULL,
                    channel     TEXT NOT NULL,
                    event_type  TEXT NOT NULL,
                    script_text TEXT,
                    success     INTEGER NOT NULL,
                    executed_at TEXT NOT NULL,
                    UNIQUE (session_id, event_type)
                )
                """
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS crm_records (
                    record_id   TEXT PRIMARY KEY,
                    session_id  TEXT NOT NULL,
                    customer_id TEXT NOT NULL,
                    status      TEXT NOT NULL,
                    phase       TEXT NOT NULL,
                    payload     TEXT NOT NULL,
                    created_at  TEXT NOT NULL,
                    UNIQUE (session_id)
                )
                """
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS calendar_events (
                    event_id    TEXT PRIMARY KEY,
                    session_id  TEXT NOT NULL,
                    customer_id TEXT NOT NULL,
                    title       TEXT,
                    due_datetime TEXT,
                    status      TEXT NOT NULL,
                    created_at  TEXT NOT NULL,
                    UNIQUE (session_id)
                )
                """
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS feedback_events (
                    event_id   TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    fc_action  TEXT NOT NULL,
                    original_draft TEXT,
                    revised_draft  TEXT,
                    safety_result  TEXT,
                    final_execution TEXT,
                    stored_at  TEXT NOT NULL,
                    UNIQUE (session_id)
                )
                """
            )

    def close(self) -> None:
        self._conn.close()

    # ------------------------------------------------------------------
    # Idempotency helpers
    # ------------------------------------------------------------------
    def _find_execution(self, session_id: str, event_type: str) -> sqlite3.Row | None:
        cur = self._conn.execute(
            "SELECT * FROM execution_logs WHERE session_id=? AND event_type=?",
            (session_id, event_type),
        )
        return cur.fetchone()

    def _insert_execution(
        self,
        execution_id: str,
        session_id: str,
        tool_name: str,
        event_type: str,
        success: bool,
        executed_at: str,
        result_ref: str | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> None:
        with self._conn:
            self._conn.execute(
                """
                INSERT OR REPLACE INTO execution_logs
                (execution_id, session_id, tool_name, event_type, success,
                 executed_at, result_ref, error_code, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (execution_id, session_id, tool_name, event_type, int(success),
                 executed_at, result_ref, error_code, error_message),
            )

    # ------------------------------------------------------------------
    # Execution log (generic)
    # ------------------------------------------------------------------
    def record_execution(
        self,
        session_id: str,
        tool_name: str,
        event_type: str,
        success: bool,
        result_ref: str | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
        executed_at: str | None = None,
    ) -> dict[str, Any]:
        """동일 (session_id, event_type) 이 이미 있으면 기존 결과를 돌려주고 새로 저장하지 않는다."""
        existing = self._find_execution(session_id, event_type)
        if existing is not None:
            return {
                "execution_id": existing["execution_id"],
                "session_id": session_id,
                "tool_name": existing["tool_name"],
                "event_type": event_type,
                "success": bool(existing["success"]),
                "executed_at": existing["executed_at"],
                "result_ref": existing["result_ref"],
                "error_code": existing["error_code"],
                "error_message": existing["error_message"],
                "reused": True,
            }
        execution_id = new_id("exec", session_id)
        executed_at = executed_at or utcnow_iso()
        self._insert_execution(
            execution_id, session_id, tool_name, event_type, success,
            executed_at, result_ref, error_code, error_message,
        )
        return {
            "execution_id": execution_id,
            "session_id": session_id,
            "tool_name": tool_name,
            "event_type": event_type,
            "success": success,
            "executed_at": executed_at,
            "result_ref": result_ref,
            "error_code": error_code,
            "error_message": error_message,
            "reused": False,
        }

    # ------------------------------------------------------------------
    # Domain records
    # ------------------------------------------------------------------
    def save_contact_attempt(
        self,
        session_id: str,
        customer_id: str,
        channel: str,
        event_type: str,
        script_text: str,
        executed_at: str | None = None,
    ) -> dict[str, Any]:
        existing = self._conn.execute(
            "SELECT * FROM contact_attempts WHERE session_id=? AND event_type=?",
            (session_id, event_type),
        ).fetchone()
        executed_at = executed_at or utcnow_iso()
        if existing is not None:
            return {
                "attempt_id": existing["attempt_id"],
                "channel": existing["channel"],
                "script_text": existing["script_text"],
                "reused": True,
            }
        attempt_id = new_id("attempt", session_id)
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO contact_attempts
                (attempt_id, session_id, customer_id, channel, event_type, script_text, success, executed_at)
                VALUES (?, ?, ?, ?, ?, ?, 1, ?)
                """,
                (attempt_id, session_id, customer_id, channel, event_type, script_text, executed_at),
            )
        return {"attempt_id": attempt_id, "channel": channel, "script_text": script_text, "reused": False}

    def save_crm_record(
        self,
        session_id: str,
        customer_id: str,
        status: str,
        phase: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        existing = self._conn.execute(
            "SELECT * FROM crm_records WHERE session_id=?", (session_id,)
        ).fetchone()
        if existing is not None:
            return {"record_id": existing["record_id"], "reused": True}
        record_id = new_id("rec-crm", session_id)
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO crm_records (record_id, session_id, customer_id, status, phase, payload, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (record_id, session_id, customer_id, status, phase,
                 json.dumps(payload, ensure_ascii=False), utcnow_iso()),
            )
        return {"record_id": record_id, "reused": False}

    def save_calendar_event(
        self,
        session_id: str,
        customer_id: str,
        title: str,
        due_datetime: str,
        status: str,
    ) -> dict[str, Any]:
        existing = self._conn.execute(
            "SELECT * FROM calendar_events WHERE session_id=?", (session_id,)
        ).fetchone()
        if existing is not None:
            return {"event_id": existing["event_id"], "reused": True}
        event_id = new_id("cal", session_id)
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO calendar_events (event_id, session_id, customer_id, title, due_datetime, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (event_id, session_id, customer_id, title, due_datetime, status, utcnow_iso()),
            )
        return {"event_id": event_id, "reused": False}

    def save_feedback(
        self,
        session_id: str,
        fc_action: str,
        original_draft: dict[str, Any] | None,
        revised_draft: dict[str, Any] | None,
        safety_result: dict[str, Any] | None,
        final_execution: dict[str, Any] | None,
    ) -> dict[str, Any]:
        existing = self._conn.execute(
            "SELECT * FROM feedback_events WHERE session_id=?", (session_id,)
        ).fetchone()
        if existing is not None:
            return {"event_id": existing["event_id"], "reused": True}
        event_id = new_id("fb", session_id)
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO feedback_events
                (event_id, session_id, fc_action, original_draft, revised_draft, safety_result, final_execution, stored_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (event_id, session_id, fc_action,
                 json.dumps(original_draft, ensure_ascii=False) if original_draft else None,
                 json.dumps(revised_draft, ensure_ascii=False) if revised_draft else None,
                 json.dumps(safety_result, ensure_ascii=False) if safety_result else None,
                 json.dumps(final_execution, ensure_ascii=False) if final_execution else None,
                 utcnow_iso()),
            )
        return {"event_id": event_id, "reused": False}

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------
    def get_executions(self, session_id: str) -> list[dict[str, Any]]:
        cur = self._conn.execute(
            "SELECT * FROM execution_logs WHERE session_id=? ORDER BY executed_at", (session_id,)
        )
        rows = [dict(r) for r in cur.fetchall()]
        for r in rows:
            r["success"] = bool(r["success"])
        return rows

    def get_contact_attempts(self, session_id: str) -> list[dict[str, Any]]:
        cur = self._conn.execute(
            "SELECT * FROM contact_attempts WHERE session_id=? ORDER BY executed_at", (session_id,)
        )
        return [dict(r) for r in cur.fetchall()]

    def get_crm_record(self, session_id: str) -> dict[str, Any] | None:
        cur = self._conn.execute(
            "SELECT * FROM crm_records WHERE session_id=?", (session_id,)
        )
        row = cur.fetchone()
        if row is None:
            return None
        d = dict(row)
        d["payload"] = json.loads(d["payload"]) if d.get("payload") else {}
        return d

    def get_calendar_event(self, session_id: str) -> dict[str, Any] | None:
        cur = self._conn.execute(
            "SELECT * FROM calendar_events WHERE session_id=?", (session_id,)
        )
        row = cur.fetchone()
        return dict(row) if row else None

    def get_feedback(self, session_id: str) -> dict[str, Any] | None:
        cur = self._conn.execute(
            "SELECT * FROM feedback_events WHERE session_id=?", (session_id,)
        )
        row = cur.fetchone()
        if row is None:
            return None
        d = dict(row)
        for k in ("original_draft", "revised_draft", "safety_result", "final_execution"):
            if d.get(k):
                try:
                    d[k] = json.loads(d[k])
                except (TypeError, json.JSONDecodeError):
                    pass
        return d

    # ------------------------------------------------------------------
    # Demo reset (session 단위)
    # ------------------------------------------------------------------
    def reset_session(self, session_id: str) -> None:
        """현재 session_id 의 Runtime 데이터만 삭제한다 (DB 파일은 유지)."""
        with self._conn:
            for table in ("execution_logs", "contact_attempts", "crm_records",
                          "calendar_events", "feedback_events"):
                self._conn.execute(f"DELETE FROM {table} WHERE session_id=?", (session_id,))