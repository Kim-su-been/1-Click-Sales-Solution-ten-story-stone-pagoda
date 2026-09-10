"""1-Pick Rescue Agent — Data Loader.

모든 화면/테스트가 파일 경로와 JSON 내부 구조를 직접 다루지 않도록,
시드·Expected·Knowledge·Transcript 를 로딩하고 검증하는 단일 진입점.
이 모듈은 '준비된 Expected 결과'를 그대로 제공한다 (Runtime Product Agent 결과로 교체 가능).

검증 포함:
- 파일 누락 / JSON 문법 오류 → 이해 가능한 예외
- customer_id ↔ contract_id 참조 무결성
- evidenceRef 기본 형식 (NFC 정규화, 허용 evidenceType)
- Transcript `#spk:N` 을 실제 발화(1-based 순서)와 연결

날짜 계산은 DEMO_AS_OF_DATE(2026-09-09) 기준이며 시스템 현재 날짜를 사용하지 않는다.
"""
from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

import src.config as cfg

# 현재 Expected 근거로 허용하는 evidenceType (EXECUTION_LOG 는 런타임 계약에만 정의)
ALLOWED_EVIDENCE_TYPES = {"CUSTOMER_DATA", "KNOWLEDGE_DOCUMENT", "TRANSCRIPT"}

# transcript 발화 라인 정규식: [화자] 발화
_SPK_LINE_RE = re.compile(r"^\[(?P<spk>[^\]]+)\]\s*(?P<text>.+)$")


class DataLoadingError(Exception):
    """데이터 로딩 · 검증 실패 시 사용자(FC/개발자)가 이해할 수 있는 오류."""


def _nfc(*values: str) -> str:
    """문자열을 Unicode NFC 로 정규화한다."""
    return unicodedata.normalize("NFC", values[0])


