"""Tests for VSM Calculator module."""

import pytest
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.lean_optimization.event_log_models import ProductionEvent, WorkforceEvent, EventType
from agents.lean_optimization.mock_production_data import (
    generate_production_events,
    generate_workforce_events,
    BASE_DATE,
)
from agents.lean_optimization.vsm_calculator import (
    ProcessStep,
    VSMData,
    VSMCalculator,
)


class TestProcessStepDataclass:
    """Test ProcessStep dataclass."""

    def test_create_process_step(self):
        """Test creating a valid ProcessStep."""
        step = ProcessStep(
            name="CUTTING",
            va_time=3600.0,
            nva_time=600.0,
            wait_time=1800.0,
            inventory=50,
            takt_time=30.0,
        )
        assert step.name == "CUTTING"
        assert step.va_time == 3600.0
        assert step.nva_time == 600.0
        assert step.wait_time == 1800.0
        assert step.inventory == 50
        assert step.takt_time == 30.0

    def test_process_step_defaults(self):
        """Test ProcessStep with default values."""
        step = ProcessStep(name="WELDING")
        assert step.name == "WELDING"
        assert step.va_time == 0.0
        assert step.nva_time == 0.0
        assert step.wait_time == 0.0
        assert step.inventory == 0
        assert step.takt_time == 0.0


class TestVSMDataDataclass:
    """Test VSMData dataclass."""

    def test_create_vsm_data(self):
        """Test creating a valid VSMData."""
        steps = [
            ProcessStep(name="CUTTING", va_time=3600.0),
            ProcessStep(name="WELDING", va_time=1800.0),
        ]
        data = VSMData(
            process_steps=steps,
            total_va_time=5400.0,
            total_nva_time=1200.0,
            total_lead_time=7200.0,
            inventory_positions={"CUTTING": 50, "WELDING": 30},
            takt_time=30.0,
        )
        assert len(data.process_steps) == 2
        assert data.total_va_time == 5400.0
        assert data.total_nva_time == 1200.0
        assert data.total_lead_time == 7200.0
        assert data.inventory_positions == {"CUTTING": 50, "WELDING": 30}
        assert data.takt_time == 30.0


class TestVSMCalculatorTaktTime:
    """Test VSMCalculator takt time calculation."""

    def test_calculate_takt_time_normal(self):
        """Test takt time calculation with normal parameters."""
        calc = VSMCalculator()
        # 8 hours available time, 480 units demand -> 60 seconds per unit
        takt = calc.calculate_takt_time(available_time=28800.0, demand=480)
        assert takt == 60.0

    def test_calculate_takt_time_zero_demand(self):
        """Test takt time with zero demand raises error."""
        calc = VSMCalculator()
        with pytest.raises(ValueError) as exc_info:
            calc.calculate_takt_time(available_time=28800.0, demand=0)
        assert "demand must be positive" in str(exc_info.value)

    def test_calculate_takt_time_negative_demand(self):
        """Test takt time with negative demand raises error."""
        calc = VSMCalculator()
        with pytest.raises(ValueError) as exc_info:
            calc.calculate_takt_time(available_time=28800.0, demand=-10)
        assert "demand must be positive" in str(exc_info.value)

    def test_calculate_takt_time_float_inputs(self):
        """Test takt time calculation with float inputs."""
        calc = VSMCalculator()
        # 8.5 hours = 30600 seconds, 500 units demand -> 61.2 seconds per unit
        takt = calc.calculate_takt_time(available_time=30600.0, demand=500)
        assert takt == 61.2


