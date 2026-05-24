"""Anomaly detection module for manufacturing data.

This module provides statistical anomaly detection capabilities for
identifying unusual patterns in manufacturing metrics like OEE, output
quantity, defect rates, etc.

Methods:
    - Z-score based detection (detect_statistical)
    - IQR-based detection (detect_iqr)
    - Rule-based detection with custom rules (detect_rule_based)
"""

import statistics
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, List, Optional, Union


@dataclass
class AnomalyPoint:
    """Represents a detected anomaly in the data.

    Attributes:
        timestamp: When the anomaly occurred
        metric: The metric name (e.g., "oee", "output_qty")
        value: The anomalous value
        expected_value: What was expected
        deviation: How much it deviated (percentage)
        severity: "low", "medium", "high", or "critical"
        description: Natural language description of the anomaly
    """

    timestamp: datetime
    metric: str
    value: float
    expected_value: float
    deviation: float
    severity: str
    description: str


class AnomalyDetector:
    """Detects anomalies in manufacturing data using statistical methods.

    Provides three detection methods:
        - Statistical (Z-score): Flags points where |z-score| > threshold
        - IQR-based: Flags points outside [Q1 - multiplier*IQR, Q3 + multiplier*IQR]
        - Rule-based: Evaluates custom rules like {"metric": "oee", "operator": "<", "threshold": 0.6}
    """

    def __init__(self, timestamp_generator: Optional[Callable[[int], datetime]] = None) -> None:
        """Initialize the AnomalyDetector.

        Args:
            timestamp_generator: Optional function that takes an index and returns a datetime.
                                 If not provided, uses epoch time (1970-01-01) with index as offset.
        """
        self.timestamp_generator = timestamp_generator

    def _get_timestamp(self, index: int) -> datetime:
        """Get timestamp for a given index.

        Args:
            index: The data point index

        Returns:
            datetime for the anomaly point
        """
        if self.timestamp_generator:
            return self.timestamp_generator(index)
        # Default: epoch + index hours
        return datetime(1970, 1, 1) + __import__("datetime").timedelta(hours=index)

    def _calculate_severity(self, z_score: float) -> str:
        """Calculate severity based on z-score.

        Severity levels:
            - 2-3 std dev = "medium"
            - >3 std dev = "high"
            - >4 std dev = "critical"

        Args:
            z_score: The absolute z-score value

        Returns:
            Severity level as string
        """
        abs_z = abs(z_score)
        if abs_z > 4:
            return "critical"
        elif abs_z > 3:
            return "high"
        elif abs_z > 2:
            return "medium"
        else:
            return "low"

    def detect_statistical(
        self, data: List[float], threshold: float = 2.0
    ) -> List[AnomalyPoint]:
        """Detect anomalies using Z-score method.

        Flags data points where |z-score| > threshold.

        Args:
            data: List of numerical values to analyze
            threshold: Z-score threshold (default 2.0). Points with |z-score| > threshold
                      are flagged as anomalies.

        Returns:
            List of AnomalyPoint objects representing detected anomalies
        """
        anomalies = []

        # Need at least 2 data points to compute std dev
        if len(data) < 2:
            return anomalies

        mean = statistics.mean(data)
        # Use population stdev for anomaly detection
        # Handle case where all values are identical (stdev = 0)
        try:
            stdev = statistics.pstdev(data)
        except statistics.StatisticsError:
            return anomalies

        # If stdev is 0, no anomalies can be detected (all values identical)
        if stdev == 0:
            return anomalies

        for index, value in enumerate(data):
            z_score = (value - mean) / stdev

            if abs(z_score) > threshold:
                deviation = abs((value - mean) / mean * 100) if mean != 0 else 0.0
                severity = self._calculate_severity(z_score)
                description = self._generate_description(
                    metric="value",
                    value=value,
                    expected_value=mean,
                    deviation=deviation,
                    severity=severity
                )
                anomalies.append(
                    AnomalyPoint(
                        timestamp=self._get_timestamp(index),
                        metric="value",
                        value=value,
                        expected_value=round(mean, 4),
                        deviation=round(deviation, 2),
                        severity=severity,
                        description=description
                    )
                )

        return anomalies

    def detect_iqr(
        self, data: List[float], multiplier: float = 1.5
    ) -> List[AnomalyPoint]:
        """Detect anomalies using IQR (Interquartile Range) method.

        Flags points outside [Q1 - multiplier*IQR, Q3 + multiplier*IQR].

        Args:
            data: List of numerical values to analyze
            multiplier: IQR multiplier (default 1.5). Standard outlier detection uses 1.5.

        Returns:
            List of AnomalyPoint objects representing detected anomalies
        """
        anomalies = []

        if len(data) < 4:
            # Need at least 4 points for quartiles
            return anomalies

        sorted_data = sorted(data)
        n = len(sorted_data)

        # Calculate Q1 and Q3 using linear interpolation
        # Q1 is median of lower half, Q3 is median of upper half
        if n % 4 == 0:
            q1_index = n // 4
            q3_index = 3 * n // 4
            q1 = (sorted_data[q1_index - 1] + sorted_data[q1_index]) / 2
            q3 = (sorted_data[q3_index - 1] + sorted_data[q3_index]) / 2
        else:
            # Use linear interpolation method
            q1_index = (n + 1) / 4
            q3_index = 3 * (n + 1) / 4

            # Interpolate Q1
            q1_lower = int(q1_index) - 1
            q1_upper = q1_lower + 1
            q1_frac = q1_index - int(q1_index)
            q1 = sorted_data[q1_lower] * (1 - q1_frac) + sorted_data[q1_upper] * q1_frac

            # Interpolate Q3
            q3_lower = int(q3_index) - 1
            q3_upper = q3_lower + 1
            q3_frac = q3_index - int(q3_index)
            q3 = sorted_data[q3_lower] * (1 - q3_frac) + sorted_data[q3_upper] * q3_frac

        iqr = q3 - q1
        lower_bound = q1 - multiplier * iqr
        upper_bound = q3 + multiplier * iqr

        # Median (Q2)
        median = statistics.median(data)

        for index, value in enumerate(data):
            if value < lower_bound or value > upper_bound:
                deviation = abs((value - median) / median * 100) if median != 0 else 0.0

                # Calculate z-score for severity
                if iqr > 0:
                    z_score = abs(value - median) / (iqr / 1.35)  # Convert IQR to std dev estimate
                else:
                    z_score = 0.0

                severity = self._calculate_severity(z_score)

                description = self._generate_description(
                    metric="value",
                    value=value,
                    expected_value=round(median, 4),
                    deviation=deviation,
                    severity=severity
                )

                anomalies.append(
                    AnomalyPoint(
                        timestamp=self._get_timestamp(index),
                        metric="value",
                        value=value,
                        expected_value=round(median, 4),
                        deviation=round(deviation, 2),
                        severity=severity,
                        description=description
                    )
                )

        return anomalies

    def detect_rule_based(
        self,
        values: dict[str, float],
        rules: Union[dict, list[dict]]
    ) -> List[AnomalyPoint]:
        """Detect anomalies using custom rules.

        Evaluates rules against metric values. Each rule should have:
            - "metric": the metric name to check
            - "operator": one of "<", ">", "<=", ">=", "==", "!="
            - "threshold": the threshold value to compare against

        Args:
            values: Dictionary of metric names to values
            rules: Single rule dict or list of rule dicts

        Returns:
            List of AnomalyPoint objects representing detected anomalies
        """
        anomalies = []

        # Normalize rules to list
        if isinstance(rules, dict):
            rules = [rules]

        for rule in rules:
            metric = rule.get("metric")
            operator = rule.get("operator")
            threshold = rule.get("threshold")

            if not all([metric, operator, threshold is not None]):
                continue

            if metric not in values:
                continue

            value = values[metric]
            violated = False

            if operator == "<":
                violated = value < threshold
            elif operator == ">":
                violated = value > threshold
            elif operator == "<=":
                violated = value <= threshold
            elif operator == ">=":
                violated = value >= threshold
            elif operator == "==":
                violated = value == threshold
            elif operator == "!=":
                violated = value != threshold

            if violated:
                # Calculate deviation percentage
                if threshold != 0:
                    deviation = abs((value - threshold) / threshold * 100)
                else:
                    deviation = abs(value * 100) if value != 0 else 0.0

                # Calculate severity based on deviation
                z_score = deviation / 25  # Rough mapping for rule-based
                severity = self._calculate_severity(z_score)

                description = self._generate_description(
                    metric=metric,
                    value=value,
                    expected_value=threshold,
                    deviation=deviation,
                    severity=severity
                )

                anomalies.append(
                    AnomalyPoint(
                        timestamp=datetime.now(),
                        metric=metric,
                        value=value,
                        expected_value=threshold,
                        deviation=round(deviation, 2),
                        severity=severity,
                        description=description
                    )
                )

        return anomalies

    def _generate_description(
        self,
        metric: str,
        value: float,
        expected_value: float,
        deviation: float,
        severity: str
    ) -> str:
        """Generate a natural language description of an anomaly.

        Args:
            metric: The metric name
            value: The anomalous value
            expected_value: The expected value
            deviation: Deviation percentage
            severity: Severity level

        Returns:
            Human-readable description string
        """
        direction = "above" if value > expected_value else "below"

        description = f"{metric} is {value} ({deviation:.1f}% {direction} expected value of {expected_value}). Severity: {severity}."

        return description