def _read_text(path: Path, label: str) -> str:
    if not path.exists():
        raise DataLoadingError(f"{label} 파일을 찾을 수 없습니다: {path.name} ({path})")
    try:
        return path.read_text(encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        raise DataLoadingError(f"{label} 파일을 읽지 못했습니다: {path.name} — {exc}") from exc


def _read_json(path: Path, label: str) -> Any:
    if not path.exists():
        raise DataLoadingError(f"{label} 파일을 찾을 수 없습니다: {path.name} ({path})")
    try:
        return json.loads(_read_text(path, label))
    except json.JSONDecodeError as exc:
        raise DataLoadingError(
            f"{label} JSON 문법 오류: {path.name} — {exc.msg} (라인 {exc.lineno}, 컬럼 {exc.colno})"
        ) from exc


# ---------------------------------------------------------------------------
# 시드 데이터
# ---------------------------------------------------------------------------
@dataclass
class Customer:
    customer_id: str
    name: str
    birth_year: int | None
    sex: str
    phone: str
    consent_channels: list[str]
    active_complaint: bool
    complaint_detail: str | None
    fc_id: str
    previous_fc_id: str | None
    fc_changed_at: str | None
    last_contacted_at: str | None
    last_consultation_at: str | None
    memo: str = ""
    raw: dict = field(default_factory=dict)

    @property
    def is_eligible(self) -> bool:
        """Eligibility: 연락 동의 존재 + 진행 중 민원 없음."""
        return bool(self.consent_channels) and not self.active_complaint

    @property
    def exclusion_reason(self) -> str | None:
        if not self.consent_channels:
            return "CONTACT_CONSENT_NONE"
        if self.active_complaint:
            return "ACTIVE_COMPLAINT"
        return None


@dataclass
class Contract:
    contract_id: str
    customer_id: str
    product_code: str
    product_name: str
    contract_type: str
    status: str
    monthly_premium: int
    premium_status: str
    started_at: str | None
    renewal_date: str | None
    maturity_date: str | None
    rider_flag: bool
    raw: dict = field(default_factory=dict)


@dataclass
class ScoringRule:
    rule_id: str
    name_kr: str
    condition: str
    points: int
    category: str
    exclusive_with: str | None = None
    raw: dict = field(default_factory=dict)


@dataclass
class EligibilityRule:
    rule_id: str
    name_kr: str
    condition: str
    exclusion_reason: str
    raw: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Transcript
# ---------------------------------------------------------------------------
@dataclass
class Utterance:
    spk_index: int          # 1부터 시작하는 발화 순서 (#spk:N 과 일치)
    speaker: str
    text: str

    @property
    def line(self) -> str:
        return f"[{self.speaker}] {self.text}"


# ---------------------------------------------------------------------------
# DataLoader
# ---------------------------------------------------------------------------
class DataLoader:
    """시드·Expected·Knowledge·Transcript 의 단일 로딩 진입점."""

    def __init__(self) -> None:
        self.customers: dict[str, Customer] = {}
        self.contracts: list[Contract] = []
        self.scoring_rules: list[ScoringRule] = []
        self.eligibility_rules: list[EligibilityRule] = []
        self.daily_pick: dict[str, Any] = {}
        self.contact_script: dict[str, Any] = {}
        self.safety_reject: dict[str, Any] = {}
        self.session_analysis: dict[str, Any] = {}
        self.crm_record: dict[str, Any] = {}
        self.next_action: dict[str, Any] = {}
        self.knowledge_docs: dict[str, str] = {}
        self.transcript: list[Utterance] = []
        self.transcript_raw: str = ""
        self.demo_as_of_date: str = cfg.DEMO_AS_OF_DATE

    # ---------------- 로딩 ----------------
    def load_all(self) -> "DataLoader":
        self._load_seed()
        self._load_expected()
        self._load_knowledge()
        self._load_transcript()
        self._validate_refs()
        return self

    def _load_seed(self) -> None:
        """시드: customers / contracts / scoring_rules."""
        customers_data = _read_json(cfg.CUSTOMERS_PATH, "고객")
        contracts_data = _read_json(cfg.CONTRACTS_PATH, "계약")
        rules_data = _read_json(cfg.SCORING_RULES_PATH, "스코어 규칙")

        self.demo_as_of_date = self._check_date(customers_data, "customers.json")
        self._check_date(contracts_data, "contracts.json")
        self._check_date(rules_data, "scoring_rules.json")

        self.customers = {}
        for item in customers_data["customers"]:
            item = self._norm_dict(item, "customers.json")
            cust = Customer(
                customer_id=_nfc(item["customer_id"]),
                name=_nfc(item["name"]),
                birth_year=item.get("birth_year"),
                sex=item.get("sex", ""),
                phone=_nfc(item.get("phone", "")),
                consent_channels=list(item.get("consent_channels", [])),
                active_complaint=bool(item.get("active_complaint", False)),
                complaint_detail=_nfc(item.get("complaint_detail")) if item.get("complaint_detail") else None,
                fc_id=_nfc(item.get("fc_id", "")),
                previous_fc_id=_nfc(item["previous_fc_id"]) if item.get("previous_fc_id") else None,
                fc_changed_at=_nfc(item["fc_changed_at"]) if item.get("fc_changed_at") else None,
                last_contacted_at=_nfc(item["last_contacted_at"]) if item.get("last_contacted_at") else None,
                last_consultation_at=_nfc(item["last_consultation_at"]) if item.get("last_consultation_at") else None,
                memo=_nfc(item.get("memo", "")),
                raw=item,
            )
            self.customers[cust.customer_id] = cust

        self.contracts = []
        for item in contracts_data["contracts"]:
            item = self._norm_dict(item, "contracts.json")
            self.contracts.append(
                Contract(
                    contract_id=_nfc(item["contract_id"]),
                    customer_id=_nfc(item["customer_id"]),
                    product_code=_nfc(item.get("product_code", "")),
                    product_name=_nfc(item.get("product_name", "")),
                    contract_type=_nfc(item.get("contract_type", "")),
                    status=_nfc(item.get("status", "")),
                    monthly_premium=int(item.get("monthly_premium", 0) or 0),
                    premium_status=_nfc(item.get("premium_status", "")),
                    started_at=_nfc(item["started_at"]) if item.get("started_at") else None,
                    renewal_date=_nfc(item["renewal_date"]) if item.get("renewal_date") else None,
                    maturity_date=_nfc(item["maturity_date"]) if item.get("maturity_date") else None,
                    rider_flag=bool(item.get("rider_flag", False)),
                    raw=item,
                )
            )

        self.eligibility_rules = [
            EligibilityRule(
                rule_id=_nfc(r["rule_id"]),
                name_kr=_nfc(r.get("name_kr", "")),
                condition=_nfc(r.get("condition", "")),
                exclusion_reason=_nfc(r.get("exclusion_reason", "")),
                raw=r,
            )
            for r in rules_data.get("eligibility", [])
        ]
        self.scoring_rules = [
            ScoringRule(
                rule_id=_nfc(r["rule_id"]),
                name_kr=_nfc(r.get("name_kr", "")),
                condition=_nfc(r.get("condition", "")),
                points=int(r.get("points", 0) or 0),
                category=_nfc(r.get("category", "")),
                exclusive_with=_nfc(r["exclusive_with"]) if r.get("exclusive_with") else None,
                raw=r,
            )
            for r in rules_data.get("score_rules", [])
        ]

    def _load_expected(self) -> None:
        """Expected: daily_pick / contact-script / safety-reject / session / crm / next-action."""
        self.daily_pick = _read_json(cfg.DAILY_PICK_EXPECTED_PATH, "1-Pick Expected")
        self.contact_script = _read_json(cfg.CONTACT_SCRIPT_EXPECTED_PATH, "Contact Script Expected")
        self.safety_reject = _read_json(cfg.SAFETY_REJECT_EXPECTED_PATH, "Safety Reject Expected")
        self.session_analysis = _read_json(cfg.SESSION_ANALYSIS_EXPECTED_PATH, "상담 분석 Expected")
        self.crm_record = _read_json(cfg.CRM_RECORD_EXPECTED_PATH, "CRM Expected")
        self.next_action = _read_json(cfg.NEXT_ACTION_EXPECTED_PATH, "Next Action Expected")
        self._check_date(self.daily_pick, "daily_pick_expected.json")

    def _load_knowledge(self) -> None:
        """Knowledge: .md 본문 (고지문 첫 줄 포함) 을 그대로 보관."""
        for fname in cfg.KNOWLEDGE_FILES:
            path = cfg.KNOWLEDGE_DIR / fname
            if not path.exists():
                raise DataLoadingError(f"Knowledge 문서를 찾을 수 없습니다: {fname} ({path})")
            text = _read_text(path, f"Knowledge {fname}")
            self.knowledge_docs[fname] = _nfc(text)

    def _load_transcript(self) -> None:
        """Transcript: `[화자] 발화` 라인을 파싱해 1-based 발화 순서를 부여한다."""
        text = _read_text(cfg.TRANSCRIPT_PATH, "상담 Transcript")
        self.transcript_raw = text
        utterances: list[Utterance] = []
        for line in text.splitlines():
            m = _SPK_LINE_RE.match(line.strip())
            if not m:
                continue  # 주석/빈 줄 무시
            utterances.append(
                Utterance(
                    spk_index=len(utterances) + 1,
                    speaker=_nfc(m.group("spk")),
                    text=_nfc(m.group("text")),
                )
            )
        if not utterances:
            raise DataLoadingError(
                "상담 Transcript 에 발화가 없습니다. `[화자] 발화` 형식의 라인이 필요합니다."
            )
        self.transcript = utterances

    def _check_date(self, data: Any, label: str) -> str:
        val = data.get("demo_as_of_date")
        if val != cfg.DEMO_AS_OF_DATE:
            raise DataLoadingError(
                f"{label} 의 demo_as_of_date 가 {cfg.DEMO_AS_OF_DATE} 가 아닙니다: {val!r}"
            )
        return _nfc(val)

    @staticmethod
    def _norm_dict(item: Any, label: str) -> dict[str, Any]:
        if not isinstance(item, dict):
            raise DataLoadingError(f"{label} 항목이 JSON 객체가 아닙니다: {item!r}")
        out = {}
        for k, v in item.items():
            if isinstance(v, str):
                v = unicodedata.normalize("NFC", v)
            out[k] = v
        return out

    # ---------------- 검증 ----------------
    def _validate_refs(self) -> None:
        # 1) 계약 → 고객 참조
        cust_ids = set(self.customers.keys())
        bad = [c.contract_id for c in self.contracts if c.customer_id not in cust_ids]
        if bad:
            raise DataLoadingError(
                f"계약이 존재하지 않는 고객을 참조합니다: {bad}. contracts.json 의 customer_id 를 확인하세요."
            )

        # 2) Expected evidenceRef/evidenceType 기본 형식
        problems: list[str] = []
        for label, data in [
            ("contact-script", self.contact_script),
            ("safety-reject", self.safety_reject),
            ("session-analysis", self.session_analysis),
            ("crm-record", self.crm_record),
            ("next-action", self.next_action),
        ]:
            problems += self._check_evidence(data, label)
        if problems:
            raise DataLoadingError("Evidence 형식 문제가 감지되었습니다:\n  " + "\n  ".join(problems))

        # 3) Transcript 발화에 대한 evidenceRef #spk:N 유효성
        spk_problems = self._check_spk_refs(self.session_analysis, "session-analysis")
        spk_problems += self._check_spk_refs(self.crm_record, "crm-record")
        spk_problems += self._check_spk_refs(self.next_action, "next-action")
        if spk_problems:
            raise DataLoadingError("Transcript 발화 참조(#spk:N) 문제:\n  " + "\n  ".join(spk_problems))

    def _check_evidence(self, data: Any, label: str, _path: str = "") -> list[str]:
        problems: list[str] = []
        if isinstance(data, dict):
            for k, v in data.items():
                if k == "evidenceType" and v not in ALLOWED_EVIDENCE_TYPES:
                    problems.append(f"{label}: 허용되지 않은 evidenceType={v!r} (경로 {_path or 'top'})")
                if k == "evidenceRef" and isinstance(v, str):
                    v = unicodedata.normalize("NFC", v)
                    if not (v.startswith("data/seed/") or v.startswith("data/knowledge/")
                            or v.startswith("data/demo/")):
                        problems.append(f"{label}: 잘못된 evidenceRef 형식={v!r}")
                problems += self._check_evidence(v, label, f"{_path}/{k}")
        elif isinstance(data, list):
            for i, item in enumerate(data):
                problems += self._check_evidence(item, label, f"{_path}[{i}]")
        return problems

    def _check_spk_refs(self, data: Any, label: str) -> list[str]:
        problems: list[str] = []
        max_idx = len(self.transcript)

        def walk(o: Any, path: str = "") -> None:
            if isinstance(o, dict):
                for k, v in o.items():
                    if k == "evidenceRef" and isinstance(v, str):
                        m = re.search(r"#spk:(\d+)$", v.strip())
                        if m:
                            idx = int(m.group(1))
                            if not (1 <= idx <= max_idx):
                                problems.append(f"{label}: #spk:{idx} 가 발화 범위(1~{max_idx})를 벗어남")
                        else:
                            # transcript 가 아닌 ref 는 위에서 형식 검증됨
                            pass
                    else:
                        walk(v, f"{path}/{k}")
            elif isinstance(o, list):
                for i, item in enumerate(o):
                    walk(item, f"{path}[{i}]")

        walk(data, label)
        return problems

    # ---------------- 조회 헬퍼 ----------------
    def get_customer(self, customer_id: str) -> Customer:
        try:
            return self.customers[customer_id]
        except KeyError as exc:
            raise DataLoadingError(f"존재하지 않는 고객 ID: {customer_id}") from exc

    def contracts_of(self, customer_id: str) -> list[Contract]:
        return [c for c in self.contracts if c.customer_id == customer_id]

    def eligible_customers(self) -> list[Customer]:
        return [c for c in self.customers.values() if c.is_eligible]

    def knowledge_text(self, fname: str) -> str:
        return self.knowledge_docs.get(fname, "")

    def utter_by_spk(self, spk_index: int) -> Utterance | None:
        if 1 <= spk_index <= len(self.transcript):
            return self.transcript[spk_index - 1]
        return None

    def utter_lines(self) -> list[str]:
        return [u.line for u in self.transcript]

    def utter_text(self) -> str:
        return "\n".join(u.line for u in self.transcript)

    # ---------------- 날짜 헬퍼 (기준일 고정) ----------------
    def days_until(self, iso_date: str | None) -> int | None:
        """기준일(2026-09-09)로부터 남은 일수. 갱신 등 D-Day 계산."""
        if not iso_date:
            return None
        return (date.fromisoformat(iso_date) - date.fromisoformat(self.demo_as_of_date)).days

    def months_elapsed(self, iso_date: str | None) -> int | None:
        """기준일 기준 경과 개월 수."""
        if not iso_date:
            return None
        d0 = date.fromisoformat(iso_date)
        d1 = date.fromisoformat(self.demo_as_of_date)
        return (d1.year - d0.year) * 12 + (d1.month - d0.month)

    # ---------------- 1-Pick 조회 (Prepared Expected) ----------------
    @property
    def pick(self) -> dict[str, Any]:
        """daily_pick_expected.json 의 daily_pick 절."""
        return self.daily_pick["daily_pick"]

    @property
    def pick_candidate_rows(self) -> list[dict[str, Any]]:
        """daily_pick_expected.json 의 candidates 절 (후보 명세)."""
        return self.daily_pick["candidates"]

    @property
    def pick_evidence(self) -> dict[str, Any]:
        return self.daily_pick["evidence"]


# ---------------------------------------------------------------------------
# 모듈 수준 캐시 (Streamlit rerun 간 재로딩 방지)
# ---------------------------------------------------------------------------
_loader: DataLoader | None = None


def get_loader() -> DataLoader:
    """전역 DataLoader 싱글턴. 최초 1회 로딩하고 이후 캐시한다."""
    global _loader
    if _loader is None:
        _loader = DataLoader().load_all()
    return _loader