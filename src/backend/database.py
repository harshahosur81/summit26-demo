import aiosqlite
import logging
from datetime import datetime, date, timedelta
from pathlib import Path
from src.backend.config import config

logger = logging.getLogger("solar_sync.database")

# Ensure database directory exists
config.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

async def init_db():
    """Initializes the SQLite database tables and seeds default system configurations."""
    async with aiosqlite.connect(config.DATABASE_PATH) as db:
        # 1. System Config Table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS system_config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        
        # 2. Telemetry Log Table (Raw 10-second logs, kept for 7 days)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS telemetry_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                solar_power_w REAL NOT NULL,
                household_consumption_w REAL NOT NULL,
                grid_export_w REAL NOT NULL,
                tesla_charge_amps INTEGER NOT NULL,
                tesla_state TEXT NOT NULL
            )
        """)
        
        # 3. Daily Aggregates Table (Kept indefinitely for analytics)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS daily_aggregates (
                date TEXT PRIMARY KEY,
                solar_generated_kwh REAL NOT NULL,
                ev_charged_kwh REAL NOT NULL,
                grid_imported_kwh REAL NOT NULL,
                grid_exported_kwh REAL NOT NULL,
                self_consumption_pct REAL NOT NULL
            )
        """)
        
        # 4. Charge Sessions Table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS charge_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time REAL NOT NULL,
                end_time REAL,
                energy_added_kwh REAL NOT NULL DEFAULT 0.0,
                start_soc INTEGER,
                end_soc INTEGER
            )
        """)
        
        # Index on telemetry timestamp for rapid pruning and range queries
        await db.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp ON telemetry_log(timestamp)")
        
        # Seed system config defaults if empty
        defaults = {
            "grid_phases": str(config.GRID_PHASES),
            "override_duration_mins": str(config.OVERRIDE_DURATION_MINS),
            "ema_alpha": str(config.EMA_ALPHA),
            "override_active": "false",
            "override_target_amps": "0",
            "override_start_time": "0.0"
        }
        
        for key, val in defaults.items():
            await db.execute(
                "INSERT OR IGNORE INTO system_config (key, value) VALUES (?, ?)",
                (key, val)
            )
            
        await db.commit()
    logger.info("Database initialized successfully.")

# Config getters and setters
async def get_config_val(key: str, default: str) -> str:
    async with aiosqlite.connect(config.DATABASE_PATH) as db:
        async with db.execute("SELECT value FROM system_config WHERE key = ?", (key,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else default

async def set_config_val(key: str, value: str):
    async with aiosqlite.connect(config.DATABASE_PATH) as db:
        await db.execute(
            "INSERT INTO system_config (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value)
        )
        await db.commit()

async def get_override_state() -> dict:
    """Returns the override active state, target amps, and start time."""
    active = (await get_config_val("override_active", "false")).lower() == "true"
    target_amps = int(await get_config_val("override_target_amps", "0"))
    start_time = float(await get_config_val("override_start_time", "0.0"))
    duration_mins = int(await get_config_val("override_duration_mins", str(config.OVERRIDE_DURATION_MINS)))
    
    return {
        "active": active,
        "target_amps": target_amps,
        "start_time": start_time,
        "duration_mins": duration_mins
    }

async def set_override_state(active: bool, target_amps: int = 0, start_time: float = 0.0):
    async with aiosqlite.connect(config.DATABASE_PATH) as db:
        await db.execute("UPDATE system_config SET value = ? WHERE key = 'override_active'", ("true" if active else "false",))
        await db.execute("UPDATE system_config SET value = ? WHERE key = 'override_target_amps'", (str(target_amps),))
        await db.execute("UPDATE system_config SET value = ? WHERE key = 'override_start_time'", (str(start_time),))
        await db.commit()

# Telemetry Log operations
async def log_telemetry(solar_power_w: float, household_consumption_w: float, grid_export_w: float, tesla_charge_amps: int, tesla_state: str):
    async with aiosqlite.connect(config.DATABASE_PATH) as db:
        await db.execute("""
            INSERT INTO telemetry_log (timestamp, solar_power_w, household_consumption_w, grid_export_w, tesla_charge_amps, tesla_state)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (datetime.now().timestamp(), solar_power_w, household_consumption_w, grid_export_w, tesla_charge_amps, tesla_state))
        await db.commit()

