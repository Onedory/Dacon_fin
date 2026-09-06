import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from server.schemas import LogEntry

_SCHEMA = """
CREATE TABLE IF NOT EXISTS audit_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  user_query TEXT NOT NULL,        -- PII 마스킹 적용본만 저장
  domain TEXT,
  risk_level TEXT,
  action TEXT,
  violated_rules TEXT,             -- JSON: rule_id 배열만 (matched_text 미저장)
  retrieved_docs TEXT,             -- JSON: doc_id 배열
  raw_response TEXT,               -- PII 마스킹 적용본
  final_response TEXT,
  latency_ms INTEGER
);
"""


class AuditLogger:
    """감사 로거. 이후 모델 평가/SFT 데이터 분석에 활용 가능한 구조화 저장.
    원칙: PII 원문은 어떤 컬럼에도 저장하지 않는다 (호출측에서 마스킹본 전달 + 여기선 rule_id만 기록).
    """

    def __init__(self, db_path: str):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._lock = threading.Lock()
        with self._lock:
            self._conn.execute(_SCHEMA)
            self._conn.commit()

    def log(self, *, user_query: str, domain: str, risk_level: str, action: str,
            rule_ids: list[str], doc_ids: list[str],
            raw_response: str, final_response: str, latency_ms: int) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO audit_logs (ts, user_query, domain, risk_level, action, "
                "violated_rules, retrieved_docs, raw_response, final_response, latency_ms) "
                "VALUES (?,?,?,?,?,?,?,?,?,?)",
                (datetime.now(timezone.utc).isoformat(), user_query, domain,
                 risk_level, action, json.dumps(rule_ids), json.dumps(doc_ids),
                 raw_response, final_response, latency_ms))
            self._conn.commit()

    def list_logs(self, limit: int = 50) -> tuple[int, list[LogEntry]]:
        with self._lock:
            total = self._conn.execute("SELECT COUNT(*) FROM audit_logs").fetchone()[0]
            rows = self._conn.execute(
                "SELECT id, ts, user_query, domain, risk_level, action, final_response "
                "FROM audit_logs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        items = [LogEntry(id=r[0], ts=r[1], user_query=r[2], domain=r[3] or "",
                          risk_level=r[4] or "", action=r[5] or "",
                          final_response=r[6] or "") for r in rows]
        return total, items
    def close(self) -> None:
        with self._lock:
            self._conn.close()