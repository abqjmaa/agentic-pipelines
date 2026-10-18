"""Versioned SQLite schema creation and additive migrations.
StateSchemaMixin uses the owning StateStore connection and shared schema version.
Applies transactional database migrations; performs no model or network work.
"""
from __future__ import annotations


from .state_common import SCHEMA_VERSION, StateError, _stamp


class StateSchemaMixin:
    def _columns(self, table: str) -> set[str]:
        return {row["name"] for row in self.connection.execute(f"PRAGMA table_info({table})")}


    def _add_column(self, table: str, declaration: str) -> None:
        name = declaration.split()[0]
        if name not in self._columns(table):
            self.connection.execute(f"ALTER TABLE {table} ADD COLUMN {declaration}")


    def _migrate(self) -> None:
        version = int(self.connection.execute("PRAGMA user_version").fetchone()[0])
        if version > SCHEMA_VERSION:
            raise StateError(f"state schema {version} is newer than runtime schema {SCHEMA_VERSION}")
        with self.connection:
            self.connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS entities (
                    id TEXT PRIMARY KEY,
                    source_path TEXT NOT NULL,
                    source_hash TEXT NOT NULL,
                    state TEXT NOT NULL,
                    candidate_path TEXT,
                    accepted_path TEXT,
                    error_code TEXT,
                    error_detail TEXT,
                    thread_path TEXT,
                    prompt_hash TEXT,
                    run_id TEXT,
                    lease_owner TEXT,
                    lease_expires TEXT,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS transitions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_id TEXT NOT NULL REFERENCES entities(id),
                    from_state TEXT,
                    to_state TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    evidence_path TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY,
                    started_at TEXT NOT NULL,
                    finished_at TEXT,
                    status TEXT NOT NULL,
                    processed INTEGER NOT NULL DEFAULT 0,
                    accepted INTEGER NOT NULL DEFAULT 0,
                    quarantined INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS attempts (
                    id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    entity_id TEXT NOT NULL REFERENCES entities(id),
                    stage TEXT NOT NULL,
                    prompt_id TEXT NOT NULL,
                    prompt_version TEXT NOT NULL,
                    prompt_hash TEXT NOT NULL,
                    status TEXT NOT NULL,
                    thread_path TEXT,
                    artifact_path TEXT,
                    error_code TEXT,
                    error_detail TEXT,
                    started_at TEXT NOT NULL,
                    finished_at TEXT
                );
                CREATE TABLE IF NOT EXISTS validator_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    entity_id TEXT NOT NULL REFERENCES entities(id),
                    attempt_id TEXT NOT NULL,
                    passed INTEGER NOT NULL,
                    evidence_json TEXT NOT NULL,
                    evidence_path TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS runner_lock (
                    singleton INTEGER PRIMARY KEY CHECK(singleton = 1),
                    owner TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    acquired_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS promotion_records (
                    id TEXT PRIMARY KEY,
                    entity_id TEXT NOT NULL REFERENCES entities(id),
                    original_hash TEXT NOT NULL,
                    candidate_hash TEXT NOT NULL,
                    backup_path TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    finished_at TEXT
                );
                """
            )
            for declaration in (
                "accepted_path TEXT", "prompt_hash TEXT", "run_id TEXT", "lease_owner TEXT", "lease_expires TEXT"
            ):
                self._add_column("entities", declaration)
            for declaration in (
                "request_bytes INTEGER",
                "response_bytes INTEGER",
                "context_limit INTEGER",
                "completion_limit INTEGER",
                "reasoning_mode TEXT",
                "failure_class TEXT",
                "authority TEXT",
                "validator_name TEXT",
                "retry_disposition TEXT",
                "provider TEXT",
                "model TEXT",
                "generation_config_json TEXT",
                "transport_attempts INTEGER",
                "transport_retry_json TEXT",
                "prompt_tokens INTEGER",
                "completion_tokens INTEGER",
                "prompt_template_bytes INTEGER",
                "session_id TEXT",
                "session_step INTEGER",
            ):
                self._add_column("attempts", declaration)
            if "created_at" not in self._columns("transitions"):
                self._add_column("transitions", "created_at TEXT")
                self.connection.execute("UPDATE transitions SET created_at=? WHERE created_at IS NULL", (_stamp(),))
            self.connection.execute("INSERT OR IGNORE INTO schema_migrations(version, applied_at) VALUES(?, ?)", (SCHEMA_VERSION, _stamp()))
            self.connection.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