async def get_recent_telemetry(limit: int = 100):
    """Retrieves recent raw telemetry rows."""
    async with aiosqlite.connect(config.DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM telemetry_log ORDER BY timestamp DESC LIMIT ?", (limit,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

# DB Pruning and daily aggregation
async def aggregate_and_prune():
    """
    1. Computes the daily statistics for previous days that do not have aggregates.
    2. Deletes raw telemetry log entries older than 7 days.
    """
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    seven_days_ago = now - timedelta(days=7)
    seven_days_ago_ts = seven_days_ago.timestamp()
    
    async with aiosqlite.connect(config.DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        # Find distinct dates in the telemetry log excluding today
        async with db.execute("""
            SELECT DISTINCT date(timestamp, 'unixepoch', 'localtime') as log_date 
            FROM telemetry_log 
            WHERE date(timestamp, 'unixepoch', 'localtime') != ?
        """, (today_str,)) as cursor:
            rows = await cursor.fetchall()
            dates = [row["log_date"] for row in rows if row["log_date"]]
            
        for d in dates:
            # Check if we already have daily_aggregates for this date
            async with db.execute("SELECT 1 FROM daily_aggregates WHERE date = ?", (d,)) as c:
                if await c.fetchone():
                    continue  # already aggregated
            
            # Compute aggregations for date 'd'
            # Note: We aggregate assuming each telemetry row represents approx 10-second intervals
            # Energy (kWh) = Sum(Power (W) * 10 seconds) / (3600 * 1000)
            async with db.execute("""
                SELECT 
                    COUNT(*) as count,
                    SUM(solar_power_w) as sum_solar,
                    SUM(household_consumption_w) as sum_house,
                    SUM(grid_export_w) as sum_grid_export,
                    SUM(CASE WHEN grid_export_w < 0 THEN -grid_export_w ELSE 0 END) as sum_grid_import,
                    SUM(tesla_charge_amps) as sum_tesla_amps
                FROM telemetry_log 
                WHERE date(timestamp, 'unixepoch', 'localtime') = ?
            """, (d,)) as agg_cursor:
                agg = await agg_cursor.fetchone()
                if not agg or agg["count"] == 0:
                    continue
                
                # Each record represents roughly a 10s interval
                # Average power (W) * 24 hours / 1000 = kWh total.
                # Actually, average power (W) * (total duration in hours) / 1000 is more correct.
                # Or simply: sum(Power_W) * interval_seconds / 3,600,000.
                # Since the loop runs every 10 seconds, interval_seconds = 10.
                interval = 10.0
                to_kwh = interval / 3600000.0
                
                solar_gen_kwh = (agg["sum_solar"] or 0) * to_kwh
                # Tesla power draw: Ampere * Grid Voltage * Phases
                # We'll assume a standard 230V connection. TeslaPy Power = Amps * Volt * Phases
                # Let's read grid_phases config to determine multiplier
                phases_str = await get_config_val("grid_phases", "3")
                phases = int(phases_str)
                volt_per_amp = 690.0 if phases == 3 else 230.0
                ev_charged_kwh = (agg["sum_tesla_amps"] or 0) * volt_per_amp * to_kwh
                
                # Grid exported is when grid_export_w > 0
                async with db.execute("""
                    SELECT SUM(CASE WHEN grid_export_w > 0 THEN grid_export_w ELSE 0 END) as sum_export
                    FROM telemetry_log
                    WHERE date(timestamp, 'unixepoch', 'localtime') = ?
                """, (d,)) as exp_cursor:
                    exp_row = await exp_cursor.fetchone()
                    grid_exported_kwh = (exp_row["sum_export"] or 0) * to_kwh
                
                grid_imported_kwh = (agg["sum_grid_import"] or 0) * to_kwh
                
                # Self consumption = (Solar Gen - Grid Export) / Solar Gen * 100
                if solar_gen_kwh > 0:
                    self_consumption = ((solar_gen_kwh - grid_exported_kwh) / solar_gen_kwh) * 100.0
                    self_consumption = max(0.0, min(100.0, self_consumption))
                else:
                    self_consumption = 100.0
                
                await db.execute("""
                    INSERT INTO daily_aggregates (date, solar_generated_kwh, ev_charged_kwh, grid_imported_kwh, grid_exported_kwh, self_consumption_pct)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (d, solar_gen_kwh, ev_charged_kwh, grid_imported_kwh, grid_exported_kwh, self_consumption))
                
        # Now prune raw logs older than 7 days
        await db.execute("DELETE FROM telemetry_log WHERE timestamp < ?", (seven_days_ago_ts,))
        await db.commit()
    logger.info("Database aggregation and pruning complete.")

async def get_daily_analytics(limit: int = 30):
    async with aiosqlite.connect(config.DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM daily_aggregates ORDER BY date DESC LIMIT ?", (limit,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]
