"""1-Pick Rescue Agent — 전역 설정.

Demo 기준일은 2026-09-09 로 고정한다. 시스템 현재 날짜는 사용하지 않는다.
화면/코드 어디서든 이 모듈의 상수를 기준으로 동작한다.
"""
from pathlib import Path

# --- 경로 ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
SEED_DIR = DATA_DIR / "seed"
EXPECTED_DIR = DATA_DIR / "expected"
KNOWLEDGE_DIR = DATA_DIR / "knowledge"
DEMO_DIR = DATA_DIR / "demo"

# --- 데이터 파일 경로 (Data Loader 전용) ---
CUSTOMERS_PATH = SEED_DIR / "customers.json"
CONTRACTS_PATH = SEED_DIR / "contracts.json"
SCORING_RULES_PATH = SEED_DIR / "scoring_rules.json"

DAILY_PICK_EXPECTED_PATH = EXPECTED_DIR / "daily_pick_expected.json"
CONTACT_SCRIPT_EXPECTED_PATH = EXPECTED_DIR / "contact-script-expected.json"
SAFETY_REJECT_EXPECTED_PATH = EXPECTED_DIR / "safety-reject-expected.json"
SESSION_ANALYSIS_EXPECTED_PATH = EXPECTED_DIR / "session-analysis-expected.json"
CRM_RECORD_EXPECTED_PATH = EXPECTED_DIR / "crm-record-expected.json"
NEXT_ACTION_EXPECTED_PATH = EXPECTED_DIR / "next-action-expected.json"

KNOWLEDGE_FILES = [
    "product-guide.md",
    "terms.md",
    "renewal-faq.md",
    "sales-cautions.md",
]

TRANSCRIPT_PATH = DEMO_DIR / "consultation-transcript.txt"

# --- 데모 기준일 (ISO 8601) ---
DEMO_AS_OF_DATE = "2026-09-09"

# --- UI ---
APP_TITLE = "1-Pick Rescue Agent"
NOTICE_TEXT = (
    "본 데모에 표시된 모든 고객·계약·상품·상담 데이터는 해커톤 시연을 위한 "
    "가상 데이터이며 실제 보험계약이나 고객 정보가 아닙니다."
)

# --- 화면 상태 (demo_state.py 와 공유) ---
SCREEN_DAILY_PICK = "DAILY_PICK"
SCREEN_CONSULTATION = "CONSULTATION"
SCREEN_CLOSING = "CLOSING"