class TestVSMCalculatorIdentifyProcessSteps:
    """Test VSMCalculator process step identification."""

    def test_identify_process_steps_simple(self):
        """Test identifying process steps from simple events."""
        calc = VSMCalculator()
        events = [
            ProductionEvent(
                event_id="EVT001",
                order_id="ORD001",
                event_type="OP_START",
                operation="CUTTING",
                equipment_id="EQ-001",
                start_time=datetime(2026, 5, 17, 8, 0, 0),
                end_time=None,
                quantity=100,
                location="STATION-1",
            ),
            ProductionEvent(
                event_id="EVT002",
                order_id="ORD001",
                event_type="OP_COMPLETE",
                operation="CUTTING",
                equipment_id="EQ-001",
                start_time=datetime(2026, 5, 17, 8, 0, 0),
                end_time=datetime(2026, 5, 17, 9, 0, 0),
                quantity=100,
                location="STATION-1",
            ),
            ProductionEvent(
                event_id="EVT003",
                order_id="ORD001",
                event_type="OP_START",
                operation="WELDING",
                equipment_id="EQ-002",
                start_time=datetime(2026, 5, 17, 9, 30, 0),
                end_time=None,
                quantity=100,
                location="STATION-2",
            ),
            ProductionEvent(
                event_id="EVT004",
                order_id="ORD001",
                event_type="OP_COMPLETE",
                operation="WELDING",
                equipment_id="EQ-002",
                start_time=datetime(2026, 5, 17, 9, 30, 0),
                end_time=datetime(2026, 5, 17, 11, 0, 0),
                quantity=100,
                location="STATION-2",
            ),
        ]
        steps = calc.identify_process_steps(events)
        assert len(steps) == 2
        # CUTTING: 1 hour VA
        assert steps[0].name == "CUTTING"
        assert steps[0].va_time == 3600.0
        # WELDING: 1.5 hours VA
        assert steps[1].name == "WELDING"
        assert steps[1].va_time == 5400.0

    def test_identify_process_steps_empty(self):
        """Test with empty event list."""
        calc = VSMCalculator()
        steps = calc.identify_process_steps([])
        assert len(steps) == 0

    def test_identify_process_steps_calculates_wait_time(self):
        """Test that wait time between operations is calculated."""
        calc = VSMCalculator()
        events = [
            ProductionEvent(
                event_id="EVT001",
                order_id="ORD001",
                event_type="OP_COMPLETE",
                operation="CUTTING",
                equipment_id="EQ-001",
                start_time=datetime(2026, 5, 17, 8, 0, 0),
                end_time=datetime(2026, 5, 17, 9, 0, 0),
                quantity=100,
                location="STATION-1",
            ),
            ProductionEvent(
                event_id="EVT002",
                order_id="ORD001",
                event_type="OP_START",
                operation="WELDING",
                equipment_id="EQ-002",
                start_time=datetime(2026, 5, 17, 10, 0, 0),  # 1 hour wait after CUTTING
                end_time=None,
                quantity=100,
                location="STATION-2",
            ),
            ProductionEvent(
                event_id="EVT003",
                order_id="ORD001",
                event_type="OP_COMPLETE",
                operation="WELDING",
                equipment_id="EQ-002",
                start_time=datetime(2026, 5, 17, 10, 0, 0),
                end_time=datetime(2026, 5, 17, 11, 0, 0),
                quantity=100,
                location="STATION-2",
            ),
        ]
        steps = calc.identify_process_steps(events)
        assert len(steps) == 2
        # WELDING has 1 hour wait before it
        assert steps[1].wait_time == 3600.0

    def test_identify_process_steps_inventory_tracking(self):
        """Test that WIP inventory is tracked at each step."""
        calc = VSMCalculator()
        events = [
            ProductionEvent(
                event_id="EVT001",
                order_id="ORD001",
                event_type="OP_COMPLETE",
                operation="CUTTING",
                equipment_id="EQ-001",
                start_time=datetime(2026, 5, 17, 8, 0, 0),
                end_time=datetime(2026, 5, 17, 9, 0, 0),
                quantity=50,
                location="STATION-1",
            ),
            ProductionEvent(
                event_id="EVT002",
                order_id="ORD001",
                event_type="OP_COMPLETE",
                operation="WELDING",
                equipment_id="EQ-002",
                start_time=datetime(2026, 5, 17, 10, 0, 0),
                end_time=datetime(2026, 5, 17, 11, 0, 0),
                quantity=40,  # Some may have failed QC
                location="STATION-2",
            ),
        ]
        steps = calc.identify_process_steps(events)
        assert len(steps) == 2
        # Inventory is tracked as cumulative WIP after each step
        assert steps[0].inventory == 50  # After CUTTING
        assert steps[1].inventory == 40  # After WELDING


