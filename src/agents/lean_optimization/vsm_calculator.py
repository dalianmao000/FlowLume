"""Value Stream Map (VSM) Calculator for Lean Optimization.

This module computes VSM metrics from production events, including:
- Value-added (VA) time: actual processing time
- Non-value-added (NVA) time: wait, transport, inspection time
- Lead time: total time from order to shipment
- Takt time: required pace to meet customer demand
- Inventory positions: WIP at each process step
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional

from .event_log_models import ProductionEvent, WorkforceEvent, EventType


@dataclass
class ProcessStep:
    """Represents a single process step in the value stream.

    Attributes:
        name: Operation/process name (e.g., "CUTTING", "WELDING")
        va_time: Value-added time in seconds (actual processing)
        nva_time: Non-value-added time in seconds (wait, transport, inspection)
        wait_time: Wait time in seconds before this step can start
        inventory: Work-in-progress (WIP) after this step
        takt_time: Target takt time for this step in seconds
    """

    name: str
    va_time: float = 0.0
    nva_time: float = 0.0
    wait_time: float = 0.0
    inventory: int = 0
    takt_time: float = 0.0


@dataclass
class VSMData:
    """Value Stream Map data for a production line or process.

    Attributes:
        process_steps: List of ProcessStep objects in order
        total_va_time: Sum of all value-added time in seconds
        total_nva_time: Sum of all non-value-added time in seconds
        total_lead_time: Total lead time (VA + NVA + wait) in seconds
        inventory_positions: Dict mapping step name to WIP count
        takt_time: Required takt time in seconds to meet demand
    """

    process_steps: List[ProcessStep] = field(default_factory=list)
    total_va_time: float = 0.0
    total_nva_time: float = 0.0
    total_lead_time: float = 0.0
    inventory_positions: Dict[str, int] = field(default_factory=dict)
    takt_time: float = 0.0


class VSMCalculator:
    """Calculator for Value Stream Map metrics.

    Computes VA/NVA time, lead time, takt time, and inventory positions
    from production and workforce events.
    """

    def calculate_takt_time(self, available_time: float, demand: int) -> float:
        """Calculate takt time (required pace to meet demand).

        Args:
            available_time: Available production time in seconds
            demand: Customer demand (units per time period)

        Returns:
            Takt time in seconds per unit

        Raises:
            ValueError: If demand is not positive
        """
        if demand <= 0:
            raise ValueError("demand must be positive")
        return available_time / demand

    def identify_process_steps(
        self, events: List[ProductionEvent]
    ) -> List[ProcessStep]:
        """Identify and group events by operation to create process steps.

        Args:
            events: List of ProductionEvent objects

        Returns:
            List of ProcessStep objects ordered as they appear in production
        """
        if not events:
            return []

        # Group events by operation
        operation_events: Dict[str, List[ProductionEvent]] = {}
        for event in events:
            if event.operation not in operation_events:
                operation_events[event.operation] = []
            operation_events[event.operation].append(event)

        # Sort operations by first event start_time
        def get_first_start(op: str) -> datetime:
            events_for_op = operation_events[op]
            return min(e.start_time for e in events_for_op)

        sorted_operations = sorted(
            operation_events.keys(), key=get_first_start
        )

        steps = []
        prev_end_time: Optional[datetime] = None
        prev_operation: Optional[str] = None

        for op_name in sorted_operations:
            op_events = operation_events[op_name]

            # Calculate VA time (processing time from OP_COMPLETE events)
            va_time = 0.0
            nva_time = 0.0
            total_inventory = 0

            for event in op_events:
                if event.event_type == "OP_COMPLETE":
                    duration = event.duration_seconds()
                    if duration:
                        va_time += duration
                    # Track inventory from quantity
                    total_inventory += event.quantity
                elif event.event_type == "QC_PASS":
                    # QC adds inspection time (NVA)
                    duration = event.duration_seconds()
                    if duration:
                        nva_time += duration

            # Calculate wait time (gap between previous step end and this step start)
            wait_time = 0.0
            if prev_end_time is not None:
                first_start = min(e.start_time for e in op_events)
                if first_start > prev_end_time:
                    wait_time = (first_start - prev_end_time).total_seconds()

            # Get last end time for next iteration
            last_end: Optional[datetime] = None
            for event in op_events:
                if event.end_time:
                    if last_end is None or event.end_time > last_end:
                        last_end = event.end_time

            steps.append(
                ProcessStep(
                    name=op_name,
                    va_time=va_time,
                    nva_time=nva_time,
                    wait_time=wait_time,
                    inventory=total_inventory,
                    takt_time=0.0,  # Set during final calculation
                )
            )

            prev_end_time = last_end
            prev_operation = op_name

        return steps

    def calculate_from_events(
        self,
        production_events: List[ProductionEvent],
        workforce_events: List[WorkforceEvent],
        available_time: Optional[float] = None,
        demand: Optional[int] = None,
    ) -> VSMData:
        """Calculate VSM metrics from production and workforce events.

        Args:
            production_events: List of ProductionEvent objects
            workforce_events: List of WorkforceEvent objects (for future use)
            available_time: Available production time in seconds (optional)
            demand: Customer demand units (optional, required for takt_time)

        Returns:
            VSMData object with all calculated metrics
        """
        # Identify process steps from events
        steps = self.identify_process_steps(production_events)

        # Calculate totals
        total_va_time = sum(s.va_time for s in steps)
        total_nva_time = sum(s.nva_time for s in steps)
        total_wait_time = sum(s.wait_time for s in steps)
        total_lead_time = total_va_time + total_nva_time + total_wait_time

        # Build inventory positions dict
        inventory_positions = {s.name: s.inventory for s in steps}

        # Calculate takt time if parameters provided
        takt_time = 0.0
        if available_time is not None and demand is not None:
            takt_time = self.calculate_takt_time(available_time, demand)
            # Update takt_time on each step
            for step in steps:
                step.takt_time = takt_time

        return VSMData(
            process_steps=steps,
            total_va_time=total_va_time,
            total_nva_time=total_nva_time,
            total_lead_time=total_lead_time,
            inventory_positions=inventory_positions,
            takt_time=takt_time,
        )