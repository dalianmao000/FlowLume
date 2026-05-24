"""Tests for Text-to-SQL module."""

import pytest
from pathlib import Path
import sys
from unittest.mock import MagicMock, AsyncMock

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from agents.data_insight.text_to_sql import (
    DatabaseSchema,
    ColumnInfo,
    TableInfo,
    SQLQuery,
    TextToSQLConverter,
    ValidationError,
    SQLGenerationError,
)


class TestDatabaseSchema:
    """Test DatabaseSchema class."""

    def test_schema_initialization(self):
        """Test schema can be initialized with tables."""
        tables = [
            TableInfo(
                name="production_daily",
                columns=[
                    ColumnInfo(name="date", type="TEXT", description="Production date"),
                    ColumnInfo(name="oee", type="REAL", description="Overall Equipment Effectiveness"),
                ],
            )
        ]
        schema = DatabaseSchema(tables=tables)
        assert schema is not None

    def test_get_table_existing(self):
        """Test retrieving an existing table."""
        tables = [
            TableInfo(
                name="production_daily",
                columns=[
                    ColumnInfo(name="date", type="TEXT", description="Production date"),
                ],
            )
        ]
        schema = DatabaseSchema(tables=tables)
        table = schema.get_table("production_daily")
        assert table is not None
        assert table.name == "production_daily"

    def test_get_table_non_existing(self):
        """Test retrieving a non-existing table returns None."""
        schema = DatabaseSchema(tables=[])
        table = schema.get_table("non_existing")
        assert table is None

    def test_schema_from_mock_db(self):
        """Test creating schema from mock database structure."""
        from agents.data_insight.mock_database import get_schema

        mock_schema = get_schema()
        tables = []

        for table_name, table_data in mock_schema.items():
            columns = [
                ColumnInfo(
                    name=col["name"],
                    type=col["type"],
                    description="",
                )
                for col in table_data["columns"]
            ]
            tables.append(TableInfo(name=table_name, columns=columns))

        schema = DatabaseSchema(tables=tables)
        assert schema.get_table("production_daily") is not None
        assert schema.get_table("equipment_status") is not None
        assert schema.get_table("quality_inspection") is not None


class TestColumnInfo:
    """Test ColumnInfo dataclass."""

    def test_column_info_creation(self):
        """Test ColumnInfo can be created."""
        col = ColumnInfo(name="oee", type="REAL", description="OEE metric")
        assert col.name == "oee"
        assert col.type == "REAL"
        assert col.description == "OEE metric"


class TestTableInfo:
    """Test TableInfo dataclass."""

    def test_table_info_creation(self):
        """Test TableInfo can be created."""
        columns = [
            ColumnInfo(name="date", type="TEXT", description="Date"),
            ColumnInfo(name="oee", type="REAL", description="OEE"),
        ]
        table = TableInfo(name="production_daily", columns=columns)
        assert table.name == "production_daily"
        assert len(table.columns) == 2


class TestSQLQuery:
    """Test SQLQuery dataclass."""

    def test_sql_query_creation(self):
        """Test SQLQuery can be created."""
        query = SQLQuery(
            sql="SELECT * FROM production_daily",
            explanation="Selects all data from production_daily",
            confidence=0.95,
        )
        assert query.sql == "SELECT * FROM production_daily"
        assert query.explanation == "Selects all data from production_daily"
        assert query.confidence == 0.95

    def test_sql_query_defaults(self):
        """Test SQLQuery default confidence."""
        query = SQLQuery(sql="SELECT 1", explanation="Returns 1", confidence=0.5)
        assert query.confidence == 0.5


