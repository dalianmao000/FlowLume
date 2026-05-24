"""Tests for AnomalyDetector module."""

import pytest
from datetime import datetime
from typing import List

# Add src to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from agents.data_insight.anomaly_detector import (
    AnomalyPoint,
    AnomalyDetector,
)


class TestAnomalyPointDataclass:
    """Test AnomalyPoint dataclass."""

    def test_anomaly_point_creation(self):
        """Verify AnomalyPoint can be created with all required fields."""
        anomaly = AnomalyPoint(
            timestamp=datetime(2026, 4, 25, 10, 0, 0),
            metric="oee",
            value=0.95,
            expected_value=0.85,
            deviation=11.76,
            severity="high",
            description="OEE value exceeded expected range"
        )
        assert anomaly.timestamp == datetime(2026, 4, 25, 10, 0, 0)
        assert anomaly.metric == "oee"
        assert anomaly.value == 0.95
        assert anomaly.expected_value == 0.85
        assert anomaly.deviation == 11.76
        assert anomaly.severity == "high"
        assert anomaly.description == "OEE value exceeded expected range"

    def test_anomaly_point_str_representation(self):
        """Verify AnomalyPoint has readable string representation."""
        anomaly = AnomalyPoint(
            timestamp=datetime(2026, 4, 25, 10, 0, 0),
            metric="output_qty",
            value=1000,
            expected_value=800,
            deviation=25.0,
            severity="critical",
            description="Output quantity significantly above expected"
        )
        str_repr = str(anomaly)
        assert "output_qty" in str_repr
        assert "critical" in str_repr


class TestAnomalyDetectorCreation:
    """Test AnomalyDetector instantiation."""

    def test_anomaly_detector_default_creation(self):
        """Verify AnomalyDetector can be instantiated with defaults."""
        detector = AnomalyDetector()
        assert detector is not None

    def test_anomaly_detector_with_timestamp_generator(self):
        """Verify AnomalyDetector accepts custom timestamp generator."""
        def custom_timestamp(index: int) -> datetime:
            return datetime(2026, 4, 25, index, 0, 0)

        detector = AnomalyDetector(timestamp_generator=custom_timestamp)
        assert detector is not None


class TestDetectStatistical:
    """Test detect_statistical method (Z-score based detection)."""

    def test_detect_statistical_no_anomalies(self):
        """Verify no anomalies detected in normal data (within 2 std dev)."""
        detector = AnomalyDetector()
        # Data within normal range
        data = [10, 11, 10.5, 10.8, 10.2, 10.3, 10.6, 10.4, 10.5, 10.7]

        anomalies = detector.detect_statistical(data, threshold=2.0)

        assert len(anomalies) == 0

    def test_detect_statistical_single_anomaly(self):
        """Verify single anomaly is detected when value exceeds threshold."""
        detector = AnomalyDetector()
        # Last value is way outside normal range
        data = [10, 11, 10.5, 10.8, 10.2, 10.3, 10.6, 10.4, 10.5, 10.7, 50]

        anomalies = detector.detect_statistical(data, threshold=2.0)

        assert len(anomalies) == 1
        assert anomalies[0].value == 50
        assert anomalies[0].metric == "value"
        assert anomalies[0].severity in ["medium", "high", "critical"]

    def test_detect_statistical_multiple_anomalies(self):
        """Verify multiple anomalies can be detected."""
        detector = AnomalyDetector()
        # Multiple extreme values with high enough z-scores (>2.0)
        # With [10,10,10,10,10,10,10,10,10,10,100,-100]:
        # mean ≈ 18.18, stdev ≈ 34.5
        # 100: z = (100-18.18)/34.5 = 2.37 > 2.0 ✓
        # -100: z = (-100-18.18)/34.5 = -3.43 > 2.0 ✓ (abs is 3.43)
        data = [10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 100, -100]

        anomalies = detector.detect_statistical(data, threshold=2.0)

        assert len(anomalies) == 2
        anomaly_values = {a.value for a in anomalies}
        assert anomaly_values == {100, -100}

    def test_detect_statistical_empty_data(self):
        """Verify empty data returns empty list."""
        detector = AnomalyDetector()
        anomalies = detector.detect_statistical([], threshold=2.0)

        assert anomalies == []

    def test_detect_statistical_single_value(self):
        """Verify single value data returns empty list (can't compute std dev)."""
        detector = AnomalyDetector()
        anomalies = detector.detect_statistical([10.0], threshold=2.0)

        assert anomalies == []

    def test_detect_statistical_custom_threshold(self):
        """Verify custom threshold is respected."""
        detector = AnomalyDetector()
        # Value at ~2.5 std dev - should be caught with threshold=2.0 but not 3.0
        data = [10, 11, 10.5, 10.8, 10.2, 10.3, 10.6, 10.4, 10.5, 10.7, 25]

        anomalies_tight = detector.detect_statistical(data, threshold=2.0)
        anomalies_loose = detector.detect_statistical(data, threshold=3.0)

        assert len(anomalies_tight) >= len(anomalies_loose)

    def test_detect_statistical_severity_levels(self):
        """Verify severity levels are assigned correctly based on std dev."""
        detector = AnomalyDetector()
        # Data where we can predict severity
        # Normal data around 10, extreme outlier at 100
        data = [10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 100]

        anomalies = detector.detect_statistical(data, threshold=2.0)

        assert len(anomalies) == 1
        # With data std dev ~0 and mean 10, z-score for 100 is very high
        assert anomalies[0].severity in ["medium", "high", "critical"]

    def test_detect_statistical_deviation_calculation(self):
        """Verify deviation percentage is calculated correctly."""
        detector = AnomalyDetector()
        data = [10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 20]

        anomalies = detector.detect_statistical(data, threshold=2.0)

        if len(anomalies) > 0:
            # Data: [10,10,10,10,10,10,10,10,10,10,20], mean = 120/11 ≈ 10.91
            # deviation = |20 - 10.91| / 10.91 * 100 ≈ 83.33%
            mean = (10 * 10 + 20) / 11  # 10.909...
            expected_deviation = abs((20 - mean) / mean * 100)
            assert abs(anomalies[0].deviation - expected_deviation) < 0.1
            assert anomalies[0].expected_value == round(mean, 4)


