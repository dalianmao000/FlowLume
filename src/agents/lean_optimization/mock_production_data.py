"""Mock production data generator for Lean Optimization Agent testing."""

import random
import uuid
from datetime import datetime, timedelta
from typing import List

from .event_log_models import ProductionEvent, EquipmentEvent, WorkforceEvent, EventType, EquipmentStatus


# Base date for deterministic test data generation
BASE_DATE = datetime(2026, 5, 17, 0, 0, 0)

# Configuration for mock data generation
PRODUCTION_LINES = ["LINE-001", "LINE-002", "LINE-003"]
OPERATIONS = ["CUTTING", "WELDING", "ASSEMBLY", "PAINTING", "QC"]
LOCATIONS = ["WAREHOUSE-A", "WAREHOUSE-B", "STATION-1", "STATION-2", "STATION-3", "SHIPPING"]
EQUIPMENT_IDS = [f"EQ-{line}-{op}" for line in ["A", "B", "C"] for op in ["CUT", "WELD", "ASS", "PAINT"]]
OPERATOR_IDS = [f"OP-{i:03d}" for i in range(1, 21)]
EVENT_TYPES = [e.value for e in EventType]
EQUIPMENT_STATUSES = [s.value for s in EquipmentStatus]


def generate_production_events(start_date: datetime, days: int = 7) -> List[ProductionEvent]:
    """Generate production events with realistic patterns over a period.

    Args:
        start_date: Starting datetime for event generation
        days: Number of days to generate events for

    Returns:
        List of ProductionEvent objects
    """
    events = []
    current_time = start_date

    # Generate orders with varying volumes
    num_orders = random.randint(40, 60)

    for order_idx in range(num_orders):
        order_id = f"ORD-{start_date.strftime('%Y%m%d')}-{order_idx:04d}"
        quantity = random.randint(50, 500)

        # Create order creation event
        order_start_time = current_time + timedelta(hours=random.uniform(0, 2))
        events.append(ProductionEvent(
            event_id=str(uuid.uuid4()),
            order_id=order_id,
            event_type="ORDER_CREATED",
            operation="ORDER_ENTRY",
            equipment_id="ERP-SYSTEM",
            start_time=order_start_time,
            end_time=order_start_time + timedelta(minutes=random.uniform(5, 15)),
            quantity=quantity,
            location="ORDER_ENTRY"
        ))

        # Simulate order release with slight delay after creation
        release_time = order_start_time + timedelta(hours=random.uniform(0.5, 2))
        events.append(ProductionEvent(
            event_id=str(uuid.uuid4()),
            order_id=order_id,
            event_type="ORDER_RELEASED",
            operation="ORDER_RELEASE",
            equipment_id="ERP-SYSTEM",
            start_time=release_time,
            end_time=release_time + timedelta(minutes=random.uniform(2, 5)),
            quantity=quantity,
            location="ORDER_ENTRY"
        ))

        # Create operation events for each production stage
        op_start_time = release_time + timedelta(hours=random.uniform(0, 1))

        for op_idx, operation in enumerate(OPERATIONS):
            # Add realistic bottlenecks - painting often takes longer
            if operation == "PAINTING":
                op_duration = timedelta(hours=random.uniform(2, 5))
            elif operation == "WELDING":
                op_duration = timedelta(hours=random.uniform(1.5, 3))
            else:
                op_duration = timedelta(hours=random.uniform(0.5, 2))

            # Include changeover time occasionally
            if random.random() < 0.1:
                op_duration += timedelta(minutes=random.uniform(15, 45))

            equipment_id = f"EQ-{PRODUCTION_LINES[order_idx % 3][-3:]}-{operation[:4]}"

            # OP_START event
            events.append(ProductionEvent(
                event_id=str(uuid.uuid4()),
                order_id=order_id,
                event_type="OP_START",
                operation=operation,
                equipment_id=equipment_id,
                start_time=op_start_time,
                end_time=None,
                quantity=quantity,
                location=LOCATIONS[op_idx % len(LOCATIONS)]
            ))

            op_end_time = op_start_time + op_duration

            # OP_COMPLETE event
            events.append(ProductionEvent(
                event_id=str(uuid.uuid4()),
                order_id=order_id,
                event_type="OP_COMPLETE",
                operation=operation,
                equipment_id=equipment_id,
                start_time=op_start_time,
                end_time=op_end_time,
                quantity=quantity,
                location=LOCATIONS[op_idx % len(LOCATIONS)]
            ))

            # QC events after operations
            if random.random() < 0.9:  # 90% pass rate
                qc_time = op_end_time + timedelta(minutes=random.uniform(10, 30))
                events.append(ProductionEvent(
                    event_id=str(uuid.uuid4()),
                    order_id=order_id,
                    event_type="QC_PASS",
                    operation=operation,
                    equipment_id="QC-STATION-01",
                    start_time=qc_time,
                    end_time=qc_time + timedelta(minutes=random.uniform(5, 15)),
                    quantity=quantity,
                    location="QC-LAB"
                ))
            else:
                qc_time = op_end_time + timedelta(minutes=random.uniform(10, 30))
                events.append(ProductionEvent(
                    event_id=str(uuid.uuid4()),
                    order_id=order_id,
                    event_type="QC_FAIL",
                    operation=operation,
                    equipment_id="QC-STATION-01",
                    start_time=qc_time,
                    end_time=qc_time + timedelta(minutes=random.uniform(5, 15)),
                    quantity=quantity,
                    location="QC-LAB"
                ))
                # Retry with pass
                retry_time = qc_time + timedelta(hours=1)
                events.append(ProductionEvent(
                    event_id=str(uuid.uuid4()),
                    order_id=order_id,
                    event_type="QC_PASS",
                    operation=operation,
                    equipment_id="QC-STATION-01",
                    start_time=retry_time,
                    end_time=retry_time + timedelta(minutes=random.uniform(5, 15)),
                    quantity=quantity,
                    location="QC-LAB"
                ))

            op_start_time = op_end_time + timedelta(hours=random.uniform(0.5, 1.5))

        # Final shipping event
        ship_time = op_start_time + timedelta(hours=random.uniform(1, 3))
        events.append(ProductionEvent(
            event_id=str(uuid.uuid4()),
            order_id=order_id,
            event_type="ORDER_SHIPPED",
            operation="SHIPPING",
            equipment_id="SHIPPING-BAY",
            start_time=ship_time,
            end_time=ship_time + timedelta(minutes=random.uniform(30, 90)),
            quantity=quantity,
            location="SHIPPING"
        ))

        # Advance time for next order (with peak hours consideration)
        hour = current_time.hour
        if 8 <= hour < 10 or 14 <= hour < 16:  # Peak hours
            current_time += timedelta(hours=random.uniform(1, 2))
        else:
            current_time += timedelta(hours=random.uniform(2, 4))

        # Weekend slowdown
        if current_time.weekday() >= 5:
            current_time += timedelta(days=1)
            current_time = current_time.replace(hour=8)

    # Sort by start_time before returning
    events.sort(key=lambda e: e.start_time)
    return events