class TestTextToSQLConverter:
    """Test TextToSQLConverter class."""

    @pytest.fixture
    def mock_schema(self):
        """Create a mock schema for testing."""
        tables = [
            TableInfo(
                name="production_daily",
                columns=[
                    ColumnInfo(name="date", type="TEXT", description="Production date"),
                    ColumnInfo(name="plant", type="TEXT", description="Plant name"),
                    ColumnInfo(name="line", type="TEXT", description="Production line"),
                    ColumnInfo(name="output_qty", type="INTEGER", description="Output quantity"),
                    ColumnInfo(name="defect_qty", type="INTEGER", description="Defect quantity"),
                    ColumnInfo(name="downtime_hours", type="REAL", description="Downtime hours"),
                    ColumnInfo(name="oee", type="REAL", description="Overall Equipment Effectiveness"),
                ],
            ),
            TableInfo(
                name="equipment_status",
                columns=[
                    ColumnInfo(name="timestamp", type="TEXT", description="Event timestamp"),
                    ColumnInfo(name="equipment_id", type="TEXT", description="Equipment ID"),
                    ColumnInfo(name="status", type="TEXT", description="Equipment status"),
                    ColumnInfo(name="temperature", type="REAL", description="Temperature reading"),
                    ColumnInfo(name="pressure", type="REAL", description="Pressure reading"),
                ],
            ),
        ]
        return DatabaseSchema(tables=tables)

    @pytest.fixture
    def mock_llm_client(self):
        """Create a mock LLM client."""
        client = MagicMock()
        client.generate = MagicMock(return_value="SELECT * FROM production_daily")
        return client

    def test_converter_initialization(self, mock_schema, mock_llm_client):
        """Test TextToSQLConverter initializes correctly."""
        converter = TextToSQLConverter(schema=mock_schema, llm_client=mock_llm_client)
        assert converter.schema == mock_schema
        assert converter.llm_client == mock_llm_client

    def test_convert_returns_sql_query(self, mock_schema, mock_llm_client):
        """Test convert method returns SQLQuery."""
        converter = TextToSQLConverter(schema=mock_schema, llm_client=mock_llm_client)
        result = converter.convert("Show all production data")
        assert isinstance(result, SQLQuery)
        assert result.sql is not None
        assert result.explanation is not None

    def test_convert_includes_schema_context(self, mock_schema, mock_llm_client):
        """Test that schema is included in LLM prompt."""
        converter = TextToSQLConverter(schema=mock_schema, llm_client=mock_llm_client)
        converter.convert("Show data")
        # Verify LLM was called with prompt containing schema info
        mock_llm_client.generate.assert_called_once()
        call_args = mock_llm_client.generate.call_args
        prompt = call_args[0][0] if call_args[0] else call_args[1].get("prompt", "")
        assert "production_daily" in prompt.lower()

    def test_validate_sql_valid_select(self, mock_schema, mock_llm_client):
        """Test SQL validation passes for valid SELECT."""
        converter = TextToSQLConverter(schema=mock_schema, llm_client=mock_llm_client)
        # Should not raise for valid SQL
        result = converter.validate_sql("SELECT date, oee FROM production_daily WHERE oee < 0.8")
        assert result is True

    def test_validate_sql_invalid_syntax(self, mock_schema, mock_llm_client):
        """Test SQL validation fails for invalid SQL."""
        converter = TextToSQLConverter(schema=mock_schema, llm_client=mock_llm_client)
        with pytest.raises(ValidationError):
            converter.validate_sql("SELEC * FROM production_daily")

    def test_validate_sql_dangerous_operations(self, mock_schema, mock_llm_client):
        """Test SQL validation rejects dangerous operations."""
        converter = TextToSQLConverter(schema=mock_schema, llm_client=mock_llm_client)

        dangerous_operations = [
            "DROP TABLE production_daily",
            "DELETE FROM production_daily WHERE 1=1",
            "DROP INDEX idx_production",
            "TRUNCATE TABLE production_daily",
            "ALTER TABLE production_daily DROP COLUMN date",
            "INSERT INTO production_daily VALUES (1,2,3)",
            "UPDATE production_daily SET oee = 1.0",
        ]

        for sql in dangerous_operations:
            with pytest.raises(ValidationError, match="Forbidden SQL operation"):
                converter.validate_sql(sql)

    def test_validate_sql_rejects_unknown_tables(self, mock_schema, mock_llm_client):
        """Test SQL validation rejects queries on unknown tables."""
        converter = TextToSQLConverter(schema=mock_schema, llm_client=mock_llm_client)
        with pytest.raises(ValidationError, match="Unknown table"):
            converter.validate_sql("SELECT * FROM unknown_table")

    def test_validate_sql_rejects_unknown_columns(self, mock_schema, mock_llm_client):
        """Test SQL validation rejects queries with unknown columns."""
        converter = TextToSQLConverter(schema=mock_schema, llm_client=mock_llm_client)
        with pytest.raises(ValidationError, match="Unknown column"):
            converter.validate_sql("SELECT unknown_col FROM production_daily")

    def test_validate_sql_allows_valid_aggregations(self, mock_schema, mock_llm_client):
        """Test SQL validation allows GROUP BY and ORDER BY."""
        converter = TextToSQLConverter(schema=mock_schema, llm_client=mock_llm_client)
        # Should not raise for valid aggregation queries
        result = converter.validate_sql(
            "SELECT line, AVG(oee) as avg_oee FROM production_daily GROUP BY line ORDER BY avg_oee"
        )
        assert result is True

    def test_validate_sql_allows_joins(self, mock_schema, mock_llm_client):
        """Test SQL validation allows JOINs between known tables."""
        # Create schema with both tables
        tables = [
            TableInfo(
                name="production_daily",
                columns=[
                    ColumnInfo(name="date", type="TEXT", description="Date"),
                    ColumnInfo(name="line", type="TEXT", description="Line"),
                    ColumnInfo(name="oee", type="REAL", description="OEE"),
                ],
            ),
            TableInfo(
                name="equipment_status",
                columns=[
                    ColumnInfo(name="timestamp", type="TEXT", description="Timestamp"),
                    ColumnInfo(name="equipment_id", type="TEXT", description="Equipment ID"),
                    ColumnInfo(name="status", type="TEXT", description="Status"),
                ],
            ),
        ]
        schema = DatabaseSchema(tables=tables)
        converter = TextToSQLConverter(schema=schema, llm_client=mock_llm_client)
        # Should not raise for valid join
        result = converter.validate_sql(
            "SELECT p.line, e.status FROM production_daily p JOIN equipment_status e ON p.line = e.equipment_id"
        )
        assert result is True


