"""Mock SQLite database for Data Insight Agent testing.

This module provides a test database with sample manufacturing data for:
- Text-to-SQL module testing
- Anomaly detection testing
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

DB_PATH = Path("/Users/yinjili/p43_FlowLume/data/mock_manufacturing.db")


def get_connection() -> sqlite3.Connection:
    """Get a connection to the mock database."""
    return sqlite3.connect(DB_PATH)


def init_mock_db() -> None:
    """Create tables and insert sample data into the mock database."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Remove existing database to ensure clean state
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = get_connection()
    cursor = conn.cursor()

    # Create production_daily table
    cursor.execute("""
        CREATE TABLE production_daily (
            date TEXT NOT NULL,
            plant TEXT NOT NULL,
            line TEXT NOT NULL,
            output_qty INTEGER NOT NULL,
            defect_qty INTEGER NOT NULL,
            downtime_hours REAL NOT NULL,
            oee REAL NOT NULL
        )
    """)

    # Create equipment_status table
    cursor.execute("""
        CREATE TABLE equipment_status (
            timestamp TEXT NOT NULL,
            equipment_id TEXT NOT NULL,
            status TEXT NOT NULL,
            temperature REAL,
            pressure REAL
        )
    """)

    # Create quality_inspection table
    cursor.execute("""
        CREATE TABLE quality_inspection (
            inspection_date TEXT NOT NULL,
            batch_no TEXT NOT NULL,
            inspection_result TEXT NOT NULL,
            defect_type TEXT,
            quantity INTEGER NOT NULL
        )
    """)

    # Insert sample data for production_daily
    # 30 days x 3 lines x 2 plants = 180 rows
    plants = ["Plant_A", "Plant_B"]
    lines = ["Line_1", "Line_2", "Line_3"]
    base_date = datetime(2026, 4, 25)

    production_rows = []
    for day_offset in range(30):
        current_date = base_date + timedelta(days=day_offset)
        date_str = current_date.strftime("%Y-%m-%d")
        for plant in plants:
            for line in lines:
                output_qty = 800 + (day_offset * 10) + (hash(f"{plant}{line}") % 200)
                defect_qty = int(output_qty * (0.02 + (day_offset % 10) * 0.002))
                downtime_hours = (day_offset % 5) * 0.5 + (hash(f"{plant}{line}{day_offset}") % 100) / 100
                oee = 0.85 + (hash(f"{plant}{line}{day_offset}") % 150) / 1000
                production_rows.append(
                    (date_str, plant, line, output_qty, defect_qty, round(downtime_hours, 2), round(oee, 3))
                )

    cursor.executemany(
        "INSERT INTO production_daily (date, plant, line, output_qty, defect_qty, downtime_hours, oee) VALUES (?, ?, ?, ?, ?, ?, ?)",
        production_rows,
    )

    # Insert sample data for equipment_status
    # ~500 event records with RUNNING/IDLE/DOWN/MAINTENANCE status
    equipment_ids = [f"EQ_{i:03d}" for i in range(1, 21)]
    statuses = ["RUNNING", "IDLE", "DOWN", "MAINTENANCE"]
    status_weights = [0.6, 0.2, 0.1, 0.1]  # Probabilities for each status

    equipment_rows = []
    base_timestamp = datetime(2026, 4, 25, 6, 0, 0)

    for minute_offset in range(500):
        timestamp = base_timestamp + timedelta(minutes=minute_offset * 10)
        equipment_id = equipment_ids[minute_offset % len(equipment_ids)]

        # Weighted random status selection
        import random
        rand_val = random.random()
        cumulative = 0
        selected_status = statuses[0]
        for i, status in enumerate(statuses):
            cumulative += status_weights[i]
            if rand_val <= cumulative:
                selected_status = status
                break

        temp = 45 + (minute_offset % 50) * 0.5 + random.random() * 5
        pressure = 1.0 + (minute_offset % 30) * 0.02 + random.random() * 0.1

        equipment_rows.append(
            (timestamp.strftime("%Y-%m-%d %H:%M:%S"), equipment_id, selected_status, round(temp, 1), round(pressure, 2))
        )

    cursor.executemany(
        "INSERT INTO equipment_status (timestamp, equipment_id, status, temperature, pressure) VALUES (?, ?, ?, ?, ?)",
        equipment_rows,
    )

    # Insert sample data for quality_inspection
    # ~100 inspection records
    inspection_results = ["PASS", "FAIL", "REWORK"]
    defect_types = ["Scratch", "Dent", "Misalignment", "Surface_Flaw", "Dimension_Error", None]

    inspection_rows = []
    base_inspection_date = datetime(2026, 4, 1)

    for i in range(100):
        inspection_date = base_inspection_date + timedelta(days=i % 30, hours=(i % 12))
        batch_no = f"BATCH_{2026}_{i:04d}"
        result = inspection_results[i % 3]
        defect = defect_types[i % 6] if result != "PASS" else None
        quantity = 50 + (i * 7) % 100

        inspection_rows.append(
            (inspection_date.strftime("%Y-%m-%d"), batch_no, result, defect, quantity)
        )

    cursor.executemany(
        "INSERT INTO quality_inspection (inspection_date, batch_no, inspection_result, defect_type, quantity) VALUES (?, ?, ?, ?, ?)",
        inspection_rows,
    )

    conn.commit()
    conn.close()


def get_schema() -> dict[str, Any]:
    """Return table metadata for Text-to-SQL.

    Returns:
        Dictionary containing table names and their column information.
    """
    conn = get_connection()
    cursor = conn.cursor()

    schema = {}
    table_names = ["production_daily", "equipment_status", "quality_inspection"]

    for table_name in table_names:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        schema[table_name] = {
            "columns": [
                {"name": col[1], "type": col[2], "not_null": bool(col[3]), "default": col[4]}
                for col in columns
            ]
        }

    conn.close()
    return schema


def verify_data() -> dict[str, int]:
    """Return row counts for all tables.

    Returns:
        Dictionary with table names as keys and row counts as values.
    """
    conn = get_connection()
    cursor = conn.cursor()

    counts = {}
    for table_name in ["production_daily", "equipment_status", "quality_inspection"]:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        counts[table_name] = cursor.fetchone()[0]

    conn.close()
    return counts