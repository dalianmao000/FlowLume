"""Event dataclasses for Lean Optimization Agent.

These models represent production events, equipment status, and workforce
activity for process mining and Value Stream Map (VSM) analysis.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class EventType(str, Enum):
    """Production event types in order of the value stream."""

    ORDER_CREATED = "ORDER_CREATED"
    ORDER_RELEASED = "ORDER_RELEASED"
    OP_START = "OP_START"
    OP_COMPLETE = "OP_COMPLETE"
    QC_PASS = "QC_PASS"
    QC_FAIL = "QC_FAIL"
    ORDER_SHIPPED = "ORDER_SHIPPED"


class EquipmentStatus(str, Enum):
    """Equipment status values."""

    RUNNING = "RUNNING"
    IDLE = "IDLE"
    DOWN = "DOWN"
    MAINTENANCE = "MAINTENANCE"


@dataclass
class ProductionEvent:
    """Represents a production event in the manufacturing process.

    Attributes:
        event_id: Unique identifier for the event
        order_id: Associated order identifier
        event_type: Type of production event (ORDER_CREATED, ORDER_RELEASED, etc.)
        operation: Operation name (e.g., "ASSEMBLY", "WELDING", "PAINTING")
        equipment_id: Equipment identifier performing the operation
        start_time: When the event started
        end_time: When the event ended (None if still in progress)
        quantity: Number of units involved in the event
        location: Physical location/plant where the event occurred
    """

    event_id: str
    order_id: str
    event_type: EventType
    operation: str
    equipment_id: str
    start_time: datetime
    end_time: Optional[datetime]
    quantity: int
    location: str

    def duration_seconds(self) -> Optional[float]:
        """Calculate event duration in seconds.

        Returns:
            Duration in seconds if end_time is set, None otherwise.
        """
        if self.end_time is None:
            return None
        return (self.end_time - self.start_time).total_seconds()

    def __post_init__(self):
        """Validate event_type is a valid EventType value."""
        valid_types = {e.value for e in EventType}
        if self.event_type not in valid_types:
            raise ValueError(
                f"Invalid event_type: {self.event_type}. Must be one of {valid_types}"
            )


@dataclass
class EquipmentEvent:
    """Represents an equipment status change event.

    Attributes:
        timestamp: When the status change occurred
        equipment_id: Unique equipment identifier
        status: Current equipment status (RUNNING, IDLE, DOWN, MAINTENANCE)
        duration: How long the equipment was in this status (hours)
        reason: Optional reason for the status (e.g., "planned maintenance", "breakdown")
    """

    timestamp: datetime
    equipment_id: str
    status: EquipmentStatus
    duration: Optional[float] = None
    reason: Optional[str] = None

    def __post_init__(self):
        """Validate status is a valid EquipmentStatus value."""
        valid_statuses = {s.value for s in EquipmentStatus}
        if self.status not in valid_statuses:
            raise ValueError(
                f"Invalid status: {self.status}. Must be one of {valid_statuses}"
            )


@dataclass
class WorkforceEvent:
    """Represents a workforce/operator activity event.

    Attributes:
        timestamp: When the activity occurred
        operator_id: Unique operator identifier
        operation: Operation being performed
        cycle_time: Time taken to complete one cycle (seconds)
    """

    timestamp: datetime
    operator_id: str
    operation: str
    cycle_time: float

    def __post_init__(self):
        """Validate cycle_time is positive."""
        if self.cycle_time <= 0:
            raise ValueError(f"cycle_time must be positive, got {self.cycle_time}")