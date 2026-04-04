"""Database utilities for Health Addon."""
import aiosqlite
import logging
from datetime import datetime
from typing import Any, Optional

_LOGGER = logging.getLogger(__name__)


class Database:
    """SQLite database handler for health data."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn: Optional[aiosqlite.Connection] = None

    async def init(self) -> None:
        """Initialize the database."""
        self.conn = await aiosqlite.connect(self.db_path)
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS health_parameters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                value REAL NOT NULL,
                unit TEXT NOT NULL,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS medications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                dosage TEXT NOT NULL,
                barcode TEXT,
                expiration_date DATE,
                quantity INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS medication_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                medication_id INTEGER NOT NULL,
                taken_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (medication_id) REFERENCES medications (id)
            )
        """)
        await self.conn.commit()
        _LOGGER.info("Database initialized at %s", self.db_path)

    async def close(self) -> None:
        """Close database connection."""
        if self.conn:
            await self.conn.close()

    # Health Parameters
    async def add_health_parameter(self, name: str, value: float, unit: str) -> None:
        """Add a health parameter reading."""
        await self.conn.execute(
            "INSERT INTO health_parameters (name, value, unit) VALUES (?, ?, ?)",
            (name, value, unit)
        )
        await self.conn.commit()

    async def get_health_parameters(self, name: str, limit: int = 100) -> list[dict]:
        """Get health parameter history."""
        cursor = await self.conn.execute(
            "SELECT name, value, unit, recorded_at FROM health_parameters WHERE name = ? ORDER BY recorded_at DESC LIMIT ?",
            (name, limit)
        )
        rows = await cursor.fetchall()
        return [
            {"name": row[0], "value": row[1], "unit": row[2], "recorded_at": row[3]}
            for row in rows
        ]

    async def get_all_parameters(self) -> list[dict]:
        """Get all unique parameter names."""
        cursor = await self.conn.execute(
            "SELECT DISTINCT name, unit FROM health_parameters ORDER BY name"
        )
        rows = await cursor.fetchall()
        return [{"name": row[0], "unit": row[1]} for row in rows]

    # Medications
    async def add_medication(self, name: str, dosage: str, barcode: str = None, expiration_date: str = None, quantity: int = 0) -> int:
        """Add a medication to inventory."""
        cursor = await self.conn.execute(
            "INSERT INTO medications (name, dosage, barcode, expiration_date, quantity) VALUES (?, ?, ?, ?, ?)",
            (name, dosage, barcode, expiration_date, quantity)
        )
        await self.conn.commit()
        return cursor.lastrowid

    async def update_medication(self, medication_id: int, **kwargs) -> None:
        """Update medication details."""
        fields = ", ".join(f"{k} = ?" for k in kwargs.keys())
        values = list(kwargs.values()) + [medication_id]
        await self.conn.execute(
            f"UPDATE medications SET {fields} WHERE id = ?",
            values
        )
        await self.conn.commit()

    async def get_medications(self) -> list[dict]:
        """Get all medications."""
        cursor = await self.conn.execute(
            "SELECT id, name, dosage, barcode, expiration_date, quantity FROM medications ORDER BY name"
        )
        rows = await cursor.fetchall()
        return [
            {"id": row[0], "name": row[1], "dosage": row[2], "barcode": row[3], "expiration_date": row[4], "quantity": row[5]}
            for row in rows
        ]

    async def get_medication_by_barcode(self, barcode: str) -> Optional[dict]:
        """Get medication by barcode."""
        cursor = await self.conn.execute(
            "SELECT id, name, dosage, barcode, expiration_date, quantity FROM medications WHERE barcode = ?",
            (barcode,)
        )
        row = await cursor.fetchone()
        if row:
            return {"id": row[0], "name": row[1], "dosage": row[2], "barcode": row[3], "expiration_date": row[4], "quantity": row[5]}
        return None

    async def delete_medication(self, medication_id: int) -> None:
        """Delete a medication."""
        await self.conn.execute("DELETE FROM medications WHERE id = ?", (medication_id,))
        await self.conn.commit()

    # Medication Logs
    async def log_medication_taken(self, medication_id: int) -> None:
        """Log when medication was taken."""
        await self.conn.execute(
            "INSERT INTO medication_logs (medication_id) VALUES (?)",
            (medication_id,)
        )
        await self.conn.commit()

    async def get_medication_logs(self, medication_id: int, limit: int = 50) -> list[dict]:
        """Get medication intake history."""
        cursor = await self.conn.execute(
            "SELECT medication_id, taken_at FROM medication_logs WHERE medication_id = ? ORDER BY taken_at DESC LIMIT ?",
            (medication_id, limit)
        )
        rows = await cursor.fetchall()
        return [{"medication_id": row[0], "taken_at": row[1]} for row in rows]

    async def get_last_dose(self, medication_id: int) -> Optional[datetime]:
        """Get last dose timestamp."""
        cursor = await self.conn.execute(
            "SELECT taken_at FROM medication_logs WHERE medication_id = ? ORDER BY taken_at DESC LIMIT 1",
            (medication_id,)
        )
        row = await cursor.fetchone()
        return datetime.fromisoformat(row[0]) if row else None