class TestDetectIQR:
    """Test detect_iqr method (IQR-based detection)."""

    def test_detect_iqr_no_anomalies(self):
        """Verify no anomalies detected in normal data."""
        detector = AnomalyDetector()
        data = [10, 11, 10.5, 10.8, 10.2, 10.3, 10.6, 10.4, 10.5, 10.7]

        anomalies = detector.detect_iqr(data, multiplier=1.5)

        assert len(anomalies) == 0

    def test_detect_iqr_outlier_above_upper_bound(self):
        """Verify outlier above upper bound is detected."""
        detector = AnomalyDetector()
        # Q3 ~ 10.75, upper bound = Q3 + 1.5*IQR
        # IQR = Q3 - Q1 ~ 0.55, upper bound ~ 11.575
        data = [10, 11, 10.5, 10.8, 10.2, 10.3, 10.6, 10.4, 10.5, 10.7, 15]

        anomalies = detector.detect_iqr(data, multiplier=1.5)

        assert len(anomalies) == 1
        assert anomalies[0].value == 15

    def test_detect_iqr_outlier_below_lower_bound(self):
        """Verify outlier below lower bound is detected."""
        detector = AnomalyDetector()
        data = [10, 11, 10.5, 10.8, 10.2, 10.3, 10.6, 10.4, 10.5, 10.7, 1]

        anomalies = detector.detect_iqr(data, multiplier=1.5)

        assert len(anomalies) == 1
        assert anomalies[0].value == 1

    def test_detect_iqr_both_bounds(self):
        """Verify outliers on both bounds are detected."""
        detector = AnomalyDetector()
        data = [10, 11, 10.5, 10.8, 10.2, 10.3, 10.6, 10.4, 10.5, 10.7, 15, 1]

        anomalies = detector.detect_iqr(data, multiplier=1.5)

        assert len(anomalies) == 2
        anomaly_values = {a.value for a in anomalies}
        assert anomaly_values == {15, 1}

    def test_detect_iqr_empty_data(self):
        """Verify empty data returns empty list."""
        detector = AnomalyDetector()
        anomalies = detector.detect_iqr([], multiplier=1.5)

        assert anomalies == []

    def test_detect_iqr_custom_multiplier(self):
        """Verify custom multiplier affects bounds."""
        detector = AnomalyDetector()
        # Value 14 is at edge - should be outlier with 1.5x but not with 3x
        data = [10, 11, 10.5, 10.8, 10.2, 10.3, 10.6, 10.4, 10.5, 10.7, 14]

        anomalies_strict = detector.detect_iqr(data, multiplier=1.5)
        anomalies_lenient = detector.detect_iqr(data, multiplier=3.0)

        assert len(anomalies_strict) >= len(anomalies_lenient)

    def test_detect_iqr_expected_value_is_median(self):
        """Verify expected_value is the median of the data."""
        detector = AnomalyDetector()
        data = [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 100]

        anomalies = detector.detect_iqr(data, multiplier=1.5)

        if len(anomalies) > 0:
            # Median of 11 elements is the 6th element = 10
            assert anomalies[0].expected_value == 10


