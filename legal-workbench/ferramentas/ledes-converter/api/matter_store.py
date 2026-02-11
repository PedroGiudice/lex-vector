import os
import sqlite3
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class Matter:
    """Entidade central de persistencia."""
    matter_name: str          # PK
    matter_id: str            # LAW_FIRM_MATTER_ID (ex: LS-2020-05805)
    client_matter_id: str     # CLIENT_MATTER_ID (campo 24)
    client_id: str            # CLIENT_ID (ex: Salesforce, Inc.)
    client_name: str          # nome legivel
    law_firm_id: str          # LAW_FIRM_ID (ex: SF004554)
    law_firm_name: str        # nome da firma
    timekeeper_id: str        # TIMEKEEPER_ID (ex: CMR)
    timekeeper_name: str      # TIMEKEEPER_NAME (ex: RODRIGUES, CARLOS MAGNO)
    timekeeper_classification: str  # PARTNR, ASSOCIATE, etc.
    unit_cost: float          # rate por unidade (ex: 300.00)
    default_task_code: str = ""
    default_activity_code: str = ""
    created_at: str = ""
    updated_at: str = ""


class MatterStore:
    """CRUD para Matters usando SQLite."""

    def __init__(self, db_path: str | None = None):
        if db_path is None:
            data_path = os.getenv("LEDES_DATA_PATH", "")
            if data_path:
                db_path = os.path.join(data_path, "matters.db")
            else:
                db_path = str(Path(__file__).parent.parent / "data" / "matters.db")
        self.db_path = db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Cria tabela se nao existir e faz seed inicial."""
        conn = self._get_conn()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS matters (
                    matter_name TEXT PRIMARY KEY,
                    matter_id TEXT NOT NULL,
                    client_matter_id TEXT DEFAULT '',
                    client_id TEXT NOT NULL,
                    client_name TEXT DEFAULT '',
                    law_firm_id TEXT NOT NULL,
                    law_firm_name TEXT DEFAULT '',
                    timekeeper_id TEXT DEFAULT '',
                    timekeeper_name TEXT DEFAULT '',
                    timekeeper_classification TEXT DEFAULT '',
                    unit_cost REAL DEFAULT 0.0,
                    default_task_code TEXT DEFAULT '',
                    default_activity_code TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.commit()
            self._seed_if_empty(conn)
        finally:
            conn.close()

    def _seed_if_empty(self, conn: sqlite3.Connection):
        """Seed com os 3 matters conhecidos se o banco estiver vazio."""
        count = conn.execute("SELECT COUNT(*) FROM matters").fetchone()[0]
        if count > 0:
            return

        now = datetime.now(timezone.utc).isoformat()
        seed_data = [
            Matter(
                matter_name="CMR General Litigation Matters",
                matter_id="LS-2020-05805",
                client_matter_id="",
                client_id="Salesforce, Inc.",
                client_name="Salesforce, Inc.",
                law_firm_id="SF004554",
                law_firm_name="C. M. Rodrigues Sociedade de Advogados",
                timekeeper_id="CMR",
                timekeeper_name="RODRIGUES, CARLOS MAGNO",
                timekeeper_classification="PARTNR",
                unit_cost=300.00,
                created_at=now,
                updated_at=now,
            ),
            Matter(
                matter_name="BRA/STLandATDIL/CRM/Governance",
                matter_id="LS-2025-23274",
                client_matter_id="",
                client_id="Salesforce, Inc.",
                client_name="Salesforce, Inc.",
                law_firm_id="SF004554",
                law_firm_name="C. M. Rodrigues Sociedade de Advogados",
                timekeeper_id="CMR",
                timekeeper_name="RODRIGUES, CARLOS MAGNO",
                timekeeper_classification="PARTNR",
                unit_cost=300.00,
                created_at=now,
                updated_at=now,
            ),
            Matter(
                matter_name="FY26 - General Employment Advice (Brazil)",
                matter_id="LS-2025-22672",
                client_matter_id="",
                client_id="Salesforce, Inc.",
                client_name="Salesforce, Inc.",
                law_firm_id="SF004554",
                law_firm_name="C. M. Rodrigues Sociedade de Advogados",
                timekeeper_id="CMR",
                timekeeper_name="RODRIGUES, CARLOS MAGNO",
                timekeeper_classification="PARTNR",
                unit_cost=300.00,
                created_at=now,
                updated_at=now,
            ),
            Matter(
                matter_name="[WA-27] Brazil - Employment Advice",
                matter_id="LS-2026-24216",
                client_matter_id="",
                client_id="Salesforce, Inc.",
                client_name="Salesforce, Inc.",
                law_firm_id="SF004554",
                law_firm_name="C.M. Rodrigues Sociedade de Advogados",
                timekeeper_id="CMR",
                timekeeper_name="RODRIGUES, CARLOS MAGNO",
                timekeeper_classification="PARTNR",
                unit_cost=300.00,
                default_task_code="L100",
                default_activity_code="A103",
                created_at=now,
                updated_at=now,
            ),
        ]
        for matter in seed_data:
            self._insert(conn, matter)
        conn.commit()
        logger.info(f"Seeded {len(seed_data)} matters")

    def _insert(self, conn: sqlite3.Connection, matter: Matter):
        d = asdict(matter)
        cols = ", ".join(d.keys())
        placeholders = ", ".join(["?"] * len(d))
        conn.execute(
            f"INSERT INTO matters ({cols}) VALUES ({placeholders})",
            list(d.values()),
        )

    def list_all(self) -> list[Matter]:
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM matters ORDER BY matter_name"
            ).fetchall()
            return [Matter(**dict(row)) for row in rows]
        finally:
            conn.close()

    def get(self, matter_name: str) -> Matter | None:
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM matters WHERE matter_name = ?",
                (matter_name,),
            ).fetchone()
            return Matter(**dict(row)) if row else None
        finally:
            conn.close()

    def create(self, matter: Matter) -> Matter:
        now = datetime.now(timezone.utc).isoformat()
        matter.created_at = now
        matter.updated_at = now
        conn = self._get_conn()
        try:
            self._insert(conn, matter)
            conn.commit()
            return matter
        finally:
            conn.close()

    def update(self, matter_name: str, updates: dict) -> Matter | None:
        existing = self.get(matter_name)
        if not existing:
            return None
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
        conn = self._get_conn()
        try:
            conn.execute(
                f"UPDATE matters SET {set_clause} WHERE matter_name = ?",
                list(updates.values()) + [matter_name],
            )
            conn.commit()
            return self.get(matter_name)
        finally:
            conn.close()

    def delete(self, matter_name: str) -> bool:
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                "DELETE FROM matters WHERE matter_name = ?",
                (matter_name,),
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