class TestSQLGenerationError:
    """Test SQLGenerationError exception."""

    def test_error_message(self):
        """Test SQLGenerationError has proper message."""
        error = SQLGenerationError("Failed to generate SQL")
        assert str(error) == "Failed to generate SQL"


class TestValidationError:
    """Test ValidationError exception."""

    def test_error_message(self):
        """Test ValidationError has proper message."""
        error = ValidationError("Invalid SQL syntax")
        assert str(error) == "Invalid SQL syntax"


class TestEdgeCases:
    """Test edge cases for Text-to-SQL conversion."""

    @pytest.fixture
    def mock_schema(self):
        """Create a minimal mock schema for testing."""
        tables = [
            TableInfo(
                name="production_daily",
                columns=[
                    ColumnInfo(name="date", type="TEXT", description="Date"),
                    ColumnInfo(name="oee", type="REAL", description="OEE"),
                ],
            )
        ]
        return DatabaseSchema(tables=tables)

    @pytest.fixture
    def mock_llm_client(self):
        """Create a mock LLM client."""
        client = MagicMock()
        return client

    def test_empty_query(self, mock_schema, mock_llm_client):
        """Test handling of empty query."""
        converter = TextToSQLConverter(schema=mock_schema, llm_client=mock_llm_client)
        # Empty query should raise an error
        with pytest.raises(SQLGenerationError):
            converter.convert("")

    def test_whitespace_query(self, mock_schema, mock_llm_client):
        """Test handling of whitespace-only query."""
        converter = TextToSQLConverter(schema=mock_schema, llm_client=mock_llm_client)
        # Whitespace query should raise an error
        with pytest.raises(SQLGenerationError):
            converter.convert("   ")

    def test_confidence_score_bounds(self, mock_schema, mock_llm_client):
        """Test confidence score is between 0 and 1."""
        mock_llm_client.generate = MagicMock(
            return_value="SELECT date, oee FROM production_daily ORDER BY oee LIMIT 1"
        )
        converter = TextToSQLConverter(schema=mock_schema, llm_client=mock_llm_client)
        result = converter.convert("Find the line with lowest OEE yesterday")
        assert 0.0 <= result.confidence <= 1.0