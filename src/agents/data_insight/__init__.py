"""Data Insight Agent - mock database for testing Text-to-SQL and anomaly detection."""

from .mock_database import init_mock_db, get_schema, DB_PATH

__all__ = ["init_mock_db", "get_schema", "DB_PATH"]