def generate_equipment_events(start_date: datetime, days: int = 7) -> List[EquipmentEvent]:
    """Generate equipment status events.

    Args:
        start_date: Starting datetime for event generation
        days: Number of days to generate events for

    Returns:
        List of EquipmentEvent objects
    """
    events = []
    current_time = start_date
    end_time = start_date + timedelta(days=days)

    # Track current status for each piece of equipment
    equipment_status = {eq: "RUNNING" for eq in EQUIPMENT_IDS}

    while current_time < end_time:
        for equipment_id in EQUIPMENT_IDS:
            # Small chance of status change at each interval
            if random.random() < 0.05:
                old_status = equipment_status[equipment_id]
                possible_statuses = [s for s in EQUIPMENT_STATUSES if s != old_status]

                # Weighted probabilities based on typical manufacturing
                if old_status == "RUNNING":
                    weights = [0.7, 0.1, 0.1, 0.1]  # Stay running, go idle, down, maintenance
                elif old_status == "IDLE":
                    weights = [0.6, 0.1, 0.15, 0.15]
                elif old_status == "DOWN":
                    weights = [0.4, 0.2, 0.2, 0.2]
                else:  # MAINTENANCE
                    weights = [0.5, 0.15, 0.15, 0.2]

                new_status = random.choices(possible_statuses, weights=weights[:len(possible_statuses)])[0]
                equipment_status[equipment_id] = new_status

                # Calculate duration
                if new_status in ["RUNNING", "IDLE"]:
                    duration = random.uniform(0.5, 4.0)  # hours
                    reason = None
                elif new_status == "DOWN":
                    duration = random.uniform(1.0, 8.0)  # hours
                    reason = random.choice(["机械故障", "电气故障", "物料短缺", "操作错误"])
                else:  # MAINTENANCE
                    duration = random.uniform(2.0, 12.0)  # hours
                    reason = random.choice(["计划维护", "预防性维护", "设备调整", "换型"])

                events.append(EquipmentEvent(
                    timestamp=current_time,
                    equipment_id=equipment_id,
                    status=new_status,
                    duration=duration,
                    reason=reason
                ))

        # Advance time by 15 minutes
        current_time += timedelta(minutes=15)

    return events


def generate_workforce_events(start_date: datetime, days: int = 7) -> List[WorkforceEvent]:
    """Generate workforce performance events with cycle times.

    Args:
        start_date: Starting datetime for event generation
        days: Number of days to generate events for

    Returns:
        List of WorkforceEvent objects
    """
    events = []
    current_time = start_date
    end_time = start_date + timedelta(days=days)

    while current_time < end_time:
        # Only generate during working hours
        if 8 <= current_time.hour < 18 and current_time.weekday() < 5:
            # Generate events for random operators
            num_operators = random.randint(5, 15)

            for _ in range(num_operators):
                operator_id = random.choice(OPERATOR_IDS)
                operation = random.choice(OPERATIONS)

                # Base cycle times vary by operation
                if operation == "CUTTING":
                    base_cycle = random.uniform(0.5, 1.5)
                elif operation == "WELDING":
                    base_cycle = random.uniform(1.0, 2.5)
                elif operation == "ASSEMBLY":
                    base_cycle = random.uniform(0.8, 2.0)
                elif operation == "PAINTING":
                    base_cycle = random.uniform(1.5, 3.0)
                else:  # QC
                    base_cycle = random.uniform(0.3, 1.0)

                # Add some variation
                cycle_time = base_cycle * random.uniform(0.8, 1.2)

                events.append(WorkforceEvent(
                    timestamp=current_time,
                    operator_id=operator_id,
                    operation=operation,
                    cycle_time=cycle_time
                ))

        # Advance time by 30 minutes
        current_time += timedelta(minutes=30)

    return events


def generate_all_mock_data(start_date: datetime = None, days: int = 7):
    """Generate all mock data for testing.

    Args:
        start_date: Starting datetime (defaults to 7 days ago)
        days: Number of days to generate

    Returns:
        Tuple of (production_events, equipment_events, workforce_events)
    """
    if start_date is None:
        start_date = datetime.now() - timedelta(days=days)

    production_events = generate_production_events(start_date, days)
    equipment_events = generate_equipment_events(start_date, days)
    workforce_events = generate_workforce_events(start_date, days)

    return production_events, equipment_events, workforce_events