class TestVSMCalculatorCalculateFromEvents:
    """Test VSMCalculator main calculation method."""

    def test_calculate_from_events_basic(self):
        """Test basic VSM calculation from production events."""
        calc = VSMCalculator()
        events = [
            ProductionEvent(
                event_id="EVT001",
                order_id="ORD001",
                event_type="OP_COMPLETE",
                operation="CUTTING",
                equipment_id="EQ-001",
                start_time=datetime(2026, 5, 17, 8, 0, 0),
                end_time=datetime(2026, 5, 17, 9, 0, 0),
                quantity=100,
                location="STATION-1",
            ),
            ProductionEvent(
                event_id="EVT002",
                order_id="ORD001",
                event_type="OP_COMPLETE",
                operation="WELDING",
                equipment_id="EQ-002",
                start_time=datetime(2026, 5, 17, 10, 0, 0),
                end_time=datetime(2026, 5, 17, 11, 30, 0),
                quantity=100,
                location="STATION-2",
            ),
        ]
        workforce_events = []  # Not needed for basic calculation

        vsm_data = calc.calculate_from_events(events, workforce_events)

        assert isinstance(vsm_data, VSMData)
        assert len(vsm_data.process_steps) == 2
        assert vsm_data.total_va_time > 0
        # Lead time includes VA + NVA + wait times
        assert vsm_data.total_lead_time >= vsm_data.total_va_time

    def test_calculate_from_events_with_takt_time(self):
        """Test VSM calculation includes takt time."""
        calc = VSMCalculator()
        events = [
            ProductionEvent(
                event_id="EVT001",
                order_id="ORD001",
                event_type="OP_COMPLETE",
                operation="CUTTING",
                equipment_id="EQ-001",
                start_time=datetime(2026, 5, 17, 8, 0, 0),
                end_time=datetime(2026, 5, 17, 9, 0, 0),
                quantity=100,
                location="STATION-1",
            ),
        ]
        workforce_events = []

        # Available: 8 hours (28800 sec), Demand: 480 units
        vsm_data = calc.calculate_from_events(
            events, workforce_events, available_time=28800.0, demand=480
        )

        assert vsm_data.takt_time == 60.0

    def test_calculate_from_events_inventory_positions(self):
        """Test inventory positions are tracked."""
        calc = VSMCalculator()
        events = [
            ProductionEvent(
                event_id="EVT001",
                order_id="ORD001",
                event_type="OP_COMPLETE",
                operation="CUTTING",
                equipment_id="EQ-001",
                start_time=datetime(2026, 5, 17, 8, 0, 0),
                end_time=datetime(2026, 5, 17, 9, 0, 0),
                quantity=100,
                location="STATION-1",
            ),
            ProductionEvent(
                event_id="EVT002",
                order_id="ORD001",
                event_type="OP_COMPLETE",
                operation="ASSEMBLY",
                equipment_id="EQ-003",
                start_time=datetime(2026, 5, 17, 10, 0, 0),
                end_time=datetime(2026, 5, 17, 11, 0, 0),
                quantity=90,
                location="STATION-3",
            ),
        ]
        workforce_events = []

        vsm_data = calc.calculate_from_events(events, workforce_events)

        assert "CUTTING" in vsm_data.inventory_positions
        assert "ASSEMBLY" in vsm_data.inventory_positions
        assert vsm_data.inventory_positions["CUTTING"] == 100
        assert vsm_data.inventory_positions["ASSEMBLY"] == 90


class TestVSMCalculatorIntegration:
    """Integration tests with mock data."""

    def test_with_mock_production_data(self):
        """Test VSM calculator with generated mock data."""
        calc = VSMCalculator()
        production_events = generate_production_events(start_date=BASE_DATE, days=3)
        workforce_events = generate_workforce_events(start_date=BASE_DATE, days=3)

        vsm_data = calc.calculate_from_events(
            production_events,
            workforce_events,
            available_time=28800.0,
            demand=480,
        )

        assert isinstance(vsm_data, VSMData)
        assert len(vsm_data.process_steps) > 0
        assert vsm_data.takt_time == 60.0
        assert vsm_data.total_va_time > 0
        # Verify process steps have required fields
        for step in vsm_data.process_steps:
            assert step.name
            assert step.va_time >= 0
            assert step.nva_time >= 0
            assert step.inventory >= 0

    def test_va_vs_nva_ratio(self):
        """Test VA vs NVA time calculation makes sense."""
        calc = VSMCalculator()
        events = [
            ProductionEvent(
                event_id="EVT001",
                order_id="ORD001",
                event_type="OP_COMPLETE",
                operation="CUTTING",
                equipment_id="EQ-001",
                start_time=datetime(2026, 5, 17, 8, 0, 0),
                end_time=datetime(2026, 5, 17, 9, 0, 0),
                quantity=100,
                location="STATION-1",
            ),
            # Add some NVA (wait time)
            ProductionEvent(
                event_id="EVT002",
                order_id="ORD001",
                event_type="OP_COMPLETE",
                operation="QC",
                equipment_id="QC-001",
                start_time=datetime(2026, 5, 17, 11, 0, 0),
                end_time=datetime(2026, 5, 17, 11, 30, 0),
                quantity=100,
                location="QC-LAB",
            ),
        ]
        workforce_events = []

        vsm_data = calc.calculate_from_events(events, workforce_events)

        # Lead time includes VA + NVA + wait times
        assert vsm_data.total_lead_time >= vsm_data.total_va_time
        # Verify lead time = VA + NVA + wait
        total_wait = sum(s.wait_time for s in vsm_data.process_steps)
        assert vsm_data.total_lead_time == (
            vsm_data.total_va_time + vsm_data.total_nva_time + total_wait
        )