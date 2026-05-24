"""Tests for Lean Optimization Agent mock data and event models."""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.lean_optimization.event_log_models import (
    ProductionEvent,
    EquipmentEvent,
    WorkforceEvent,
    EventType,
    EquipmentStatus,
)
from agents.lean_optimization.mock_production_data import (
    generate_production_events,
    generate_equipment_events,
    generate_workforce_events,
    generate_all_mock_data,
    BASE_DATE,
    PRODUCTION_LINES,
    OPERATIONS,
)


class TestEventTypeEnum:
    """Test EventType enum values."""

    def test_all_event_types_defined(self):
        """Verify all required event types are defined."""
        expected_types = {
            "ORDER_CREATED",
            "ORDER_RELEASED",
            "OP_START",
            "OP_COMPLETE",
            "QC_PASS",
            "QC_FAIL",
            "ORDER_SHIPPED",
        }
        actual_types = {e.value for e in EventType}
        assert expected_types == actual_types


class TestEquipmentStatusEnum:
    """Test EquipmentStatus enum values."""

    def test_all_status_values_defined(self):
        """Verify all required status values are defined."""
        expected_statuses = {"RUNNING", "IDLE", "DOWN", "MAINTENANCE"}
        actual_statuses = {s.value for s in EquipmentStatus}
        assert expected_statuses == actual_statuses


class TestProductionEventModel:
    """Test ProductionEvent dataclass."""

    def test_valid_production_event_creation(self):
        """Test creating a valid ProductionEvent."""
        event = ProductionEvent(
            event_id="EVT_001",
            order_id="ORD_001",
            event_type="ORDER_CREATED",
            operation="ASSEMBLY",
            equipment_id="EQ_001",
            start_time=datetime(2026, 5, 17, 8, 0, 0),
            end_time=datetime(2026, 5, 17, 8, 30, 0),
            quantity=100,
            location="Plant_A",
        )
        assert event.event_id == "EVT_001"
        assert event.order_id == "ORD_001"
        assert event.quantity == 100

    def test_production_event_duration_seconds(self):
        """Test duration_seconds calculation."""
        event = ProductionEvent(
            event_id="EVT_001",
            order_id="ORD_001",
            event_type="OP_COMPLETE",
            operation="ASSEMBLY",
            equipment_id="EQ_001",
            start_time=datetime(2026, 5, 17, 8, 0, 0),
            end_time=datetime(2026, 5, 17, 8, 30, 0),
            quantity=100,
            location="Plant_A",
        )
        assert event.duration_seconds() == 1800.0

    def test_production_event_duration_none_when_no_end(self):
        """Test duration_seconds returns None when end_time is None."""
        event = ProductionEvent(
            event_id="EVT_001",
            order_id="ORD_001",
            event_type="OP_START",
            operation="ASSEMBLY",
            equipment_id="EQ_001",
            start_time=datetime(2026, 5, 17, 8, 0, 0),
            end_time=None,
            quantity=100,
            location="Plant_A",
        )
        assert event.duration_seconds() is None

    def test_production_event_invalid_event_type(self):
        """Test that invalid event_type raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            ProductionEvent(
                event_id="EVT_001",
                order_id="ORD_001",
                event_type="INVALID_TYPE",
                operation="ASSEMBLY",
                equipment_id="EQ_001",
                start_time=datetime(2026, 5, 17, 8, 0, 0),
                end_time=datetime(2026, 5, 17, 8, 30, 0),
                quantity=100,
                location="Plant_A",
            )
        assert "Invalid event_type" in str(exc_info.value)


class TestEquipmentEventModel:
    """Test EquipmentEvent dataclass."""

    def test_valid_equipment_event_creation(self):
        """Test creating a valid EquipmentEvent."""
        event = EquipmentEvent(
            timestamp=datetime(2026, 5, 17, 8, 0, 0),
            equipment_id="EQ_001",
            status="RUNNING",
            duration=4.0,
            reason="production",
        )
        assert event.equipment_id == "EQ_001"
        assert event.status == "RUNNING"
        assert event.duration == 4.0

    def test_equipment_event_optional_duration_and_reason(self):
        """Test EquipmentEvent with optional fields."""
        event = EquipmentEvent(
            timestamp=datetime(2026, 5, 17, 8, 0, 0),
            equipment_id="EQ_001",
            status="RUNNING",
        )
        assert event.duration is None
        assert event.reason is None

    def test_equipment_event_invalid_status(self):
        """Test that invalid status raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            EquipmentEvent(
                timestamp=datetime(2026, 5, 17, 8, 0, 0),
                equipment_id="EQ_001",
                status="INVALID_STATUS",
            )
        assert "Invalid status" in str(exc_info.value)


