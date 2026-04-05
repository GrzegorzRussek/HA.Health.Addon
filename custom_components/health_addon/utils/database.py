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
        
        # Enable foreign keys
        await self.conn.execute("PRAGMA foreign_keys = ON")
        
        # Users table
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Health parameters with user_id
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS health_parameters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                value REAL NOT NULL,
                unit TEXT NOT NULL,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Medications with user_id
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS medications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                dosage TEXT NOT NULL,
                barcode TEXT,
                expiration_date DATE,
                quantity INTEGER DEFAULT 0,
                schedule TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Medication logs with user_id
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS medication_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                medication_id INTEGER NOT NULL,
                taken_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (medication_id) REFERENCES medications(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Create indexes for better query performance
        await self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_health_params_user ON health_parameters(user_id, name)
        """)
        await self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_medications_user ON medications(user_id)
        """)
        await self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_med_logs_user ON medication_logs(user_id, medication_id)
        """)
        
        await self.conn.commit()
        _LOGGER.info("Database initialized at %s", self.db_path)

    async def close(self) -> None:
        """Close database connection."""
        if self.conn:
            await self.conn.close()

    # User management
    async def add_user(self, user_id: str, name: str) -> None:
        """Add a user."""
        await self.conn.execute(
            "INSERT OR IGNORE INTO users (user_id, name) VALUES (?, ?)",
            (user_id, name)
        )
        await self.conn.commit()

    async def get_users(self) -> list[dict]:
        """Get all users."""
        cursor = await self.conn.execute(
            "SELECT user_id, name, created_at FROM users ORDER BY name"
        )
        rows = await cursor.fetchall()
        return [{"user_id": row[0], "name": row[1], "created_at": row[2]} for row in rows]

    # Health Parameters
    async def add_health_parameter(self, user_id: str, name: str, value: float, unit: str) -> None:
        """Add a health parameter reading."""
        await self.conn.execute(
            "INSERT INTO health_parameters (user_id, name, value, unit) VALUES (?, ?, ?, ?)",
            (user_id, name, value, unit)
        )
        await self.conn.commit()

    async def get_health_parameters(self, user_id: str, name: str, limit: int = 100) -> list[dict]:
        """Get health parameter history for a user."""
        cursor = await self.conn.execute(
            """SELECT name, value, unit, recorded_at FROM health_parameters 
               WHERE user_id = ? AND name = ? ORDER BY recorded_at DESC LIMIT ?""",
            (user_id, name, limit)
        )
        rows = await cursor.fetchall()
        return [
            {"name": row[0], "value": row[1], "unit": row[2], "recorded_at": row[3]}
            for row in rows
        ]

    async def get_all_parameters(self, user_id: str = None) -> list[dict]:
        """Get all unique parameter names, optionally filtered by user."""
        if user_id:
            cursor = await self.conn.execute(
                """SELECT DISTINCT user_id, name, unit FROM health_parameters 
                   WHERE user_id = ? ORDER BY name""",
                (user_id,)
            )
        else:
            cursor = await self.conn.execute(
                """SELECT DISTINCT user_id, name, unit FROM health_parameters ORDER BY user_id, name"""
            )
        rows = await cursor.fetchall()
        return [{"user_id": row[0], "name": row[1], "unit": row[2]} for row in rows]

    async def get_latest_parameters(self, user_id: str) -> list[dict]:
        """Get latest reading for each parameter for a user."""
        cursor = await self.conn.execute("""
            SELECT hp.user_id, hp.name, hp.value, hp.unit, hp.recorded_at
            FROM health_parameters hp
            INNER JOIN (
                SELECT user_id, name, MAX(recorded_at) as max_recorded
                FROM health_parameters
                WHERE user_id = ?
                GROUP BY user_id, name
            ) latest ON hp.user_id = latest.user_id AND hp.name = latest.name AND hp.recorded_at = latest.max_recorded
            WHERE hp.user_id = ?
            ORDER BY hp.name
        """, (user_id, user_id))
        rows = await cursor.fetchall()
        return [
            {"user_id": row[0], "name": row[1], "value": row[2], "unit": row[3], "recorded_at": row[4]}
            for row in rows
        ]

    # Medications
    async def add_medication(self, user_id: str, name: str, dosage: str, barcode: str = None, expiration_date: str = None, quantity: int = 0, schedule: str = None) -> int:
        """Add a medication to inventory."""
        cursor = await self.conn.execute(
            "INSERT INTO medications (user_id, name, dosage, barcode, expiration_date, quantity, schedule) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, name, dosage, barcode, expiration_date, quantity, schedule)
        )
        await self.conn.commit()
        return cursor.lastrowid

    async def update_medication(self, user_id: str, medication_id: int, **kwargs) -> None:
        """Update medication details."""
        fields = ", ".join(f"{k} = ?" for k in kwargs.keys())
        values = list(kwargs.values()) + [user_id, medication_id]
        await self.conn.execute(
            f"UPDATE medications SET {fields} WHERE user_id = ? AND id = ?",
            values
        )
        await self.conn.commit()

    async def get_medications(self, user_id: str = None) -> list[dict]:
        """Get all medications, optionally filtered by user."""
        if user_id:
            cursor = await self.conn.execute(
                """SELECT id, user_id, name, dosage, barcode, expiration_date, quantity, schedule 
                   FROM medications WHERE user_id = ? ORDER BY name""",
                (user_id,)
            )
        else:
            cursor = await self.conn.execute(
                """SELECT id, user_id, name, dosage, barcode, expiration_date, quantity, schedule 
                   FROM medications ORDER BY user_id, name"""
            )
        rows = await cursor.fetchall()
        return [
            {"id": row[0], "user_id": row[1], "name": row[2], "dosage": row[3], "barcode": row[4], "expiration_date": row[5], "quantity": row[6], "schedule": row[7]}
            for row in rows
        ]

    async def get_medication_by_barcode(self, user_id: str, barcode: str) -> Optional[dict]:
        """Get medication by barcode for a user."""
        cursor = await self.conn.execute(
            """SELECT id, user_id, name, dosage, barcode, expiration_date, quantity, schedule 
               FROM medications WHERE user_id = ? AND barcode = ?""",
            (user_id, barcode)
        )
        row = await cursor.fetchone()
        if row:
            return {"id": row[0], "user_id": row[1], "name": row[2], "dosage": row[3], "barcode": row[4], "expiration_date": row[5], "quantity": row[6], "schedule": row[7]}
        return None

    async def delete_medication(self, user_id: str, medication_id: int) -> None:
        """Delete a medication."""
        await self.conn.execute(
            "DELETE FROM medications WHERE user_id = ? AND id = ?", 
            (user_id, medication_id)
        )
        await self.conn.commit()

    # Medication Logs
    async def log_medication_taken(self, user_id: str, medication_id: int) -> None:
        """Log when medication was taken."""
        await self.conn.execute(
            "INSERT INTO medication_logs (user_id, medication_id) VALUES (?, ?)",
            (user_id, medication_id)
        )
        await self.conn.commit()

    async def get_medication_logs(self, user_id: str, medication_id: int = None, limit: int = 50) -> list[dict]:
        """Get medication intake history."""
        if medication_id:
            cursor = await self.conn.execute(
                """SELECT user_id, medication_id, taken_at FROM medication_logs 
                   WHERE user_id = ? AND medication_id = ? ORDER BY taken_at DESC LIMIT ?""",
                (user_id, medication_id, limit)
            )
        else:
            cursor = await self.conn.execute(
                """SELECT user_id, medication_id, taken_at FROM medication_logs 
                   WHERE user_id = ? ORDER BY taken_at DESC LIMIT ?""",
                (user_id, limit)
            )
        rows = await cursor.fetchall()
        return [{"user_id": row[0], "medication_id": row[1], "taken_at": row[2]} for row in rows]

    async def get_last_dose(self, user_id: str, medication_id: int) -> Optional[datetime]:
        """Get last dose timestamp."""
        cursor = await self.conn.execute(
            """SELECT taken_at FROM medication_logs 
               WHERE user_id = ? AND medication_id = ? ORDER BY taken_at DESC LIMIT 1""",
            (user_id, medication_id)
        )
        row = await cursor.fetchone()
        return datetime.fromisoformat(row[0]) if row else None