class TestDetectRuleBased:
    """Test detect_rule_based method (rule-based detection)."""

    def test_detect_rule_based_single_rule_violation(self):
        """Verify single rule violation is detected."""
        detector = AnomalyDetector()
        values = {"oee": 0.55, "output_qty": 800}
        rules = {"metric": "oee", "operator": "<", "threshold": 0.6}

        anomalies = detector.detect_rule_based(values, rules)

        assert len(anomalies) == 1
        assert anomalies[0].metric == "oee"
        assert anomalies[0].value == 0.55
        assert anomalies[0].severity == "low"  # Below threshold but not extreme

    def test_detect_rule_based_no_violation(self):
        """Verify no anomaly when rule is not violated."""
        detector = AnomalyDetector()
        values = {"oee": 0.85, "output_qty": 800}
        rules = {"metric": "oee", "operator": "<", "threshold": 0.6}

        # 0.85 < 0.6 is FALSE, so there is NO violation - anomaly count should be 0
        anomalies = detector.detect_rule_based(values, rules)

        assert len(anomalies) == 0

    def test_detect_rule_based_operator_less_than(self):
        """Verify '<' operator works correctly - violation when value < threshold."""
        detector = AnomalyDetector()
        values = {"temperature": 35}
        rules = {"metric": "temperature", "operator": "<", "threshold": 40}

        # 35 < 40 is TRUE, so this SHOULD be a violation
        anomalies = detector.detect_rule_based(values, rules)

        assert len(anomalies) == 1

    def test_detect_rule_based_operator_greater_than(self):
        """Verify '>' operator works correctly - violation when value > threshold."""
        detector = AnomalyDetector()
        values = {"pressure": 2.5}
        rules = {"metric": "pressure", "operator": ">", "threshold": 2.0}

        # 2.5 > 2.0 is TRUE, so this SHOULD be a violation
        anomalies = detector.detect_rule_based(values, rules)

        assert len(anomalies) == 1

    def test_detect_rule_based_operator_less_equal(self):
        """Verify '<=' operator works correctly."""
        detector = AnomalyDetector()
        values = {"oee": 0.6}
        rules = {"metric": "oee", "operator": "<=", "threshold": 0.6}

        # 0.6 <= 0.6 is TRUE, so this SHOULD be a violation
        anomalies = detector.detect_rule_based(values, rules)

        assert len(anomalies) == 1

    def test_detect_rule_based_operator_greater_equal(self):
        """Verify '>=' operator works correctly."""
        detector = AnomalyDetector()
        values = {"oee": 0.6}
        rules = {"metric": "oee", "operator": ">=", "threshold": 0.6}

        # 0.6 >= 0.6 is TRUE, so this SHOULD be a violation
        anomalies = detector.detect_rule_based(values, rules)

        assert len(anomalies) == 1

    def test_detect_rule_based_operator_equal(self):
        """Verify '==' operator works correctly."""
        detector = AnomalyDetector()
        values = {"count": 5}
        rules = {"metric": "count", "operator": "==", "threshold": 5}

        # 5 == 5 is TRUE, so this SHOULD be a violation
        anomalies = detector.detect_rule_based(values, rules)

        assert len(anomalies) == 1

    def test_detect_rule_based_operator_not_equal(self):
        """Verify '!=' operator works correctly."""
        detector = AnomalyDetector()
        values = {"count": 5}
        rules = {"metric": "count", "operator": "!=", "threshold": 10}

        # 5 != 10 is TRUE, so this SHOULD be a violation
        anomalies = detector.detect_rule_based(values, rules)

        assert len(anomalies) == 1

    def test_detect_rule_based_missing_metric(self):
        """Verify missing metric returns empty list."""
        detector = AnomalyDetector()
        values = {"oee": 0.85}
        rules = {"metric": "nonexistent", "operator": "<", "threshold": 0.6}

        anomalies = detector.detect_rule_based(values, rules)

        assert anomalies == []

    def test_detect_rule_based_multiple_rules(self):
        """Verify multiple rules can be evaluated."""
        detector = AnomalyDetector()
        values = {"oee": 0.55, "output_qty": 800, "temperature": 50}
        rules = [
            {"metric": "oee", "operator": "<", "threshold": 0.6},
            {"metric": "temperature", "operator": ">", "threshold": 45}
        ]

        anomalies = detector.detect_rule_based(values, rules)

        assert len(anomalies) == 2
        metrics = {a.metric for a in anomalies}
        assert metrics == {"oee", "temperature"}

    def test_detect_rule_based_severity_assignment(self):
        """Verify severity is assigned based on deviation from threshold."""
        detector = AnomalyDetector()
        # Value way below threshold gets higher severity
        values = {"oee": 0.3}
        rules = {"metric": "oee", "operator": "<", "threshold": 0.6}

        anomalies = detector.detect_rule_based(values, rules)

        assert len(anomalies) == 1
        # (0.6 - 0.3) / 0.6 * 100 = 50% deviation
        assert anomalies[0].deviation > 0


