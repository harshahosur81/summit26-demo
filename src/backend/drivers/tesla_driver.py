import asyncio
import logging
import time
from typing import Optional, Dict, Any
import teslapy
from src.backend.config import config
from src.backend.vault import CryptographicVault

logger = logging.getLogger("solar_sync.tesla_driver")

class MockTeslaVehicle:
    """
    Simulates a physical Tesla Model 3 / Y battery and charger unit.
    Safely clamps control currents to [5A - 16A] and increments virtual SoC in memory.
    """
    def __init__(self):
        self.is_awake = True
        self.charging_state = "Stopped"  # "Charging", "Stopped", "Complete"
        self.charge_current_request = 5  # Start at 5A min
        self.battery_level = 62          # 62% starting state of charge
        self.charge_limit_soc = 80       # 80% default target
        self.charge_energy_added = 0.0   # Added energy in kWh
        self.last_sim_time = time.time()

    def simulate_step(self):
        """Simulates battery SoC accumulation based on current charging rate."""
        now = time.time()
        elapsed = now - self.last_sim_time
        self.last_sim_time = now

        if self.charging_state == "Charging" and self.battery_level < self.charge_limit_soc:
            # Power (kW) = Current (A) * Voltage (230V) * Phases (3) / 1000
            # To make simulation visible, we accelerate SoC growth rate by 60x (1 real-world minute = 1 hour)
            # Power = Amps * Volt-constant. Assume 230V per phase.
            # Three-phase power is approx Amps * 690W. Single phase is Amps * 230W.
            # Let's read grid phases (could be 1 or 3)
            # For simplicity, let's assume Three-Phase (690W/A) for power calculation
            power_kw = (self.charge_current_request * 690.0) / 1000.0
            
            # Energy added (kWh) = power_kw * hours
            # elapsed is in seconds. Normal rate: elapsed / 3600.
            # Accelerated 60x rate: elapsed * 60 / 3600 = elapsed / 60
            added_kwh = power_kw * (elapsed / 60.0)
            self.charge_energy_added += added_kwh
            
            # 1% SoC of a 60 kWh battery is 0.6 kWh
            battery_capacity_kwh = 60.0
            soc_added = (added_kwh / battery_capacity_kwh) * 100.0
            self.battery_level = min(float(self.charge_limit_soc), self.battery_level + soc_added)
            
            if self.battery_level >= self.charge_limit_soc:
                self.charging_state = "Complete"
                logger.info("Mock Tesla: Battery charging completed (reached target limit).")

    def sync_wake_up(self) -> bool:
        self.is_awake = True
        logger.info("Mock Tesla: Wake-up command received.")
        return True

    def command(self, name: str, **kwargs) -> Dict[str, Any]:
        """Intercepts all vehicle command protocols."""
        self.simulate_step()
        logger.info(f"Mock Tesla received command: {name} with args: {kwargs}")
        
        if name == "START_CHARGE":
            if self.battery_level >= self.charge_limit_soc:
                self.charging_state = "Complete"
            else:
                self.charging_state = "Charging"
            return {"result": True, "reason": ""}
            
        elif name == "STOP_CHARGE":
            self.charging_state = "Stopped"
            return {"result": True, "reason": ""}
            
        elif name == "CHARGING_AMPS":
            amps = int(kwargs.get("charging_amps", 5))
            # Strict safety clamps as specified in requirements
            if not (5 <= amps <= 16):
                logger.error(f"Mock Tesla: Out-of-bounds current requested: {amps}A. Clamping to safety bounds.")
                amps = max(5, min(16, amps))
            self.charge_current_request = amps
            return {"result": True, "reason": ""}
            
        return {"result": True, "reason": "Unknown command simulated."}

    def get_vehicle_data(self) -> Dict[str, Any]:
        """Simulates vehicle state dictionary matching TeslaPy API structure."""
        self.simulate_step()
        return {
            "display_name": "Steampunk Dynamo (Mock)",
            "state": "online" if self.is_awake else "asleep",
            "charge_state": {
                "charging_state": self.charging_state,
                "charge_current_request": self.charge_current_request,
                "charge_limit_soc": self.charge_limit_soc,
                "battery_level": int(self.battery_level),
                "charge_energy_added": round(self.charge_energy_added, 2)
            }
        }


