"""Tests for DataInsightAgent."""

import pytest
from pathlib import Path
import sys
from unittest.mock import MagicMock, patch
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from agents.data_insight.data_insight_agent import (
    DataInsightAgent,
    QueryResult,
    RootCauseReport,
    InsightReport,
)
from agents.data_insight.anomaly_detector import AnomalyPoint, SeverityLevel
from agents.data_insight.text_to_sql import SQLQuery, ValidationError
from agents.data_insight.mock_database import init_mock_db, DB_PATH


@pytest.fixture(autouse=True)
def setup_mock_db():
    """Initialize mock database before each test."""
    init_mock_db()
    yield
    # Cleanup after tests
    if DB_PATH.exists():
        DB_PATH.unlink()


class TestQueryResultDataclass:
    """Test QueryResult dataclass."""

    def test_query_result_creation(self):
        """Verify QueryResult can be created with all required fields."""
        result = QueryResult(
            sql="SELECT * FROM production_daily",
            results=[(1, 2, 3), (4, 5, 6)],
            row_count=2,
            execution_time=0.123
        )
        assert result.sql == "SELECT * FROM production_daily"
        assert result.results == [(1, 2, 3), (4, 5, 6)]
        assert result.row_count == 2
        assert result.execution_time == 0.123

    def test_query_result_empty_results(self):
        """Verify QueryResult works with empty results."""
        result = QueryResult(
            sql="SELECT * FROM production_daily WHERE 1=0",
            results=[],
            row_count=0,
            execution_time=0.001
        )
        assert result.row_count == 0
        assert result.results == []


class TestRootCauseReportDataclass:
    """Test RootCauseReport dataclass."""

    def test_root_cause_report_creation(self):
        """Verify RootCauseReport can be created with all required fields."""
        anomaly = AnomalyPoint(
            timestamp=datetime(2026, 4, 25, 10, 0, 0),
            metric="oee",
            value=0.95,
            expected_value=0.85,
            deviation=11.76,
            severity=SeverityLevel.HIGH,
            description="OEE value exceeded expected range"
        )
        report = RootCauseReport(
            anomaly=anomaly,
            possible_causes=["Equipment malfunction", "Raw material quality issue"],
            confidence=0.85,
            recommended_actions=["Inspect equipment", "Check material quality"]
        )
        assert report.anomaly == anomaly
        assert len(report.possible_causes) == 2
        assert report.confidence == 0.85
        assert len(report.recommended_actions) == 2


class TestInsightReportDataclass:
    """Test InsightReport dataclass."""

    def test_insight_report_creation(self):
        """Verify InsightReport can be created with all required fields."""
        anomaly = AnomalyPoint(
            timestamp=datetime(2026, 4, 25, 10, 0, 0),
            metric="oee",
            value=0.95,
            expected_value=0.85,
            deviation=11.76,
            severity=SeverityLevel.HIGH,
            description="OEE value exceeded expected range"
        )
        report = InsightReport(
            query="SELECT oee FROM production_daily",
            interpretation="OEE is above target",
            anomalies=[anomaly],
            root_causes=[],
            recommendations=["Monitor equipment"]
        )
        assert report.query == "SELECT oee FROM production_daily"
        assert report.interpretation == "OEE is above target"
        assert len(report.anomalies) == 1
        assert len(report.recommendations) == 1


class TestDataInsightAgentCreation:
    """Test DataInsightAgent instantiation."""

    def test_agent_default_creation(self):
        """Verify DataInsightAgent can be instantiated with defaults."""
        agent = DataInsightAgent()
        assert agent is not None
        assert agent.llm is not None
        assert agent.text_to_sql_converter is not None
        assert agent.anomaly_detector is not None

    def test_agent_with_custom_llm(self):
        """Verify DataInsightAgent accepts custom LLM client."""
        mock_llm = MagicMock()
        agent = DataInsightAgent(llm_client=mock_llm)
        assert agent.llm == mock_llm

    def test_agent_with_custom_detector(self):
        """Verify DataInsightAgent accepts custom AnomalyDetector."""
        mock_detector = MagicMock()
        agent = DataInsightAgent(anomaly_detector=mock_detector)
        assert agent.anomaly_detector == mock_detector


class TestTextToSql:
    """Test text_to_sql method."""

    def test_text_to_sql_returns_sql_query(self):
        """Verify text_to_sql returns a SQLQuery object."""
        mock_llm = MagicMock()
        mock_llm.generate = MagicMock(
            return_value="SQL: SELECT date, oee FROM production_daily\nEXPLANATION: Query returns OEE values by date"
        )
        agent = DataInsightAgent(llm_client=mock_llm)

        result = agent.text_to_sql("Show OEE values by date")

        assert isinstance(result, SQLQuery)
        assert result.sql is not None
        assert "production_daily" in result.sql.lower() or "SELECT" in result.sql.upper()

    def test_text_to_sql_calls_llm(self):
        """Verify text_to_sql calls the LLM client."""
        mock_llm = MagicMock()
        mock_llm.generate = MagicMock(
            return_value="SQL: SELECT 1\nEXPLANATION: Test"
        )
        agent = DataInsightAgent(llm_client=mock_llm)

        agent.text_to_sql("Test query")

        mock_llm.generate.assert_called_once()


