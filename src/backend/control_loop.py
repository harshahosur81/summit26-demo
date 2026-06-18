import asyncio
import logging
import time
from typing import Dict, Any, Optional, Tuple
from src.backend.config import config
from src.backend.database import get_override_state, set_override_state, log_telemetry
from src.backend.drivers.goodwe_driver import GoodWeDriver, InverterTelemetry
from src.backend.drivers.tesla_driver import TeslaDriver

logger = logging.getLogger("solar_sync.control_loop")

class ChargingController:
    """
    Core automation loop implementing zero-grid-export logic.
    Calculates charging current scaling and manages override timers.
    """
    def __init__(self, goodwe_driver: GoodWeDriver, tesla_driver: TeslaDriver):
        self.goodwe = goodwe_driver
        self.tesla = tesla_driver
        self.smoothed_surplus_w = 0.0
        self.is_initialized = False
        self.last_loop_time = 0.0
        self.running_task: Optional[asyncio.Task] = None
        self.is_running = False

    def calculate_target_current(self, telemetry: InverterTelemetry, current_amps: int, grid_phases: int, ema_alpha: float) -> Tuple[int, str]:
        """
        Pure mathematical logic determining the target amperage [5A - 16A].
        Returns a tuple: (target_amps, action_string)
        
        Where action_string can be: "START", "STOP", "HOLD", "SCALE_UP", "SCALE_DOWN"
        """
        volt_per_amp = 690.0 if grid_phases == 3 else 230.0
        
        # Calculate current EV charging power draw
        # If vehicle is stopped, power draw is 0W
        current_ev_power = (current_amps * volt_per_amp) if current_amps >= 5 else 0.0
        
        # Total household solar surplus available for EV charging is:
        # What is currently being exported to the grid + what the EV is already using
        raw_surplus_w = telemetry.grid_export_w + current_ev_power
        
        # Initialize EMA smoothing if first run
        if not self.is_initialized:
            self.smoothed_surplus_w = raw_surplus_w
            self.is_initialized = True
        else:
            # Apply EMA smoothing to the available surplus to prevent rapid oscillation
            self.smoothed_surplus_w = (ema_alpha * raw_surplus_w) + ((1.0 - ema_alpha) * self.smoothed_surplus_w)
            
        # FAST-BYPASS: Immediate drop/pause on grid import
        # If we are actively importing from the grid (grid_export < 0), we bypass smoothing
        # and trigger immediate scale-down or shutdown to maintain zero-grid-export efficiency
        if telemetry.grid_export_w < -100.0: # Allow a minor 100W buffer to avoid micro-switching
            logger.info(f"Grid Import Detected ({telemetry.grid_export_w}W). Immediate scale-down bypass triggered.")
            return 0, "STOP"
            
        # Convert smoothed surplus to available current
        target_amps = int(self.smoothed_surplus_w // volt_per_amp)
        
        # Clamping and State Machine Logic
        if target_amps < 5:
            # Not enough surplus to meet the 5A minimum vehicle requirement
            return 0, "STOP"
        elif target_amps > 16:
            # Exceeds max 16A limit, clamp to max
            return 16, "SCALE_UP" if current_amps < 16 else "HOLD"
        else:
            # Within safe [5A - 16A] range
            if current_amps < 5:
                return target_amps, "START"
            elif target_amps > current_amps:
                return target_amps, "SCALE_UP"
            elif target_amps < current_amps:
                return target_amps, "SCALE_DOWN"
            else:
                return target_amps, "HOLD"

    async def poll_and_control_once(self):
        """Executes a single cycle of the control loop (designed for 10-second pacing)."""
        try:
            # 1. Read Manual Override State from DB
            override = await get_override_state()
            now = time.time()
            
            # Fetch current vehicle status
            vehicle_status = await self.tesla.get_vehicle_status()
            charge_state = vehicle_status.get("charge_state", {})
            current_amps = charge_state.get("charge_current_request", 5)
            charging_state = charge_state.get("charging_state", "Stopped")
            
            # Translate charging state string to virtual internal current (0 if stopped)
            active_current = current_amps if charging_state in ("Charging", "Complete") else 0
            
            # Power draw based on active current and grid phases configuration
            from src.backend.database import get_config_val
            phases = int(await get_config_val("grid_phases", str(config.GRID_PHASES)))
            volt_per_amp = 690.0 if phases == 3 else 230.0
            active_ev_power_w = active_current * volt_per_amp
            
            # 2. Query GoodWe Inverter Telemetry
            telemetry = await self.goodwe.get_telemetry(current_charge_power_w=active_ev_power_w)
            
            # 3. Handle Manual Override Expiry Check
            is_override_active = override["active"]
            if is_override_active:
                elapsed_mins = (now - override["start_time"]) / 60.0
                if elapsed_mins >= override["duration_mins"]:
                    logger.info(f"Manual override expired ({elapsed_mins:.1f} mins elapsed). Reverting to smart solar tracking.")
                    await set_override_state(active=False)
                    is_override_active = False
                    
            # 4. Core Charging Logic
            if is_override_active:
                target_amps = override["target_amps"]
                logger.debug(f"Manual Override active. Driving vehicle to {target_amps}A.")
                
                # Apply current limit command
                if target_amps >= 5:
                    if charging_state != "Charging":
                        await self.tesla.start_charging()
                    await self.tesla.set_charge_current(target_amps)
                else:
                    if charging_state == "Charging":
                        await self.tesla.stop_charging()
            else:
                # Run Smart Solar Tracking Automation
                ema_alpha = float(await get_config_val("ema_alpha", str(config.EMA_ALPHA)))
                
                target_amps, action = self.calculate_target_current(
                    telemetry=telemetry,
                    current_amps=active_current,
                    grid_phases=phases,
                    ema_alpha=ema_alpha
                )
                
                logger.info(f"Smart Solar Control calculation: Surplus={self.smoothed_surplus_w:.0f}W, Target={target_amps}A, Action={action}")
                
                # Execute actions on vehicle
                if action == "STOP":
                    if charging_state == "Charging":
                        await self.tesla.stop_charging()
                elif action == "START":
                    await self.tesla.wake_up()
                    await self.tesla.start_charging()
                    await self.tesla.set_charge_current(target_amps)
                elif action in ("SCALE_UP", "SCALE_DOWN"):
                    await self.tesla.set_charge_current(target_amps)
                elif action == "HOLD":
                    # Keep current charging current
                    pass
            
            # 5. Log telemetry row to database for 7-day high resolution storage
            # Fetch updated vehicle status for accurate logging
            updated_status = await self.tesla.get_vehicle_status()
            updated_charge = updated_status.get("charge_state", {})
            updated_amps = updated_charge.get("charge_current_request", 0) if updated_charge.get("charging_state") == "Charging" else 0
            
            await log_telemetry(
                solar_power_w=telemetry.solar_power_w,
                household_consumption_w=telemetry.house_consumption_w,
                grid_export_w=telemetry.grid_export_w,
                tesla_charge_amps=updated_amps,
                tesla_state=updated_charge.get("charging_state", "Stopped")
            )
            
        except Exception as e:
            logger.error(f"Error in Charging Control Loop tick: {e}", exc_info=True)

    async def start_loop(self):
        """Starts the asynchronous 10-second automation task loop."""
        if self.is_running:
            return
        self.is_running = True
        self.is_initialized = False
        
        async def loop():
            while self.is_running:
                start_time = time.time()
                await self.poll_and_control_once()
                elapsed = time.time() - start_time
                
                # Pace loop exactly to 10-seconds minus execution time
                sleep_dur = max(1.0, 10.0 - elapsed)
                await asyncio.sleep(sleep_dur)
                
        self.running_task = asyncio.create_task(loop())
        logger.info("Automation control loop started (10-second interval).")

    def stop_loop(self):
        """Stops the control loop task."""
        self.is_running = False
        if self.running_task:
            self.running_task.cancel()
            self.running_task = None
        logger.info("Automation control loop stopped.")