class TeslaDriver:
    """Unified controller wrapper interface for TeslaPy or Mock vehicle controls."""
    
    def __init__(self):
        self.tesla: Optional[teslapy.Tesla] = None
        self.vehicle: Optional[Any] = None
        self.mock_vehicle = MockTeslaVehicle()
        self.is_running_mock = False
        
    async def connect(self) -> bool:
        """Initializes connection to Tesla API or switches to Mock mode."""
        if config.is_mock_tesla:
            logger.info("TESLA_EMAIL unconfigured or set to default. Running Tesla Driver in Mock/Emulation mode.")
            self.is_running_mock = True
            return True
            
        try:
            logger.info(f"Initializing TeslaPy Connection for {config.TESLA_EMAIL}...")
            # Set up the derived key in CryptographicVault first (required for sync wrappers)
            await CryptographicVault.get_key()
            
            # Initialize Tesla class with our secure synchronous file-rest interceptors
            self.tesla = teslapy.Tesla(
                email=config.TESLA_EMAIL,
                cache_loader=CryptographicVault.load_tesla_cache_sync,
                cache_dumper=CryptographicVault.save_tesla_cache_sync
            )
            
            # Check if we already have a cached token
            if self.tesla.authorized:
                logger.info("TeslaPy successfully authorized from secure resting Vault.")
                # Retrieve first vehicle
                vehicles = self.tesla.vehicle_list()
                if vehicles:
                    self.vehicle = vehicles[0]
                    self.is_running_mock = False
                    logger.info(f"Connected to physical Tesla Vehicle: '{self.vehicle['display_name']}'")
                    return True
                else:
                    logger.warning("No vehicles found on Tesla account. Falling back to Mock Vehicle.")
                    self.is_running_mock = True
                    return True
            else:
                logger.warning("No authorized Tesla token cache found. Starting in Mock Mode until web authentication is performed.")
                self.is_running_mock = True
                return True
                
        except Exception as e:
            logger.error(f"Failed to initialize Tesla API: {e}. Defaulting to Mock Mode.")
            self.is_running_mock = True
            return True

    def get_auth_url(self) -> str:
        """Generates the official secure Tesla SSO login redirect URL for web-flow browser login."""
        if self.is_running_mock or self.tesla is None:
            # We initialize a temporary Tesla instance if needed
            self.tesla = teslapy.Tesla(
                email=config.TESLA_EMAIL or "user@example.com",
                cache_loader=CryptographicVault.load_tesla_cache_sync,
                cache_dumper=CryptographicVault.save_tesla_cache_sync
            )
        return self.tesla.authorization_url()

    async def fetch_token(self, redirect_url: str) -> bool:
        """
        Receives the redirect callback URL from browser SSO, exchanges it for tokens,
        encrypts it into Vault, and switches from Mock Mode to Active Real Mode.
        """
        if self.tesla is None:
            return False
            
        try:
            logger.info("Exchanging SSO redirect URL callback for Tesla API access tokens...")
            # Synchronously runs in threadpool to avoid blocking event loop
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None, 
                lambda: self.tesla.fetch_token(authorization_response=redirect_url)
            )
            
            logger.info("Successfully authenticated with Tesla SSO!")
            # Retrieve physical vehicle list
            vehicles = self.tesla.vehicle_list()
            if vehicles:
                self.vehicle = vehicles[0]
                self.is_running_mock = False
                logger.info(f"Switched to Real Tesla Vehicle: '{self.vehicle['display_name']}'")
                return True
            else:
                logger.warning("No vehicles found on this account. Staying in Mock Mode.")
                return False
        except Exception as e:
            logger.error(f"Tesla SSO Token exchange failed: {e}")
            raise ValueError(f"SSO Token exchange failed: {e}")

    async def get_vehicle_status(self) -> Dict[str, Any]:
        """Queries telemetry metrics and charge details."""
        if self.is_running_mock or self.vehicle is None:
            return {
                **self.mock_vehicle.get_vehicle_data(),
                "is_mock": True
            }
            
        try:
            # Query the vehicle state
            # If vehicle is asleep, this might raise an exception or return stale data.
            # In a real controller loop, we only request high-resolution charging data if awake.
            vehicle_data = self.vehicle.get_vehicle_data()
            state = vehicle_data.get("state", "offline")
            
            # Default fallback dict
            charge_state = {
                "charging_state": "Stopped",
                "charge_current_request": 5,
                "charge_limit_soc": 80,
                "battery_level": 50,
                "charge_energy_added": 0.0
            }
            
            if state == "online":
                charge_state_raw = vehicle_data.get("charge_state", {})
                charge_state = {
                    "charging_state": charge_state_raw.get("charging_state", "Stopped"),
                    "charge_current_request": int(charge_state_raw.get("charge_current_request", 5)),
                    "charge_limit_soc": int(charge_state_raw.get("charge_limit_soc", 80)),
                    "battery_level": int(charge_state_raw.get("battery_level", 50)),
                    "charge_energy_added": float(charge_state_raw.get("charge_energy_added", 0.0))
                }
                
            return {
                "display_name": vehicle_data.get("display_name", "Tesla"),
                "state": state,
                "charge_state": charge_state,
                "is_mock": False
            }
        except Exception as e:
            logger.warning(f"Failed to poll physical Tesla vehicle: {e}. Returning mock telemetry.")
            return {
                **self.mock_vehicle.get_vehicle_data(),
                "is_mock": True
            }

    async def wake_up(self) -> bool:
        """Sends wake_up pulse sequence to vehicle."""
        if self.is_running_mock or self.vehicle is None:
            return self.mock_vehicle.sync_wake_up()
            
        try:
            logger.info("Waking up physical Tesla vehicle...")
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self.vehicle.sync_wake_up)
            logger.info("Vehicle reports online!")
            return True
        except Exception as e:
            logger.error(f"Failed to wake up Tesla: {e}")
            return False

    async def start_charging(self) -> bool:
        """Sends start charge command to vehicle."""
        if self.is_running_mock or self.vehicle is None:
            res = self.mock_vehicle.command("START_CHARGE")
            return res["result"]
            
        try:
            logger.info("Sending START_CHARGE command...")
            loop = asyncio.get_running_loop()
            res = await loop.run_in_executor(None, lambda: self.vehicle.command("START_CHARGE"))
            return res.get("result", False)
        except Exception as e:
            logger.error(f"Failed to start charging: {e}")
            return False

    async def stop_charging(self) -> bool:
        """Sends stop charge command to vehicle."""
        if self.is_running_mock or self.vehicle is None:
            res = self.mock_vehicle.command("STOP_CHARGE")
            return res["result"]
            
        try:
            logger.info("Sending STOP_CHARGE command...")
            loop = asyncio.get_running_loop()
            res = await loop.run_in_executor(None, lambda: self.vehicle.command("STOP_CHARGE"))
            return res.get("result", False)
        except Exception as e:
            logger.error(f"Failed to stop charging: {e}")
            return False

    async def set_charge_current(self, amps: int) -> bool:
        """Safely sends charging current adjustment command [5A - 16A]."""
        # Enforce strict safety boundary clamping
        amps_clamped = max(5, min(16, amps))
        if amps != amps_clamped:
            logger.warning(f"Charge current requested: {amps}A was clamped to safety range: {amps_clamped}A.")
            
        if self.is_running_mock or self.vehicle is None:
            res = self.mock_vehicle.command("CHARGING_AMPS", charging_amps=amps_clamped)
            return res["result"]
            
        try:
            logger.info(f"Sending CHARGING_AMPS command at {amps_clamped}A...")
            loop = asyncio.get_running_loop()
            res = await loop.run_in_executor(
                None, 
                lambda: self.vehicle.command("CHARGING_AMPS", charging_amps=amps_clamped)
            )
            return res.get("result", False)
        except Exception as e:
            logger.error(f"Failed to set charging current to {amps_clamped}A: {e}")
            return False