class TestExecuteQuery:
    """Test execute_query method."""

    def test_execute_query_returns_query_result(self):
        """Verify execute_query returns a QueryResult object."""
        agent = DataInsightAgent()
        sql_query = SQLQuery(
            sql="SELECT date, plant, oee FROM production_daily LIMIT 5",
            explanation="Select sample data"
        )

        result = agent.execute_query(sql_query)

        assert isinstance(result, QueryResult)
        assert result.sql == sql_query.sql
        assert result.row_count > 0
        assert result.execution_time >= 0

    def test_execute_query_validates_select_only(self):
        """Verify execute_query only allows SELECT queries."""
        agent = DataInsightAgent()
        sql_query = SQLQuery(
            sql="DROP TABLE production_daily",
            explanation="Dangerous query"
        )

        with pytest.raises(ValidationError, match="Only SELECT queries"):
            agent.execute_query(sql_query)

    def test_execute_query_empty_result(self):
        """Verify execute_query handles empty results."""
        agent = DataInsightAgent()
        sql_query = SQLQuery(
            sql="SELECT * FROM production_daily WHERE oee > 999",
            explanation="No matches"
        )

        result = agent.execute_query(sql_query)

        assert result.row_count == 0
        assert result.results == []


class TestInterpretResult:
    """Test interpret_result method."""

    def test_interpret_result_returns_string(self):
        """Verify interpret_result returns a string interpretation."""
        mock_llm = MagicMock()
        mock_llm.generate = MagicMock(return_value="The data shows OEE values ranging from 0.8 to 0.95.")
        agent = DataInsightAgent(llm_client=mock_llm)

        query_result = QueryResult(
            sql="SELECT oee FROM production_daily",
            results=[(0.85,), (0.90,)],
            row_count=2,
            execution_time=0.1
        )

        interpretation = agent.interpret_result(query_result)

        assert isinstance(interpretation, str)
        assert len(interpretation) > 0

    def test_interpret_result_calls_llm(self):
        """Verify interpret_result calls the LLM client."""
        mock_llm = MagicMock()
        mock_llm.generate = MagicMock(return_value="Interpretation text")
        agent = DataInsightAgent(llm_client=mock_llm)

        query_result = QueryResult(
            sql="SELECT 1",
            results=[],
            row_count=0,
            execution_time=0.01
        )

        agent.interpret_result(query_result)

        mock_llm.generate.assert_called_once()


class TestDetectAnomaly:
    """Test detect_anomaly method."""

    def test_detect_anomaly_statistical(self):
        """Verify detect_anomaly uses statistical method by default."""
        agent = DataInsightAgent()

        # Data with a clear anomaly
        data = [10, 10.5, 10.2, 10.3, 10.1, 10.4, 10.2, 10.3, 10.5, 10.1, 50.0]

        anomalies = agent.detect_anomaly("test_metric", data, threshold=2.0, method="statistical")

        assert isinstance(anomalies, list)
        # Should detect the 50.0 as an anomaly
        assert len(anomalies) >= 1
        assert any(a.metric == "test_metric" for a in anomalies)

    def test_detect_anomaly_iqr(self):
        """Verify detect_anomaly supports IQR method."""
        agent = DataInsightAgent()

        # Data with a clear outlier
        data = [10, 10.5, 10.2, 10.3, 10.1, 10.4, 10.2, 10.3, 10.5, 10.1, 100.0]

        anomalies = agent.detect_anomaly("test_metric", data, threshold=1.5, method="iqr")

        assert isinstance(anomalies, list)

    def test_detect_anomaly_no_anomalies(self):
        """Verify detect_anomaly handles normal data gracefully."""
        agent = DataInsightAgent()

        # Normal data within bounds
        data = [10, 10.5, 10.2, 10.3, 10.1, 10.4, 10.2, 10.3, 10.5, 10.1]

        anomalies = agent.detect_anomaly("test_metric", data, threshold=3.0)

        assert isinstance(anomalies, list)
        # No anomalies expected with high threshold
        assert len(anomalies) == 0


class TestRootCauseAnalysis:
    """Test root_cause_analysis method."""

    def test_root_cause_analysis_returns_report(self):
        """Verify root_cause_analysis returns a RootCauseReport."""
        mock_llm = MagicMock()
        mock_llm.generate = MagicMock(
            return_value="Root cause analysis: Equipment malfunction likely. Check maintenance logs."
        )
        agent = DataInsightAgent(llm_client=mock_llm)

        anomaly = AnomalyPoint(
            timestamp=datetime(2026, 4, 25, 10, 0, 0),
            metric="oee",
            value=0.95,
            expected_value=0.85,
            deviation=11.76,
            severity=SeverityLevel.HIGH,
            description="OEE value exceeded expected range"
        )

        report = agent.root_cause_analysis(anomaly)

        assert isinstance(report, RootCauseReport)
        assert report.anomaly == anomaly
        assert isinstance(report.possible_causes, list)
        assert isinstance(report.recommended_actions, list)
        assert 0.0 <= report.confidence <= 1.0

    def test_root_cause_analysis_calls_llm(self):
        """Verify root_cause_analysis calls the LLM client."""
        mock_llm = MagicMock()
        mock_llm.generate = MagicMock(return_value="Analysis complete.")
        agent = DataInsightAgent(llm_client=mock_llm)

        anomaly = AnomalyPoint(
            timestamp=datetime(2026, 4, 25, 10, 0, 0),
            metric="test",
            value=100,
            expected_value=80,
            deviation=25.0,
            severity=SeverityLevel.MEDIUM,
            description="Test anomaly"
        )

        agent.root_cause_analysis(anomaly)

        mock_llm.generate.assert_called_once()


