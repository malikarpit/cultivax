"""
Test Backup Cron Task — NFR-8

Tests automated database backup job behavior.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone


class TestBackupCron:
    """Tests for the database_backup cron task."""

    @pytest.fixture
    def db_session(self):
        """Mock database session."""
        session = MagicMock()
        session.query.return_value.filter.return_value.first.return_value = None
        return session

    @patch("app.services.cron._should_run", return_value=(True, None))
    @patch("app.services.cron._record_run")
    @patch("app.services.cron._reset_failures")
    @patch("os.getenv", return_value="sqlite:///test.db")
    async def test_backup_skipped_for_non_postgres(
        self, mock_env, mock_reset, mock_record, mock_should, db_session
    ):
        """Backup should be skipped for non-PostgreSQL databases."""
        from app.services.cron import _run_database_backup

        result = await _run_database_backup(db_session, force=True)
        assert result["status"] == "ok"
        assert result.get("backup_result") == "skipped"

    @patch("app.services.cron._should_run", return_value=(False, "not_due"))
    async def test_backup_not_due(self, mock_should, db_session):
        """Backup should be skipped when not due."""
        from app.services.cron import _run_database_backup

        result = await _run_database_backup(db_session, force=False)
        assert result["status"] == "skipped"

    @patch("app.services.cron._should_run", return_value=(True, None))
    @patch("app.services.cron._record_run")
    @patch("app.services.cron._reset_failures")
    async def test_backup_log_record_created(
        self, mock_reset, mock_record, mock_should, db_session
    ):
        """Backup should create a BackupLog record."""
        from app.services.cron import _run_database_backup

        with patch("os.getenv", return_value=""):
            result = await _run_database_backup(db_session, force=True)

        # Verify db.add was called (backup log created)
        assert db_session.add.called
        assert db_session.commit.called

    @patch("app.services.cron._should_run", return_value=(True, None))
    @patch("app.services.cron._record_run")
    @patch("app.services.cron._reset_failures")
    @patch("os.getenv", return_value="postgresql://localhost:5432/cultivax")
    @patch("subprocess.run")
    async def test_backup_postgres_success(
        self, mock_run, mock_env, mock_reset, mock_record, mock_should, db_session
    ):
        """Backup should execute pg_dump for PostgreSQL databases."""
        mock_run.return_value = MagicMock(returncode=0)

        from app.services.cron import _run_database_backup

        result = await _run_database_backup(db_session, force=True)
        assert result["status"] == "ok"
