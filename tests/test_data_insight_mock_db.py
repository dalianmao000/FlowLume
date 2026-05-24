"""Tests for Data Insight Agent mock database."""

import pytest
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from agents.data_insight.mock_database import (
    init_mock_db,
    get_schema,
    verify_data,
    get_connection,
    DB_PATH,
)


@pytest.fixture(autouse=True)
def setup_mock_db():
    """Initialize mock database before each test."""
    init_mock_db()
    yield
    # Cleanup after tests
    if DB_PATH.exists():
        DB_PATH.unlink()


class TestTablesExist:
    """Test that all required tables exist."""

    def test_production_daily_table_exists(self):
        """Verify production_daily table exists."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master WHERE type='table' AND name='production_daily'
        """)
        result = cursor.fetchone()
        conn.close()
        assert result is not None, "production_daily table should exist"

    def test_equipment_status_table_exists(self):
        """Verify equipment_status table exists."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master WHERE type='table' AND name='equipment_status'
        """)
        result = cursor.fetchone()
        conn.close()
        assert result is not None, "equipment_status table should exist"

    def test_quality_inspection_table_exists(self):
        """Verify quality_inspection table exists."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master WHERE type='table' AND name='quality_inspection'
        """)
        result = cursor.fetchone()
        conn.close()
        assert result is not None, "quality_inspection table should exist"


class TestRowCounts:
    """Test that tables have the expected number of rows."""

    def test_production_daily_row_count(self):
        """production_daily should have 180 rows (30 days x 3 lines x 2 plants)."""
        counts = verify_data()
        assert counts["production_daily"] == 180, f"Expected 180 rows, got {counts['production_daily']}"

    def test_equipment_status_row_count(self):
        """equipment_status should have approximately 500 rows."""
        counts = verify_data()
        assert counts["equipment_status"] == 500, f"Expected 500 rows, got {counts['equipment_status']}"

    def test_quality_inspection_row_count(self):
        """quality_inspection should have approximately 100 rows."""
        counts = verify_data()
        assert counts["quality_inspection"] == 100, f"Expected 100 rows, got {counts['quality_inspection']}"


class TestProductionDailySchema:
    """Test production_daily table schema."""

    def test_production_daily_columns(self):
        """Verify all required columns exist in production_daily."""
        schema = get_schema()
        columns = {col["name"] for col in schema["production_daily"]["columns"]}

        required_columns = {"date", "plant", "line", "output_qty", "defect_qty", "downtime_hours", "oee"}
        assert required_columns.issubset(columns), f"Missing columns: {required_columns - columns}"

    def test_production_daily_data_types(self):
        """Verify production_daily column types."""
        schema = get_schema()
        column_types = {col["name"]: col["type"] for col in schema["production_daily"]["columns"]}

        assert column_types["date"] == "TEXT"
        assert column_types["plant"] == "TEXT"
        assert column_types["line"] == "TEXT"
        assert column_types["output_qty"] == "INTEGER"
        assert column_types["defect_qty"] == "INTEGER"
        assert column_types["downtime_hours"] == "REAL"
        assert column_types["oee"] == "REAL"


class TestEquipmentStatusSchema:
    """Test equipment_status table schema."""

    def test_equipment_status_columns(self):
        """Verify all required columns exist in equipment_status."""
        schema = get_schema()
        columns = {col["name"] for col in schema["equipment_status"]["columns"]}

        required_columns = {"timestamp", "equipment_id", "status", "temperature", "pressure"}
        assert required_columns.issubset(columns), f"Missing columns: {required_columns - columns}"

    def test_equipment_status_data_types(self):
        """Verify equipment_status column types."""
        schema = get_schema()
        column_types = {col["name"]: col["type"] for col in schema["equipment_status"]["columns"]}

        assert column_types["timestamp"] == "TEXT"
        assert column_types["equipment_id"] == "TEXT"
        assert column_types["status"] == "TEXT"
        assert column_types["temperature"] == "REAL"
        assert column_types["pressure"] == "REAL"


class TestQualityInspectionSchema:
    """Test quality_inspection table schema."""

    def test_quality_inspection_columns(self):
        """Verify all required columns exist in quality_inspection."""
        schema = get_schema()
        columns = {col["name"] for col in schema["quality_inspection"]["columns"]}

        required_columns = {"inspection_date", "batch_no", "inspection_result", "defect_type", "quantity"}
        assert required_columns.issubset(columns), f"Missing columns: {required_columns - columns}"

    def test_quality_inspection_data_types(self):
        """Verify quality_inspection column types."""
        schema = get_schema()
        column_types = {col["name"]: col["type"] for col in schema["quality_inspection"]["columns"]}

        assert column_types["inspection_date"] == "TEXT"
        assert column_types["batch_no"] == "TEXT"
        assert column_types["inspection_result"] == "TEXT"
        assert column_types["defect_type"] == "TEXT"
        assert column_types["quantity"] == "INTEGER"


class TestDataValues:
    """Test actual data values in the database."""

    def test_production_daily_status_values(self):
        """Verify production_daily has valid OEE values (0-1 range)."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT oee FROM production_daily")
        oee_values = [row[0] for row in cursor.fetchall()]
        conn.close()

        assert all(0 <= oee <= 1 for oee in oee_values), "OEE values should be between 0 and 1"

    def test_equipment_status_has_valid_statuses(self):
        """Verify equipment_status has valid status values."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT status FROM equipment_status")
        statuses = {row[0] for row in cursor.fetchall()}
        conn.close()

        valid_statuses = {"RUNNING", "IDLE", "DOWN", "MAINTENANCE"}
        assert statuses.issubset(valid_statuses), f"Invalid statuses found: {statuses - valid_statuses}"

    def test_quality_inspection_has_valid_results(self):
        """Verify quality_inspection has valid inspection results."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT inspection_result FROM quality_inspection")
        results = {row[0] for row in cursor.fetchall()}
        conn.close()

        valid_results = {"PASS", "FAIL", "REWORK"}
        assert results.issubset(valid_results), f"Invalid inspection results found: {results - valid_results}"


class TestSchemaFunction:
    """Test the get_schema function."""

    def test_get_schema_returns_dict(self):
        """Verify get_schema returns a dictionary."""
        schema = get_schema()
        assert isinstance(schema, dict)

    def test_get_schema_has_all_tables(self):
        """Verify get_schema includes all three tables."""
        schema = get_schema()
        assert set(schema.keys()) == {"production_daily", "equipment_status", "quality_inspection"}

    def test_get_schema_column_info(self):
        """Verify get_schema returns proper column information."""
        schema = get_schema()

        for table in schema:
            for col in schema[table]["columns"]:
                assert "name" in col
                assert "type" in col