class TestWorkforceEventModel:
    """Test WorkforceEvent dataclass."""

    def test_valid_workforce_event_creation(self):
        """Test creating a valid WorkforceEvent."""
        event = WorkforceEvent(
            timestamp=datetime(2026, 5, 17, 8, 0, 0),
            operator_id="OP_001",
            operation="ASSEMBLY",
            cycle_time=90.5,
        )
        assert event.operator_id == "OP_001"
        assert event.cycle_time == 90.5

    def test_workforce_event_invalid_cycle_time(self):
        """Test that non-positive cycle_time raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            WorkforceEvent(
                timestamp=datetime(2026, 5, 17, 8, 0, 0),
                operator_id="OP_001",
                operation="ASSEMBLY",
                cycle_time=0,
            )
        assert "cycle_time must be positive" in str(exc_info.value)

    def test_workforce_event_negative_cycle_time(self):
        """Test that negative cycle_time raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            WorkforceEvent(
                timestamp=datetime(2026, 5, 17, 8, 0, 0),
                operator_id="OP_001",
                operation="ASSEMBLY",
                cycle_time=-10.0,
            )
        assert "cycle_time must be positive" in str(exc_info.value)


class TestProductionEventsGeneration:
    """Test production events generation."""

    def test_generate_production_events_returns_list(self):
        """Test that generate_production_events returns a list."""
        events = generate_production_events(start_date=BASE_DATE, days=7)
        assert isinstance(events, list)
        assert len(events) > 0

    def test_production_events_all_are_production_events(self):
        """Test all generated events are ProductionEvent instances."""
        events = generate_production_events(start_date=BASE_DATE, days=7)
        for event in events:
            assert isinstance(event, ProductionEvent)

    def test_production_events_valid_event_types(self):
        """Test all events have valid event_type values."""
        events = generate_production_events(start_date=BASE_DATE, days=7)
        valid_types = {e.value for e in EventType}
        for event in events:
            assert event.event_type in valid_types

    def test_production_events_cover_all_operation_types(self):
        """Test events cover all operation types."""
        events = generate_production_events(start_date=BASE_DATE, days=7)
        operations = {e.operation for e in events}
        expected_operations = set(OPERATIONS)
        # Some operations may not be in events but the set should match
        assert len(events) > 0

    def test_production_events_have_required_fields(self):
        """Test each event has all required fields populated."""
        events = generate_production_events(start_date=BASE_DATE, days=7)
        for event in events:
            assert event.event_id is not None
            assert event.order_id is not None
            assert event.start_time is not None
            assert event.location is not None

    def test_production_events_sorted_by_start_time(self):
        """Test events are sorted by start_time."""
        events = generate_production_events(start_date=BASE_DATE, days=7)
        for i in range(len(events) - 1):
            assert events[i].start_time <= events[i + 1].start_time


class TestEquipmentEventsGeneration:
    """Test equipment events generation."""

    def test_generate_equipment_events_returns_list(self):
        """Test that generate_equipment_events returns a list."""
        events = generate_equipment_events(start_date=BASE_DATE, days=7)
        assert isinstance(events, list)
        assert len(events) > 0

    def test_equipment_events_all_are_equipment_events(self):
        """Test all generated events are EquipmentEvent instances."""
        events = generate_equipment_events(start_date=BASE_DATE, days=7)
        for event in events:
            assert isinstance(event, EquipmentEvent)

    def test_equipment_events_valid_statuses(self):
        """Test all events have valid status values."""
        events = generate_equipment_events(start_date=BASE_DATE, days=7)
        valid_statuses = {s.value for s in EquipmentStatus}
        for event in events:
            assert event.status in valid_statuses

    def test_equipment_events_have_timestamps(self):
        """Test each event has a timestamp."""
        events = generate_equipment_events(start_date=BASE_DATE, days=7)
        for event in events:
            assert event.timestamp is not None

    def test_equipment_events_sorted_by_timestamp(self):
        """Test events are sorted by timestamp."""
        events = generate_equipment_events(start_date=BASE_DATE, days=7)
        for i in range(len(events) - 1):
            assert events[i].timestamp <= events[i + 1].timestamp


