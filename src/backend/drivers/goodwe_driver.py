import asyncio
import logging
import math
import time
from typing import Optional, Tuple, Dict, Any
import goodwe
from src.backend.config import config

logger = logging.getLogger("solar_sync.goodwe_driver")

class InverterTelemetry:
    """Standardized inverter and meter telemetry data package."""
    def __init__(self, solar_power_w: float, house_consumption_w: float, grid_export_w: float, is_mock: bool = False):
        self.solar_power_w = solar_power_w
        self.house_consumption_w = house_consumption_w
        self.grid_export_w = grid_export_w  # Positive = Export (surplus), Negative = Import
        self.is_mock = is_mock

    def to_dict(self) -> Dict[str, Any]:
        return {
            "solar_power_w": round(self.solar_power_w, 2),
            "house_consumption_w": round(self.house_consumption_w, 2),
            "grid_export_w": round(self.grid_export_w, 2),
            "is_mock": self.is_mock
        }

class MockGoodWeInverter:
    """
    Simulates a GoodWe hybrid inverter and smart meter telemetry.
    Compresses a full 24-hour diurnal cycle into exactly 15 minutes (900 seconds) of real-world time.
    """
    def __init__(self):
        self.max_solar_w = 7500.0  # 7.5 kW peak solar system
        self.base_load_w = 600.0   # 600W constant home base load
        self.cycle_duration_seconds = 900.0 # 15 minutes loop

    def get_telemetry(self, current_charge_power_w: float = 0.0) -> InverterTelemetry:
        """
        Computes synthetic telemetry data based on current real-world timestamp.
        """
        now = time.time()
        # Progress through the 15-minute simulated day (0.0 to 1.0)
        progress = (now % self.cycle_duration_seconds) / self.cycle_duration_seconds
        
        # Map progress to 24 simulated hours (0 to 24)
        sim_hour = progress * 24.0
        
        # Calculate solar power (sine curve between 6:00 and 18:00)
        if 6.0 <= sim_hour <= 18.0:
            # Normalized peak shape
            angle = math.pi * (sim_hour - 6.0) / 12.0
            solar_power = self.max_solar_w * math.sin(angle)
            
            # Simulate passing cloud dropouts (e.g. sharp drop between 11:00 and 12:00, or 14:00 and 14:30)
            if 11.0 <= sim_hour <= 11.7:
                # Passing heavy cloud - drops power by 80%
                solar_power *= 0.20
            elif 14.5 <= sim_hour <= 15.2:
                # Intermittent cloud - drops power by 50%
                solar_power *= 0.50
        else:
            solar_power = 0.0
            
        # Simulate household consumption with diurnal bumps (morning/evening peaks)
        # Bumps at 7:00-9:00 and 17:00-21:00
        house_consumption = self.base_load_w
        if 7.0 <= sim_hour <= 9.0:
            house_consumption += 1200.0 * math.sin(math.pi * (sim_hour - 7.0) / 2.0)
        elif 17.0 <= sim_hour <= 21.0:
            house_consumption += 1800.0 * math.sin(math.pi * (sim_hour - 17.0) / 4.0)
            
        # Add minor random load fluctuations (+/- 50W)
        random_fuzz = (math.sin(now * 0.5) * 30.0) + (math.cos(now * 0.1) * 20.0)
        house_consumption = max(100.0, house_consumption + random_fuzz)
        
        # Grid Export = Solar - House Consumption - EV Charging Power
        grid_export = solar_power - house_consumption - current_charge_power_w
        
        return InverterTelemetry(
            solar_power_w=solar_power,
            house_consumption_w=house_consumption,
            grid_export_w=grid_export,
            is_mock=True
        )

class GoodWeDriver:
    """Manages the connection, error handling, and polling of GoodWe local UDP telemetry."""
    
    def __init__(self):
        self.inverter: Optional[goodwe.Inverter] = None
        self.mock_inverter = MockGoodWeInverter()
        self.is_running_mock = False
        
    async def connect(self) -> bool:
        """Attempts to connect to the physical inverter. Falls back to mock if configuration says so."""
        if config.is_mock_inverter:
            logger.info("INVERTER_IP not configured. Initializing in Mock/Emulation mode.")
            self.is_running_mock = True
            return True
            
        try:
            logger.info(f"Attempting local UDP connection to GoodWe Inverter at {config.INVERTER_IP}...")
            # We wrap the connect call in a timeout of 3 seconds to avoid blocking startup
            self.inverter = await asyncio.wait_for(
                goodwe.connect(config.INVERTER_IP, port=8899, timeout=2, retries=2),
                timeout=5.0
            )
            logger.info(f"Successfully connected to GoodWe Inverter {self.inverter.model} (S/N: {self.inverter.serial_number})")
            self.is_running_mock = False
            return True
        except Exception as e:
            logger.error(f"Failed to connect to local GoodWe inverter at {config.INVERTER_IP}: {e}. Falling back to Mock/Emulation mode.")
            self.is_running_mock = True
            return True

    async def get_telemetry(self, current_charge_power_w: float = 0.0) -> InverterTelemetry:
        """
        Polls the inverter for real-time telemetry.
        If in mock mode or if the connection fails mid-operation, returns simulated telemetry.
        """
        if self.is_running_mock or self.inverter is None:
            return self.mock_inverter.get_telemetry(current_charge_power_w)
            
        try:
            # Read runtime parameters from the physical inverter via local UDP
            runtime_data = await asyncio.wait_for(
                self.inverter.read_runtime_data(),
                timeout=3.0
            )
            
            # Map standard sensors
            # 'ppv' = PV generation power (W)
            # 'house_consumption' = House consumption power (W)
            # 'active_power' = Grid active power (W). Positive is export, Negative is import.
            solar_power = float(runtime_data.get("ppv", 0.0))
            house_consumption = float(runtime_data.get("house_consumption", 0.0))
            grid_export = float(runtime_data.get("active_power", 0.0))
            
            # Note: Depending on inverter model, active_power representation may differ.
            # GoodWe ET/ES models typically report active_power as positive for export and negative for import.
            # If for some reason house_consumption is 0, we can calculate it: house_consumption = solar_power - grid_export - current_charge_power_w
            if house_consumption <= 0:
                house_consumption = max(50.0, solar_power - grid_export - current_charge_power_w)

            return InverterTelemetry(
                solar_power_w=solar_power,
                house_consumption_w=house_consumption,
                grid_export_w=grid_export,
                is_mock=False
            )
        except Exception as e:
            logger.warning(f"UDP telemetry poll failed: {e}. Temporarily falling back to Mock/Emulation data.")
            # Do not permanently drop connection, just return mock telemetry for this cycle
            return self.mock_inverter.get_telemetry(current_charge_power_w)
