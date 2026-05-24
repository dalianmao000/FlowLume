"""Data Insight Agent - main agent class for data analysis and anomaly detection.

This module provides:
- DataInsightAgent: Main agent for orchestrating data analysis workflows
- QueryResult: Data class for SQL query results
- RootCauseReport: Data class for root cause analysis results
- InsightReport: Data class for complete insight reports
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import time
import sqlite3

from src.llm.claude_client import ClaudeClient
from src.prompts.data_insight import (
    SYSTEM_PROMPT,
    RESULT_INTERPRETATION_PROMPT,
    ROOT_CAUSE_ANALYSIS_PROMPT,
    INSIGHT_REPORT_PROMPT,
)

from .text_to_sql import (
    TextToSQLConverter,
    SQLQuery,
    DatabaseSchema,
    TableInfo,
    ColumnInfo,
    ValidationError,
)
from .anomaly_detector import (
    AnomalyDetector,
    AnomalyPoint,
    SeverityLevel,
)
from .mock_database import DB_PATH


@dataclass
class QueryResult:
    """Result of executing a SQL query.

    Attributes:
        sql: The SQL query that was executed
        results: List of result rows (each row is a tuple)
        row_count: Number of rows returned
        execution_time: Time taken to execute the query in seconds
    """
    sql: str
    results: List[tuple]
    row_count: int
    execution_time: float


@dataclass
class RootCauseReport:
    """Report of root cause analysis for an anomaly.

    Attributes:
        anomaly: The anomaly that was analyzed
        possible_causes: List of possible root causes
        confidence: Confidence score (0-1) for the analysis
        recommended_actions: List of recommended actions to address the root cause
    """
    anomaly: AnomalyPoint
    possible_causes: List[str]
    confidence: float
    recommended_actions: List[str]


@dataclass
class InsightReport:
    """Complete insight report combining query results and anomaly analysis.

    Attributes:
        query: The original natural language query
        interpretation: Natural language interpretation of the results
        anomalies: List of detected anomalies
        root_causes: List of root cause reports for the anomalies
        recommendations: Consolidated list of recommended actions
    """
    query: str
    interpretation: str
    anomalies: List[AnomalyPoint]
    root_causes: List[RootCauseReport]
    recommendations: List[str]


class DataInsightAgent:
    """Main agent for data insight and anomaly detection.

    Orchestrates the Text-to-SQL conversion, query execution, anomaly detection,
    and root cause analysis modules to provide comprehensive data insights.

    Attributes:
        llm: LLM client for generating interpretations and analyses
        text_to_sql_converter: Converter for natural language to SQL
        anomaly_detector: Detector for identifying anomalies in data
        db_path: Path to the SQLite database
    """

    def __init__(
        self,
        llm_client: Optional[ClaudeClient] = None,
        text_to_sql_converter: Optional[TextToSQLConverter] = None,
        anomaly_detector: Optional[AnomalyDetector] = None,
        db_path: str = str(DB_PATH),
    ):
        """Initialize the DataInsightAgent.

        Args:
            llm_client: LLM client for generating interpretations. If not provided,
                        a new ClaudeClient will be created.
            text_to_sql_converter: Converter for natural language to SQL. If not provided,
                                  a new converter will be created using the default schema.
            anomaly_detector: Detector for identifying anomalies. If not provided,
                             a new detector will be created.
            db_path: Path to the SQLite database file.
        """
        self.llm = llm_client or ClaudeClient()
        self.text_to_sql_converter = text_to_sql_converter
        self.anomaly_detector = anomaly_detector or AnomalyDetector()
        self.db_path = db_path
        self.system_prompt = SYSTEM_PROMPT

        # Initialize default text-to-sql converter if not provided
        if self.text_to_sql_converter is None:
            self._init_text_to_sql_converter()

    def _init_text_to_sql_converter(self) -> None:
        """Initialize the default TextToSQLConverter with manufacturing schema."""
        # Define the manufacturing database schema
        tables = [
            TableInfo(
                name="production_daily",
                columns=[
                    ColumnInfo(name="date", type="TEXT", description="Production date (YYYY-MM-DD)"),
                    ColumnInfo(name="plant", type="TEXT", description="Plant name"),
                    ColumnInfo(name="line", type="TEXT", description="Production line identifier"),
                    ColumnInfo(name="output_qty", type="INTEGER", description="Number of units produced"),
                    ColumnInfo(name="defect_qty", type="INTEGER", description="Number of defective units"),
                    ColumnInfo(name="downtime_hours", type="REAL", description="Hours of downtime"),
                    ColumnInfo(name="oee", type="REAL", description="Overall Equipment Effectiveness (0-1)"),
                ],
            ),
            TableInfo(
                name="equipment_status",
                columns=[
                    ColumnInfo(name="timestamp", type="TEXT", description="Status timestamp"),
                    ColumnInfo(name="equipment_id", type="TEXT", description="Equipment identifier"),
                    ColumnInfo(name="status", type="TEXT", description="Equipment status (RUNNING/IDLE/DOWN/MAINTENANCE)"),
                    ColumnInfo(name="temperature", type="REAL", description="Equipment temperature"),
                    ColumnInfo(name="pressure", type="REAL", description="Equipment pressure"),
                ],
            ),
            TableInfo(
                name="quality_inspection",
                columns=[
                    ColumnInfo(name="inspection_date", type="TEXT", description="Inspection date"),
                    ColumnInfo(name="batch_no", type="TEXT", description="Batch number"),
                    ColumnInfo(name="inspection_result", type="TEXT", description="Result (PASS/FAIL/REWORK)"),
                    ColumnInfo(name="defect_type", type="TEXT", description="Type of defect if any"),
                    ColumnInfo(name="quantity", type="INTEGER", description="Quantity inspected"),
                ],
            ),
        ]

        schema = DatabaseSchema(tables=tables)
        self.text_to_sql_converter = TextToSQLConverter(schema=schema, llm_client=self.llm)

    def text_to_sql(self, query: str, schema: Optional[Dict[str, Any]] = None) -> SQLQuery:
        """Convert a natural language query to SQL.

        Args:
            query: Natural language query string
            schema: Optional schema dictionary (not used, kept for API compatibility)

        Returns:
            SQLQuery containing the generated SQL, explanation, and confidence score

        Raises:
            SQLGenerationError: If SQL generation fails after retries
            ValidationError: If generated SQL fails validation
        """
        return self.text_to_sql_converter.convert(query)

    def execute_query(self, sql: SQLQuery) -> QueryResult:
        """Execute a SQL query and return the results.

        Args:
            sql: SQLQuery object containing the SQL string to execute

        Returns:
            QueryResult with the query results, row count, and execution time

        Raises:
            ValidationError: If the SQL is not a SELECT query
            sqlite3.Error: If query execution fails
        """
        # Validate that this is a SELECT query (security check)
        sql_upper = sql.sql.strip().upper()
        if not sql_upper.startswith("SELECT"):
            raise ValidationError("Only SELECT queries are allowed for execution")

        # Execute the query
        start_time = time.time()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(sql.sql)
            results = cursor.fetchall()
            row_count = len(results)
        finally:
            conn.close()

        execution_time = time.time() - start_time

        return QueryResult(
            sql=sql.sql,
            results=results,
            row_count=row_count,
            execution_time=execution_time,
        )

    def interpret_result(self, result: QueryResult) -> str:
        """Generate a natural language interpretation of query results.

        Args:
            result: QueryResult containing the SQL query and results

        Returns:
            Natural language interpretation of the data
        """
        # Format the results for the prompt
        if result.row_count == 0:
            data_results = "No data returned from query."
            summary = "No data available."
        else:
            # Limit to first 10 rows for the prompt
            display_results = result.results[:10]
            rows_str = "\n".join([str(row) for row in display_results])
            suffix = f"\n... and {result.row_count - 10} more rows" if result.row_count > 10 else ""
            data_results = f"Row count: {result.row_count}\nData:\n{rows_str}{suffix}"

            # Calculate basic statistics if we have numeric data
            try:
                numeric_values = [row[0] for row in result.results if row[0] is not None]
                if numeric_values and all(isinstance(v, (int, float)) for v in numeric_values):
                    min_val = min(numeric_values)
                    max_val = max(numeric_values)
                    avg_val = sum(numeric_values) / len(numeric_values)
                    summary = f"Data has {result.row_count} rows with values ranging from {min_val} to {max_val}, averaging {avg_val:.2f}."
                else:
                    summary = f"Data has {result.row_count} rows."
            except:
                summary = f"Data has {result.row_count} rows."

        prompt = f"""Please interpret the following query results:

SQL Query: {result.sql}

Results:
{data_results}

{summary}

Provide a concise natural language interpretation focusing on key findings and any notable patterns."""

        interpretation = self.llm.generate(self.system_prompt, prompt)
        return interpretation

    def detect_anomaly(
        self,
        metric: str,
        data: List[float],
        threshold: float = 2.0,
        method: str = "statistical"
    ) -> List[AnomalyPoint]:
        """Detect anomalies in the provided data.

        Args:
            metric: Name of the metric being analyzed
            data: List of numerical values to analyze
            threshold: Threshold for anomaly detection (default 2.0 for z-score)
            method: Detection method - "statistical" or "iqr" (default "statistical")

        Returns:
            List of AnomalyPoint objects representing detected anomalies
        """
        if method == "iqr":
            anomalies = self.anomaly_detector.detect_iqr(data, multiplier=threshold)
        else:
            anomalies = self.anomaly_detector.detect_statistical(data, threshold=threshold)

        # Update metric name for all anomalies
        for anomaly in anomalies:
            anomaly.metric = metric

        return anomalies

    def root_cause_analysis(self, anomaly: AnomalyPoint) -> RootCauseReport:
        """Analyze the root cause of an anomaly.

        Args:
            anomaly: The AnomalyPoint to analyze

        Returns:
            RootCauseReport with possible causes, confidence, and recommended actions
        """
        # Build the prompt for root cause analysis
        prompt = ROOT_CAUSE_ANALYSIS_PROMPT.format(
            anomaly_description=f"{anomaly.metric}: {anomaly.description}",
            related_data=f"Value: {anomaly.value}, Expected: {anomaly.expected_value}, Deviation: {anomaly.deviation}%",
            equipment_status="Not available",
            operation_logs="Not available",
            maintenance_history="Not available",
            production_context="Anomaly detected in manufacturing data",
            problem_statement=anomaly.description,
            why1="Why did the anomaly occur?",
            why2="Why did the condition develop?",
            why3="Why was the condition not detected earlier?",
            why4="Why did the system allow this condition?",
            why5="Why did the root cause persist?",
            cause1="To be determined",
            cause2="To be determined",
            cause3="To be determined",
            cause4="To be determined",
            cause5="To be determined",
            root_cause="To be determined",
            equipment_factors="Equipment failure, maintenance issues, calibration problems",
            material_factors="Raw material quality issues, batch variations",
            process_factors="Process parameter changes, operator variations",
            environment_factors="Temperature, humidity, other environmental conditions",
            most_likely_root_cause="Based on the deviation pattern, the most likely root cause is equipment-related",
            confidence="0.75"
        )

        analysis = self.llm.generate(self.system_prompt, prompt)

        # Parse the LLM response to extract causes and recommendations
        possible_causes = self._parse_causes_from_analysis(analysis)
        recommended_actions = self._parse_actions_from_analysis(analysis)
        confidence = self._parse_confidence_from_analysis(analysis)

        return RootCauseReport(
            anomaly=anomaly,
            possible_causes=possible_causes,
            confidence=confidence,
            recommended_actions=recommended_actions,
        )

    def _parse_causes_from_analysis(self, analysis: str) -> List[str]:
        """Parse possible causes from the LLM analysis text.

        Args:
            analysis: LLM-generated analysis text

        Returns:
            List of possible causes
        """
        causes = []

        # Look for common patterns in the analysis
        if "equipment" in analysis.lower():
            causes.append("Equipment malfunction or degradation")
        if "material" in analysis.lower() or "raw" in analysis.lower():
            causes.append("Raw material quality issues")
        if "process" in analysis.lower() or "parameter" in analysis.lower():
            causes.append("Process parameter deviation")
        if "operator" in analysis.lower() or "human" in analysis.lower():
            causes.append("Operator error or variation")
        if "maintenance" in analysis.lower():
            causes.append("Inadequate maintenance")
        if "environment" in analysis.lower() or "temperature" in analysis.lower():
            causes.append("Environmental factors")

        # If no causes found, add a default
        if not causes:
            causes.append("Root cause to be determined through further analysis")

        return causes

    def _parse_actions_from_analysis(self, analysis: str) -> List[str]:
        """Parse recommended actions from the LLM analysis text.

        Args:
            analysis: LLM-generated analysis text

        Returns:
            List of recommended actions
        """
        actions = []

        # Look for common action patterns in the analysis
        if "inspect" in analysis.lower() or "check" in analysis.lower():
            actions.append("Inspect equipment and processes")
        if "maintenance" in analysis.lower():
            actions.append("Schedule maintenance review")
        if "quality" in analysis.lower():
            actions.append("Review quality control procedures")
        if "training" in analysis.lower():
            actions.append("Provide additional training")
        if "monitor" in analysis.lower() or "track" in analysis.lower():
            actions.append("Enhance monitoring and alerting")

        # Default actions if none found
        if not actions:
            actions.append("Investigate root cause further")
            actions.append("Implement corrective action plan")
            actions.append("Monitor for recurrence")

        return actions

    def _parse_confidence_from_analysis(self, analysis: str) -> float:
        """Parse confidence score from the LLM analysis text.

        Args:
            analysis: LLM-generated analysis text

        Returns:
            Confidence score between 0 and 1
        """
        import re

        # Look for confidence patterns like "Confidence: 0.75" or "confidence: 75%"
        patterns = [
            r"confidence[:\s]+0?\.\d+",
            r"confidence[:\s]+(\d+)%",
            r"(\d+)%\s+confidence",
        ]

        for pattern in patterns:
            match = re.search(pattern, analysis, re.IGNORECASE)
            if match:
                value_str = match.group(1) if match.lastindex else match.group(0).split()[-1]
                if "%" in value_str:
                    return float(value_str.replace("%", "")) / 100.0
                else:
                    return float(value_str)

        # Default confidence if not found
        return 0.75

    def generate_insight_report(
        self,
        query_result: QueryResult,
        anomalies: List[AnomalyPoint],
    ) -> InsightReport:
        """Generate a complete insight report combining query results and anomaly analysis.

        Args:
            query_result: QueryResult from executing a SQL query
            anomalies: List of AnomalyPoints detected in the data

        Returns:
            InsightReport with interpretation, root causes, and recommendations
        """
        # Generate interpretation of results
        interpretation = self.interpret_result(query_result)

        # Perform root cause analysis for each anomaly
        root_causes = []
        for anomaly in anomalies:
            root_cause = self.root_cause_analysis(anomaly)
            root_causes.append(root_cause)

        # Consolidate recommendations
        all_recommendations = []
        for rc in root_causes:
            all_recommendations.extend(rc.recommended_actions)

        # Remove duplicates while preserving order
        seen = set()
        unique_recommendations = []
        for rec in all_recommendations:
            if rec not in seen:
                seen.add(rec)
                unique_recommendations.append(rec)

        # Build findings summary
        findings = f"Analysis of {query_result.row_count} records. "
        if anomalies:
            findings += f"Found {len(anomalies)} anomalies. "
            high_severity = [a for a in anomalies if a.severity == SeverityLevel.HIGH or a.severity == SeverityLevel.CRITICAL]
            if high_severity:
                findings += f"{len(high_severity)} are high/critical severity. "

        # Generate the final report using LLM
        prompt = INSIGHT_REPORT_PROMPT.format(
            findings=findings,
            data_evidence=f"Query returned {query_result.row_count} rows in {query_result.execution_time:.3f}s",
            business_impact="Manufacturing performance and quality metrics",
            recommended_actions="\n".join([f"- {rec}" for rec in unique_recommendations[:5]]),
            executive_summary=interpretation[:500] if interpretation else "Analysis in progress",
            finding_title_1="Anomaly Detection",
            evidence_1=f"Detected {len(anomalies)} anomalies in the data",
            impact_1="Potential impact on production efficiency and quality",
            finding_title_2="Performance Analysis",
            evidence_2=f"Query executed in {query_result.execution_time:.3f}s",
            impact_2="Data-driven insights for decision making",
            finding_title_3="Recommendations",
            evidence_3=f"{len(unique_recommendations)} action items identified",
            impact_3="Improved operational efficiency through targeted actions",
            action_1=unique_recommendations[0] if len(unique_recommendations) > 0 else "Review processes",
            effect_1="Reduced anomalies",
            owner_1="Operations Manager",
            timeline_1="1-2 weeks",
            action_2=unique_recommendations[1] if len(unique_recommendations) > 1 else "Monitor metrics",
            effect_2="Improved visibility",
            owner_2="Data Analyst",
            timeline_2="1 week",
            action_3=unique_recommendations[2] if len(unique_recommendations) > 2 else "Schedule review",
            effect_3="Proactive management",
            owner_3="Shift Supervisor",
            timeline_3="Ongoing",
            metric_1="OEE",
            improvement_1="5-10%",
            metric_2="Defect Rate",
            improvement_2="10-15%",
            metric_3="Downtime",
            improvement_3="15-20%",
            risks_and_considerations="Monitor implementation progress and adjust as needed"
        )

        report_text = self.llm.generate(self.system_prompt, prompt)

        return InsightReport(
            query=query_result.sql,
            interpretation=interpretation,
            anomalies=anomalies,
            root_causes=root_causes,
            recommendations=unique_recommendations,
        )