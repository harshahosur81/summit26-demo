import asyncio
import json
import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.backend.config import config
from src.backend.database import (
    init_db,
    get_config_val,
    set_config_val,
    get_override_state,
    set_override_state,
    aggregate_and_prune,
    get_recent_telemetry,
    get_daily_analytics
)
from src.backend.vault import CryptographicVault
from src.backend.drivers.goodwe_driver import GoodWeDriver
from src.backend.drivers.tesla_driver import TeslaDriver
from src.backend.control_loop import ChargingController

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("solar_sync.main")

# Drivers and Controller instantiation
goodwe_driver = GoodWeDriver()
tesla_driver = TeslaDriver()
controller = ChargingController(goodwe_driver, tesla_driver)

# Path to static frontend files
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
FRONTEND_DIR.mkdir(parents=True, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup and shutdown lifecycle operations including automation loop instantiation."""
    logger.info("Starting up Smart Solar EV Charging Server...")
    
    # 1. Initialize SQLite Database Schema
    await init_db()
    
    # 2. Derive Vault Cryptographic Key in-memory
    try:
        await CryptographicVault.get_key()
    except Exception as e:
        logger.error(f"Critical: Failed to initialize Cryptographic Vault: {e}")
        
    # 3. Aggregate past telemetry and prune raw records older than 7 days
    try:
        await aggregate_and_prune()
    except Exception as e:
        logger.error(f"Failed database aggregation and pruning: {e}")
        
    # 4. Initialize Local Inverter UDP Driver connection
    await goodwe_driver.connect()
    
    # 5. Initialize Tesla Owner Client Driver
    await tesla_driver.connect()
    
    # 6. Kick off the 10-second smart solar tracking loop
    await controller.start_loop()
    
    yield
    
    # Shutdown operations
    logger.info("Shutting down Smart Solar EV Charging Server...")
    controller.stop_loop()


app = FastAPI(
    title="Tesla Solar Sync Controller",
    description="Neo-Futuristic Steampunk zero-grid-export home energy and charging system.",
    lifespan=lifespan
)

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for API validations
class OverrideRequest(BaseModel):
    active: bool
    target_amps: int = 5

class ConfigUpdateRequest(BaseModel):
    grid_phases: int
    ema_alpha: float
    override_duration_mins: int

class AuthCallbackRequest(BaseModel):
    redirect_url: str


async def build_consolidated_status() -> Dict[str, Any]:
    """Compiles local configuration, telemetry, override timers, and driver telemetry."""
    override = await get_override_state()
    vehicle_status = await tesla_driver.get_vehicle_status()
    charge_state = vehicle_status.get("charge_state", {})
    
    # Calculate active EV current and power draw based on database config phases
    phases = int(await get_config_val("grid_phases", str(config.GRID_PHASES)))
    volt_per_amp = 690.0 if phases == 3 else 230.0
    
    is_charging = charge_state.get("charging_state") == "Charging"
    active_current = charge_state.get("charge_current_request", 0) if is_charging else 0
    active_ev_power_w = active_current * volt_per_amp
    
    # Fetch GoodWe telemetry
    telemetry = await goodwe_driver.get_telemetry(current_charge_power_w=active_ev_power_w)
    
    # Compute manual override countdown seconds remaining
    override_secs_left = 0.0
    if override["active"]:
        now = time.time()
        elapsed_secs = now - override["start_time"]
        total_secs = override["duration_mins"] * 60.0
        override_secs_left = max(0.0, total_secs - elapsed_secs)
        
    return {
        "timestamp": time.time(),
        "config": {
            "grid_phases": phases,
            "ema_alpha": float(await get_config_val("ema_alpha", str(config.EMA_ALPHA))),
            "override_duration_mins": override["duration_mins"]
        },
        "telemetry": {
            "solar_power_w": telemetry.solar_power_w,
            "house_consumption_w": telemetry.house_consumption_w,
            "grid_export_w": telemetry.grid_export_w,
            "is_mock_inverter": telemetry.is_mock
        },
        "tesla": {
            "display_name": vehicle_status.get("display_name", "Dynamo"),
            "state": vehicle_status.get("state", "offline"),
            "charging_state": charge_state.get("charging_state", "Stopped"),
            "charge_current_request": charge_state.get("charge_current_request", 5),
            "battery_level": charge_state.get("battery_level", 0),
            "charge_energy_added": charge_state.get("charge_energy_added", 0.0),
            "is_mock_tesla": vehicle_status.get("is_mock", True)
        },
        "override": {
            "active": override["active"],
            "target_amps": override["target_amps"],
            "seconds_remaining": int(override_secs_left)
        }
    }


# REST Endpoints
@app.get("/api/v1/status")
async def get_status():
    """Returns the consolidated dashboard system status."""
    return await build_consolidated_status()

@app.post("/api/v1/override")
async def post_override(req: OverrideRequest):
    """Engages or cancels manual charging current override."""
    if req.active:
        if not (5 <= req.target_amps <= 16):
            raise HTTPException(status_code=400, detail="Override amperage must be within safe [5A - 16A] range.")
        start_time = time.time()
        await set_override_state(active=True, target_amps=req.target_amps, start_time=start_time)
        logger.info(f"Manual Override engaged: {req.target_amps}A for {config.OVERRIDE_DURATION_MINS} minutes.")
        
        # Trigger an immediate loop iteration to send the command to the vehicle rapidly
        asyncio.create_task(controller.poll_and_control_once())
    else:
        await set_override_state(active=False)
        logger.info("Manual Override disengaged. Reverted to smart solar tracking.")
        asyncio.create_task(controller.poll_and_control_once())
        
    return {"status": "success", "override": await get_override_state()}

@app.get("/api/v1/config")
async def get_config():
    """Fetches key editable configurations."""
    return {
        "grid_phases": int(await get_config_val("grid_phases", str(config.GRID_PHASES))),
        "ema_alpha": float(await get_config_val("ema_alpha", str(config.EMA_ALPHA))),
        "override_duration_mins": int(await get_config_val("override_duration_mins", str(config.OVERRIDE_DURATION_MINS)))
    }

@app.post("/api/v1/config")
async def post_config(req: ConfigUpdateRequest):
    """Updates key configurations in DB."""
    if req.grid_phases not in (1, 3):
        raise HTTPException(status_code=400, detail="Grid connection phases must be either 1 or 3.")
    if not (0.01 <= req.ema_alpha <= 1.0):
        raise HTTPException(status_code=400, detail="EMA coefficient alpha must be within [0.01 - 1.0] bounds.")
    if req.override_duration_mins < 1:
        raise HTTPException(status_code=400, detail="Override duration must be at least 1 minute.")
        
    await set_config_val("grid_phases", str(req.grid_phases))
    await set_config_val("ema_alpha", f"{req.ema_alpha:.4f}")
    await set_config_val("override_duration_mins", str(req.override_duration_mins))
    
    logger.info("Global system configurations updated.")
    return {"status": "success"}

@app.get("/api/v1/analytics/history")
async def get_history():
    """Queries raw telemetry logs (recent 100 entries) and daily aggregates for CRT plotting."""
    telemetry_raw = await get_recent_telemetry(100)
    daily_aggregates = await get_daily_analytics(30)
    return {
        "telemetry_recent": telemetry_raw,
        "daily_aggregates": daily_aggregates
    }

@app.get("/api/v1/auth")
async def get_auth():
    """Generates and returns the secure Tesla SSO login redirect URL."""
    try:
        url = tesla_driver.get_auth_url()
        return {"auth_url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate Tesla auth URL: {e}")

@app.post("/api/v1/auth/callback")
async def post_auth_callback(req: AuthCallbackRequest):
    """Exchanges browser SSO redirect URL for secure encrypted resting tokens."""
    try:
        success = await tesla_driver.fetch_token(req.redirect_url)
        if success:
            return {"status": "success", "message": "Tesla credentials securely registered."}
        else:
            raise HTTPException(status_code=400, detail="SSO login completed but no vehicles found on account.")
    except Exception as e:
        logger.error(f"Tesla Auth callback registration failure: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# WebSocket 1 Hz high-frequency telemetry streaming
@app.websocket("/api/v1/live")
async def websocket_live(websocket: WebSocket):
    """Establishes a 1 Hz real-time status stream for visual UI animations."""
    await websocket.accept()
    logger.info(f"WebSocket Client Connected: {websocket.client}")
    
    keep_streaming = True
    
    async def receive_listener():
        nonlocal keep_streaming
        try:
            while keep_streaming:
                # Keep checking for client disconnects or heartbeats
                msg = await websocket.receive_text()
                # If client sends a manual command or config ping
                logger.debug(f"WS client sent: {msg}")
        except WebSocketDisconnect:
            logger.info("WS connection terminated by client.")
            keep_streaming = False
        except Exception as e:
            logger.warning(f"Error in WS receive handler: {e}")
            keep_streaming = False

    # Spawn concurrent reader task to catch disconnects instantly
    read_task = asyncio.create_task(receive_listener())
    
    try:
        while keep_streaming:
            status = await build_consolidated_status()
            await websocket.send_text(json.dumps(status))
            
            # Lock pacing strictly to 1 Hz
            await asyncio.sleep(1.0)
    except Exception as e:
        logger.warning(f"Error in WS write loop: {e}")
    finally:
        keep_streaming = False
        read_task.cancel()
        try:
            await websocket.close()
        except Exception:
            pass
        logger.info(f"WS connection cleaned up for {websocket.client}")

# Mount static frontend directory at the root to serve Vanilla app
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