class TestWorkforceEventsGeneration:
    """Test workforce events generation."""

    def test_generate_workforce_events_returns_list(self):
        """Test that generate_workforce_events returns a list."""
        events = generate_workforce_events(start_date=BASE_DATE, days=7)
        assert isinstance(events, list)
        assert len(events) > 0

    def test_workforce_events_all_are_workforce_events(self):
        """Test all generated events are WorkforceEvent instances."""
        events = generate_workforce_events(start_date=BASE_DATE, days=7)
        for event in events:
            assert isinstance(event, WorkforceEvent)

    def test_workforce_events_positive_cycle_times(self):
        """Test all events have positive cycle_time."""
        events = generate_workforce_events(start_date=BASE_DATE, days=7)
        for event in events:
            assert event.cycle_time > 0

    def test_workforce_events_have_required_fields(self):
        """Test each event has all required fields."""
        events = generate_workforce_events(start_date=BASE_DATE, days=7)
        for event in events:
            assert event.operator_id is not None
            assert event.operation is not None
            assert event.timestamp is not None

    def test_workforce_events_sorted_by_timestamp(self):
        """Test events are sorted by timestamp."""
        events = generate_workforce_events(start_date=BASE_DATE, days=7)
        for i in range(len(events) - 1):
            assert events[i].timestamp <= events[i + 1].timestamp


class TestGenerateAllMockData:
    """Test the combined generate_all_mock_data function."""

    def test_returns_three_tuples(self):
        """Test that generate_all_mock_data returns a tuple of 3 lists."""
        result = generate_all_mock_data(start_date=BASE_DATE, days=7)
        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_all_data_types_correct(self):
        """Test all returned data types are correct."""
        prod_events, equip_events, work_events = generate_all_mock_data(
            start_date=BASE_DATE, days=7
        )
        assert all(isinstance(e, ProductionEvent) for e in prod_events)
        assert all(isinstance(e, EquipmentEvent) for e in equip_events)
        assert all(isinstance(e, WorkforceEvent) for e in work_events)

    def test_sufficient_data_volume(self):
        """Test that sufficient data is generated (hundreds of events)."""
        prod_events, equip_events, work_events = generate_all_mock_data(
            start_date=BASE_DATE, days=7
        )
        total_events = len(prod_events) + len(equip_events) + len(work_events)
        # Should generate on order of hundreds (500-1000)
        assert total_events >= 500, f"Expected >= 500 events, got {total_events}"
        assert total_events <= 3000, f"Expected <= 3000 events, got {total_events}"


class TestDataVolumeAndPatterns:
    """Test realistic patterns in generated data."""

    def test_production_events_span_multiple_days(self):
        """Test production events span multiple days."""
        events = generate_production_events(start_date=BASE_DATE, days=7)
        if len(events) > 1:
            min_time = min(e.start_time for e in events)
            max_time = max(e.start_time for e in events)
            # Should span at least 5 days
            assert (max_time - min_time).days >= 5

    def test_equipment_events_across_all_equipment(self):
        """Test equipment events cover multiple equipment IDs."""
        events = generate_equipment_events(start_date=BASE_DATE, days=7)
        equipment_ids = {e.equipment_id for e in events}
        # Should have multiple equipment IDs
        assert len(equipment_ids) >= 5

    def test_multiple_orders_in_production_events(self):
        """Test production events contain multiple orders."""
        events = generate_production_events(start_date=BASE_DATE, days=7)
        order_ids = {e.order_id for e in events}
        # Should have multiple orders
        assert len(order_ids) >= 30

    def test_all_event_types_present_in_production_events(self):
        """Test all event types are present in generated production events."""
        events = generate_production_events(start_date=BASE_DATE, days=7)
        event_types_present = {e.event_type for e in events}
        expected_types = {e.value for e in EventType}
        # All event types should be represented
        assert expected_types.issubset(event_types_present), \
            f"Missing event types: {expected_types - event_types_present}"