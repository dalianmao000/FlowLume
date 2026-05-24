"""Waste Identifier for Lean Optimization - identifies the 7 types of muda (waste).

This module analyzes production events and VSM data to identify waste:
- WAITING: Waiting for materials, equipment, or information
- TRANSPORT: Unnecessary movement of materials or products
- PROCESSING: Processing steps that don't add value from customer perspective
- INVENTORY: Excess WIP or finished goods
- MOTION: Unnecessary movement by people (walking, reaching, etc.)
- DEFECTS: Products or services that don't meet quality standards
- OVERPRODUCTION: Producing more than customer demand
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional

from .event_log_models import ProductionEvent, EventType
from .vsm_calculator import VSMData


class WasteType(str, Enum):
    """The 7 types of muda (waste) in lean manufacturing."""

    WAITING = "WAITING"
    TRANSPORT = "TRANSPORT"
    PROCESSING = "PROCESSING"
    INVENTORY = "INVENTORY"
    MOTION = "MOTION"
    DEFECTS = "DEFECTS"
    OVERPRODUCTION = "OVERPRODUCTION"


@dataclass
class WasteItem:
    """Represents a detected instance of waste.

    Attributes:
        waste_type: The type of waste (one of the 7 muda types)
        location: Where the waste occurs (process step, station, etc.)
        quantity: Time lost (seconds) or quantity affected (units)
        impact: Description of the impact on the process
        severity: Impact severity (low/medium/high/critical)
    """

    waste_type: WasteType
    location: str
    quantity: float
    impact: str
    severity: str


class WasteIdentifier:
    """Identifies the 7 types of muda from production data.

    Analyzes VSM data and production events to detect waste patterns:
    - Waiting: Long wait times between operations
    - Transport: Location changes between operations for same order
    - Processing: Excessive processing time relative to takt time
    - Inventory: High WIP levels at process steps
    - Motion: Excessive movement (derived from event patterns)
    - Defects: QC_FAIL events indicating quality issues
    - Overproduction: Output quantity exceeds customer demand
    """

    # Threshold for wait time to be considered waste (in seconds)
    WAIT_TIME_THRESHOLD = 300.0  # 5 minutes

    # Threshold for transport waste (detecting location changes)
    LOCATION_CHANGE_THRESHOLD = 1  # At least this many location changes

    # Severity thresholds based on quantity
    CRITICAL_SEVERITY_THRESHOLD = 3600.0  # 1 hour
    HIGH_SEVERITY_THRESHOLD = 1800.0  # 30 minutes
    MEDIUM_SEVERITY_THRESHOLD = 600.0  # 10 minutes

    # Scaling factors for severity calculation when using unit-based quantities
    # These multipliers convert unit counts to time-equivalent severity scores
    INVENTORY_SEVERITY_SCALE = 10  # 10 seconds per unit - WIP ties up capital/space
    TRANSPORT_SEVERITY_SCALE = 300  # 5 minutes (300s) per location change - transport is non-value-adding
    OVERPRODUCTION_SEVERITY_SCALE = 60  # 1 minute (60s) per overproduced unit - excess inventory impact

    def _determine_severity(self, quantity: float) -> str:
        """Determine severity based on quantity (time lost or units affected).

        Args:
            quantity: Time lost in seconds or quantity affected

        Returns:
            Severity level string (low/medium/high/critical)
        """
        if quantity >= self.CRITICAL_SEVERITY_THRESHOLD:
            return "critical"
        elif quantity >= self.HIGH_SEVERITY_THRESHOLD:
            return "high"
        elif quantity >= self.MEDIUM_SEVERITY_THRESHOLD:
            return "medium"
        else:
            return "low"

    def identify_from_vsm(self, vsm_data: VSMData) -> List[WasteItem]:
        """Identify waste from VSM data.

        Args:
            vsm_data: VSMData object containing process metrics

        Returns:
            List of WasteItem objects identified from VSM data
        """
        waste_items = []

        # Check for processing waste (excessive processing time)
        for step in vsm_data.process_steps:
            # If takt time is defined, check if VA time exceeds it significantly
            if vsm_data.takt_time > 0:
                if step.va_time > vsm_data.takt_time * 2:
                    waste_items.append(
                        WasteItem(
                            waste_type=WasteType.PROCESSING,
                            location=step.name,
                            quantity=step.va_time - vsm_data.takt_time,
                            impact=f"VA time ({step.va_time:.0f}s) exceeds 2x takt time ({vsm_data.takt_time:.0f}s)",
                            severity=self._determine_severity(step.va_time - vsm_data.takt_time),
                        )
                    )

            # Check for waiting waste
            if step.wait_time > self.WAIT_TIME_THRESHOLD:
                waste_items.append(
                    WasteItem(
                        waste_type=WasteType.WAITING,
                        location=step.name,
                        quantity=step.wait_time,
                        impact=f"Wait time of {step.wait_time:.0f}s between operations",
                        severity=self._determine_severity(step.wait_time),
                    )
                )

            # Check for inventory waste (excess WIP)
            if step.inventory > 100:  # Arbitrary threshold for excess inventory
                waste_items.append(
                    WasteItem(
                        waste_type=WasteType.INVENTORY,
                        location=step.name,
                        quantity=float(step.inventory),
                        impact=f"Excess WIP inventory: {step.inventory} units",
                        severity=self._determine_severity(float(step.inventory) * self.INVENTORY_SEVERITY_SCALE),  # Scale for units
                    )
                )

        return waste_items

    def identify_waiting(self, events: List[ProductionEvent]) -> List[WasteItem]:
        """Identify waiting waste from production events.

        Waiting waste occurs when there's a significant time gap between
        the end of one operation and the start of the next operation
        for the same order.

        Args:
            events: List of ProductionEvent objects

        Returns:
            List of WasteItem objects representing waiting waste
        """
        waste_items = []

        # Group events by order
        order_events: Dict[str, List[ProductionEvent]] = {}
        for event in events:
            if event.order_id not in order_events:
                order_events[event.order_id] = []
            order_events[event.order_id].append(event)

        for order_id, order_evts in order_events.items():
            # Sort by start time
            sorted_events = sorted(order_evts, key=lambda e: e.start_time)

            # Find gaps between operations
            for i in range(len(sorted_events) - 1):
                current_event = sorted_events[i]
                next_event = sorted_events[i + 1]

                # Only check between OP_COMPLETE and next OP_START for same order
                if (
                    current_event.event_type == "OP_COMPLETE"
                    and next_event.event_type == "OP_START"
                    and current_event.end_time is not None
                ):
                    gap = (next_event.start_time - current_event.end_time).total_seconds()

                    if gap > self.WAIT_TIME_THRESHOLD:
                        waste_items.append(
                            WasteItem(
                                waste_type=WasteType.WAITING,
                                location=f"{current_event.operation} -> {next_event.operation}",
                                quantity=gap,
                                impact=f"Order {order_id} waiting {gap:.0f}s after {current_event.operation} before {next_event.operation}",
                                severity=self._determine_severity(gap),
                            )
                        )

        return waste_items

    def identify_transport(self, events: List[ProductionEvent]) -> List[WasteItem]:
        """Identify transport waste from production events.

        Transport waste occurs when materials or products move between
        different locations unnecessarily (identified by location changes
        within the same order).

        Args:
            events: List of ProductionEvent objects

        Returns:
            List of WasteItem objects representing transport waste
        """
        waste_items = []

        # Group events by order
        order_events: Dict[str, List[ProductionEvent]] = {}
        for event in events:
            if event.order_id not in order_events:
                order_events[event.order_id] = []
            order_events[event.order_id].append(event)

        for order_id, order_evts in order_events.items():
            # Sort by start time
            sorted_events = sorted(order_evts, key=lambda e: e.start_time)

            # Track location sequence for this order
            location_changes = []
            last_location = None

            for event in sorted_events:
                if last_location is not None and event.location != last_location:
                    location_changes.append(
                        (last_location, event.location, event.operation)
                    )
                last_location = event.location

            # If there are excessive location changes, it's transport waste
            if len(location_changes) >= self.LOCATION_CHANGE_THRESHOLD:
                waste_items.append(
                    WasteItem(
                        waste_type=WasteType.TRANSPORT,
                        location=f"Order {order_id}",
                        quantity=float(len(location_changes)),
                        impact=f"Excessive transport: {len(location_changes)} location changes within order",
                        severity=self._determine_severity(float(len(location_changes)) * self.TRANSPORT_SEVERITY_SCALE),
                    )
                )

        return waste_items

    def identify_defects(self, events: List[ProductionEvent]) -> List[WasteItem]:
        """Identify defect waste from production events.

        Defect waste occurs when QC_FAIL events indicate products
        that don't meet quality standards.

        Args:
            events: List of ProductionEvent objects

        Returns:
            List of WasteItem objects representing defect waste
        """
        waste_items = []

        # Find all QC_FAIL events
        defect_events = [
            e for e in events if e.event_type == "QC_FAIL"
        ]

        # Group defects by operation/location
        defects_by_location: Dict[str, List[ProductionEvent]] = {}
        for event in defect_events:
            key = f"{event.operation} at {event.location}"
            if key not in defects_by_location:
                defects_by_location[key] = []
            defects_by_location[key].append(event)

        # Create waste items for each location with defects
        for location, loc_defects in defects_by_location.items():
            total_quantity = sum(e.quantity for e in loc_defects)
            num_defects = len(loc_defects)

            # Calculate time impact (approximate)
            time_impact = 0.0
            for event in loc_defects:
                duration = event.duration_seconds()
                if duration is not None:
                    time_impact += duration

            waste_items.append(
                WasteItem(
                    waste_type=WasteType.DEFECTS,
                    location=location,
                    quantity=float(total_quantity),
                    impact=f"{num_defects} QC failures affecting {total_quantity} units. Time impact: {time_impact:.0f}s",
                    severity=self._determine_severity(time_impact),
                )
            )

        return waste_items

    def identify_overproduction(self, events: List[ProductionEvent]) -> List[WasteItem]:
        """Identify overproduction waste from production events.

        Overproduction waste occurs when output quantity exceeds
        customer demand (identified by ORDER_SHIPPED quantity vs order quantity).

        Args:
            events: List of ProductionEvent objects

        Returns:
            List of WasteItem objects representing overproduction waste
        """
        waste_items = []

        # Track order quantities
        order_info: Dict[str, Dict[str, int]] = {}

        for event in events:
            if event.order_id not in order_info:
                order_info[event.order_id] = {
                    "order_qty": 0,
                    "shipped_qty": 0,
                }

            if event.event_type == "ORDER_CREATED":
                order_info[event.order_id]["order_qty"] = event.quantity
            elif event.event_type == "ORDER_SHIPPED":
                order_info[event.order_id]["shipped_qty"] = event.quantity

        # Find overproduction instances
        for order_id, info in order_info.items():
            if info["order_qty"] > 0 and info["shipped_qty"] > info["order_qty"]:
                excess_qty = info["shipped_qty"] - info["order_qty"]
                waste_items.append(
                    WasteItem(
                        waste_type=WasteType.OVERPRODUCTION,
                        location=f"Order {order_id}",
                        quantity=float(excess_qty),
                        impact=f"Produced {info['shipped_qty']} units but only {info['order_qty']} units ordered ({excess_qty} excess)",
                        severity=self._determine_severity(float(excess_qty) * self.OVERPRODUCTION_SEVERITY_SCALE),  # Scale: 1 min per unit
                    )
                )

        return waste_items

    def identify_inventory(self, events: List[ProductionEvent]) -> List[WasteItem]:
        """Identify inventory waste from production events.

        Inventory waste occurs when there is excess WIP or finished goods
        accumulating at process steps.

        Args:
            events: List of ProductionEvent objects

        Returns:
            List of WasteItem objects representing inventory waste
        """
        waste_items = []

        # Track inventory by location
        inventory_by_location: Dict[str, int] = {}

        # Process OP_COMPLETE events to track WIP
        for event in events:
            if event.event_type == "OP_COMPLETE":
                if event.location not in inventory_by_location:
                    inventory_by_location[event.location] = 0
                inventory_by_location[event.location] += event.quantity

        # Find excess inventory locations
        for location, inv_qty in inventory_by_location.items():
            if inv_qty > 100:  # Threshold for excess
                waste_items.append(
                    WasteItem(
                        waste_type=WasteType.INVENTORY,
                        location=location,
                        quantity=float(inv_qty),
                        impact=f"Excess WIP at {location}: {inv_qty} units accumulated",
                        severity=self._determine_severity(float(inv_qty) * self.INVENTORY_SEVERITY_SCALE),
                    )
                )

        return waste_items

    def identify_motion(self, events: List[ProductionEvent]) -> List[WasteItem]:
        """Identify motion waste from production events.

        Motion waste occurs when there is excessive movement by people
        (walking, reaching, etc.) - detected through frequent small movements
        or operations that take longer than expected at a station.

        Args:
            events: List of ProductionEvent objects

        Returns:
            List of WasteItem objects representing motion waste
        """
        waste_items = []

        # Group events by operation and location
        operation_stats: Dict[str, Dict[str, List[float]]] = {}

        for event in events:
            if event.event_type == "OP_COMPLETE":
                duration = event.duration_seconds()
                if duration is not None:
                    key = f"{event.operation} at {event.location}"
                    if key not in operation_stats:
                        operation_stats[key] = {"durations": [], "count": 0}
                    operation_stats[key]["durations"].append(duration)
                    operation_stats[key]["count"] += event.quantity

        # Analyze for excessive motion (operations taking longer than expected)
        for op_loc, stats in operation_stats.items():
            if len(stats["durations"]) > 1:
                avg_duration = sum(stats["durations"]) / len(stats["durations"])
                max_duration = max(stats["durations"])

                # If max is significantly higher than average, may indicate motion waste
                if max_duration > avg_duration * 1.5 and max_duration > 3600:  # > 1 hour and 50% above avg
                    operation_name = op_loc.split(" at ")[0]
                    location = op_loc.split(" at ")[1] if " at " in op_loc else "Unknown"

                    waste_items.append(
                        WasteItem(
                            waste_type=WasteType.MOTION,
                            location=location,
                            quantity=max_duration - avg_duration,
                            impact=f"Excessive motion detected at {operation_name}: max {max_duration:.0f}s vs avg {avg_duration:.0f}s",
                            severity=self._determine_severity(max_duration - avg_duration),
                        )
                    )

        return waste_items

    def identify_processing(self, events: List[ProductionEvent]) -> List[WasteItem]:
        """Identify processing waste from production events.

        Processing waste occurs when processing steps take longer than
        necessary or exceed takt time significantly.

        Args:
            events: List of ProductionEvent objects

        Returns:
            List of WasteItem objects representing processing waste
        """
        waste_items = []

        # Group events by operation to find average processing times
        operation_times: Dict[str, List[float]] = {}

        for event in events:
            if event.event_type == "OP_COMPLETE":
                duration = event.duration_seconds()
                if duration is not None:
                    if event.operation not in operation_times:
                        operation_times[event.operation] = []
                    operation_times[event.operation].append(duration)

        # Find operations with excessive processing time
        for operation, durations in operation_times.items():
            if len(durations) > 0:
                avg_time = sum(durations) / len(durations)
                total_time = sum(durations)

                # Check for processing that exceeds reasonable limits
                # Using 2x the average as threshold for excessive processing
                threshold = avg_time * 2
                excessive_count = sum(1 for d in durations if d > threshold)

                if excessive_count > 0:
                    total_excess = sum(d - threshold for d in durations if d > threshold)
                    waste_items.append(
                        WasteItem(
                            waste_type=WasteType.PROCESSING,
                            location=operation,
                            quantity=total_excess,
                            impact=f"{excessive_count} cycles exceeded threshold at {operation}: avg {avg_time:.0f}s, threshold {threshold:.0f}s",
                            severity=self._determine_severity(total_excess),
                        )
                    )

        return waste_items

    def identify_all(self, events: List[ProductionEvent], vsm_data: Optional[VSMData] = None) -> List[WasteItem]:
        """Identify all types of waste from production events.

        Args:
            events: List of ProductionEvent objects
            vsm_data: Optional VSMData object for additional context

        Returns:
            List of all WasteItem objects identified
        """
        all_waste = []

        all_waste.extend(self.identify_waiting(events))
        all_waste.extend(self.identify_transport(events))
        all_waste.extend(self.identify_defects(events))
        all_waste.extend(self.identify_overproduction(events))
        all_waste.extend(self.identify_inventory(events))
        all_waste.extend(self.identify_motion(events))
        all_waste.extend(self.identify_processing(events))

        if vsm_data is not None:
            all_waste.extend(self.identify_from_vsm(vsm_data))

        return all_waste