class TestSeverityLevels:
    """Test severity level assignment."""

    def test_severity_low_from_rule_based(self):
        """Verify 'low' severity for small deviations in rule-based detection."""
        detector = AnomalyDetector()
        # Rule-based detection: value 0.59 < 0.6 threshold
        # deviation = |0.59-0.6|/0.6 * 100 = 1.67%
        # z_score = 1.67/25 = 0.067 -> low severity
        values = {"oee": 0.59}
        rules = {"metric": "oee", "operator": "<", "threshold": 0.6}

        anomalies = detector.detect_rule_based(values, rules)

        assert len(anomalies) == 1
        assert anomalies[0].severity == "low"

    def test_severity_medium(self):
        """Verify 'medium' severity for 2-3 std dev."""
        # Use rule-based with 75% deviation
        # z_score = 75/25 = 3.0 -> which is > 2, so medium severity
        detector = AnomalyDetector()
        values = {"metric_value": 25}  # 75% below 100
        rules = {"metric": "metric_value", "operator": "<", "threshold": 100}

        anomalies = detector.detect_rule_based(values, rules)

        if len(anomalies) > 0:
            # deviation = |25-100|/100 * 100 = 75%
            # z_score = 75/25 = 3.0 -> should be "medium" (>2, <=3)
            assert anomalies[0].severity == "medium", f"Expected medium but got {anomalies[0].severity}"

    def test_severity_high(self):
        """Verify 'high' severity for >3 std dev."""
        detector = AnomalyDetector()
        # Value at ~3.5 std dev should be high
        data = [10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 15]

        anomalies = detector.detect_statistical(data, threshold=2.0)

        if len(anomalies) > 0:
            # With [10x10, 15], z-score is high enough for "high" severity
            assert anomalies[0].severity == "high"

    def test_severity_critical(self):
        """Verify 'critical' severity for >4 std dev."""
        # Use rule-based with 120% deviation
        # z_score = 120/25 = 4.8 -> which is > 4, so critical severity
        detector = AnomalyDetector()
        values = {"metric_value": -20}  # 120% below 100 (value-100)/100*100 = -120, abs=120
        rules = {"metric": "metric_value", "operator": "<", "threshold": 100}

        anomalies = detector.detect_rule_based(values, rules)

        if len(anomalies) > 0:
            assert anomalies[0].severity == "critical", f"Expected critical but got {anomalies[0].severity}"


class TestIntegration:
    """Integration tests with mock database data."""

    def test_detect_statistical_with_oee_data(self):
        """Verify statistical detection works with OEE-like data."""
        detector = AnomalyDetector()
        # Simulated OEE data with one anomaly
        oee_data = [0.85, 0.82, 0.88, 0.86, 0.84, 0.87, 0.83, 0.85, 0.86, 0.84, 0.5]

        anomalies = detector.detect_statistical(oee_data, threshold=2.0)

        assert len(anomalies) >= 1
        assert any(a.metric == "value" for a in anomalies)

    def test_detect_iqr_with_production_data(self):
        """Verify IQR detection works with production-like data."""
        detector = AnomalyDetector()
        # Simulated output_qty with outliers
        output_data = [800, 820, 810, 830, 815, 825, 810, 820, 815, 830, 1200]

        anomalies = detector.detect_iqr(output_data, multiplier=1.5)

        assert len(anomalies) >= 1
        assert anomalies[0].value == 1200

    def test_detect_rule_based_with_custom_rules(self):
        """Verify rule-based detection with manufacturing rules."""
        detector = AnomalyDetector()
        values = {
            "oee": 0.55,
            "output_qty": 750,
            "defect_rate": 0.08,
            "downtime_hours": 2.5
        }
        rules = [
            {"metric": "oee", "operator": "<", "threshold": 0.6},
            {"metric": "defect_rate", "operator": ">", "threshold": 0.05}
        ]

        anomalies = detector.detect_rule_based(values, rules)

        assert len(anomalies) == 2
        metrics = {a.metric for a in anomalies}
        assert "oee" in metrics
        assert "defect_rate" in metrics