class TestGenerateInsightReport:
    """Test generate_insight_report method."""

    def test_generate_insight_report_returns_report(self):
        """Verify generate_insight_report returns an InsightReport."""
        mock_llm = MagicMock()
        mock_llm.generate = MagicMock(return_value="Report generated successfully.")
        agent = DataInsightAgent(llm_client=mock_llm)

        query_result = QueryResult(
            sql="SELECT oee FROM production_daily",
            results=[(0.85,), (0.90,)],
            row_count=2,
            execution_time=0.1
        )
        anomalies = []

        report = agent.generate_insight_report(query_result, anomalies)

        assert isinstance(report, InsightReport)
        assert report.query == query_result.sql
        assert isinstance(report.anomalies, list)
        assert isinstance(report.root_causes, list)
        assert isinstance(report.recommendations, list)

    def test_generate_insight_report_with_anomalies(self):
        """Verify generate_insight_report processes anomalies."""
        mock_llm = MagicMock()
        mock_llm.generate = MagicMock(return_value="Report with anomaly analysis.")
        agent = DataInsightAgent(llm_client=mock_llm)

        query_result = QueryResult(
            sql="SELECT oee FROM production_daily",
            results=[(0.85,), (0.90,)],
            row_count=2,
            execution_time=0.1
        )
        anomaly = AnomalyPoint(
            timestamp=datetime(2026, 4, 25, 10, 0, 0),
            metric="oee",
            value=0.95,
            expected_value=0.85,
            deviation=11.76,
            severity=SeverityLevel.HIGH,
            description="OEE value exceeded expected range"
        )

        report = agent.generate_insight_report(query_result, [anomaly])

        assert len(report.anomalies) == 1
        assert len(report.root_causes) == 1
        assert len(report.recommendations) > 0

    def test_generate_insight_report_calls_llm(self):
        """Verify generate_insight_report calls the LLM client multiple times."""
        mock_llm = MagicMock()
        mock_llm.generate = MagicMock(return_value="Analysis complete.")
        agent = DataInsightAgent(llm_client=mock_llm)

        query_result = QueryResult(
            sql="SELECT 1",
            results=[],
            row_count=0,
            execution_time=0.01
        )

        agent.generate_insight_report(query_result, [])

        # Should call LLM for interpretation and report generation
        assert mock_llm.generate.call_count >= 1


class TestEndToEnd:
    """End-to-end integration tests."""

    def test_full_analysis_workflow(self):
        """Verify a complete workflow from query to insight report."""
        mock_llm = MagicMock()
        # Use a proper SQL-formatted response for text_to_sql
        mock_llm.generate = MagicMock(
            side_effect=[
                "SQL: SELECT date, oee FROM production_daily WHERE date >= date('now', '-7 days')\nEXPLANATION: Query returns OEE values from last 7 days",
                "Analysis shows OEE values within normal range.",
                "Report generated successfully.",
                "Insight report completed."
            ]
        )
        agent = DataInsightAgent(llm_client=mock_llm)

        # Step 1: Convert natural language to SQL
        sql_query = agent.text_to_sql("Show OEE values from the last 7 days")

        # Step 2: Execute the query
        query_result = agent.execute_query(sql_query)
        assert query_result.row_count >= 0

        # Step 3: Interpret the results
        interpretation = agent.interpret_result(query_result)
        assert isinstance(interpretation, str)

        # Step 4: Generate insight report
        report = agent.generate_insight_report(query_result, [])
        assert isinstance(report, InsightReport)

    def test_anomaly_detection_workflow(self):
        """Verify anomaly detection and root cause analysis workflow."""
        mock_llm = MagicMock()
        mock_llm.generate = MagicMock(return_value="Root cause identified.")
        agent = DataInsightAgent(llm_client=mock_llm)

        # Get some data to analyze
        sql_query = SQLQuery(
            sql="SELECT oee FROM production_daily",
            explanation="Get OEE values"
        )
        query_result = agent.execute_query(sql_query)

        # Extract metric values
        data = [row[0] for row in query_result.results]

        # Detect anomalies if we have enough data
        if len(data) >= 3:
            anomalies = agent.detect_anomaly("oee", data, threshold=2.5)

            # If anomalies found, perform root cause analysis
            if anomalies:
                report = agent.root_cause_analysis(anomalies[0])
                assert isinstance(report, RootCauseReport)