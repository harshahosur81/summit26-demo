import pytest
from src.backend.drivers.goodwe_driver import InverterTelemetry
from src.backend.control_loop import ChargingController

def test_three_phase_math():
    """Verifies three-phase charging scaling at 690W per Ampere."""
    controller = ChargingController(None, None)
    
    # 3 phases, ema_alpha = 1.0 (no smoothing, pure raw surplus)
    # Household currently exporting 4000W, Tesla charging at 6A
    # Available surplus = 4000W + (6A * 690W/A) = 4000 + 4140 = 8140W
    # 8140W // 690W/A = 11A target
    telemetry = InverterTelemetry(solar_power_w=10000, house_consumption_w=1860, grid_export_w=4000)
    
    target, action = controller.calculate_target_current(
        telemetry=telemetry,
        current_amps=6,
        grid_phases=3,
        ema_alpha=1.0
    )
    
    assert target == 11
    assert action == "SCALE_UP"

def test_single_phase_math():
    """Verifies single-phase charging scaling at 230W per Ampere."""
    controller = ChargingController(None, None)
    
    # 1 phase, ema_alpha = 1.0 (no smoothing)
    # Household exporting 1000W, Tesla charging at 6A
    # Available surplus = 1000W + (6A * 230W/A) = 1000 + 1380 = 2380W
    # 2380W // 230W/A = 10A target
    telemetry = InverterTelemetry(solar_power_w=3000, house_consumption_w=620, grid_export_w=1000)
    
    target, action = controller.calculate_target_current(
        telemetry=telemetry,
        current_amps=6,
        grid_phases=1,
        ema_alpha=1.0
    )
    
    assert target == 10
    assert action == "SCALE_UP"

def test_safety_clamps():
    """Verifies the charging currents are safely clamped to [5A - 16A]."""
    controller = ChargingController(None, None)
    
    # CASE 1: Extremely high surplus should clamp to 16A max
    # Surplus available = 15000W -> ~21A, must clamp to 16A
    telemetry1 = InverterTelemetry(solar_power_w=18000, house_consumption_w=1000, grid_export_w=15000)
    target1, action1 = controller.calculate_target_current(
        telemetry=telemetry1,
        current_amps=16,
        grid_phases=3,
        ema_alpha=1.0
    )
    assert target1 == 16
    assert action1 == "HOLD"
    
    # CASE 2: Low surplus below the 5A threshold should trigger STOP (target = 0)
    # If EV is currently charging at 5A (3450W), but grid is importing -1500W:
    # Surplus available = -1500W + 3450W = 1950W (~2.8A, less than 5A minimum), must stop.
    telemetry2 = InverterTelemetry(solar_power_w=4000, house_consumption_w=2000, grid_export_w=-1500)
    target2, action2 = controller.calculate_target_current(
        telemetry=telemetry2,
        current_amps=5,
        grid_phases=3,
        ema_alpha=1.0
    )
    assert target2 == 0
    assert action2 == "STOP"

def test_immediate_stop_on_grid_import():
    """Verifies the fast-bypass mechanism instantly triggers STOP on grid imports (zero-grid-export safety)."""
    controller = ChargingController(None, None)
    
    # Set up some historical smoothed surplus (e.g. 8000W)
    controller.smoothed_surplus_w = 8000.0
    controller.is_initialized = True
    
    # Suddenly, a large house load turns on causing a heavy grid import of -2000W
    telemetry = InverterTelemetry(solar_power_w=2000, house_consumption_w=6000, grid_export_w=-2000)
    
    # Even with high historical smoothed surplus, if grid import is active, fast-bypass must instantly STOP charging
    target, action = controller.calculate_target_current(
        telemetry=telemetry,
        current_amps=8,
        grid_phases=3,
        ema_alpha=0.1  # Highly smoothed, would take long to drop otherwise
    )
    
    assert target == 0
    assert action == "STOP"

def test_ema_smoothing_accumulation():
    """Verifies that the surplus calculations accumulate correctly under EMA smoothing coefficients."""
    controller = ChargingController(None, None)
    
    # Initial state (telemetry export = 3450W -> 5A on 3-phase)
    # Surplus available = 3450W + 0W = 3450W
    telemetry1 = InverterTelemetry(solar_power_w=5000, house_consumption_w=1550, grid_export_w=3450)
    
    # First tick: Initializes smoothed surplus to the raw surplus (3450W)
    target1, _ = controller.calculate_target_current(
        telemetry=telemetry1,
        current_amps=0,
        grid_phases=3,
        ema_alpha=0.1
    )
    assert controller.smoothed_surplus_w == 3450.0
    assert target1 == 5  # 3450 // 690 = 5A
    
    # Second tick: Solar generation surges. We want raw surplus to be 8450W.
    # Since EV is currently drawing 5A (3450W), grid export should be 5000W (8450 - 3450).
    # Smoothed = 0.1 * 8450 + 0.9 * 3450 = 845 + 3105 = 3950W
    # 3950 // 690 = 5A (Should HOLD charging at 5A due to EMA smoothing, dampening spikes)
    telemetry2 = InverterTelemetry(solar_power_w=10000, house_consumption_w=1550, grid_export_w=5000)
    target2, action2 = controller.calculate_target_current(
        telemetry=telemetry2,
        current_amps=5,
        grid_phases=3,
        ema_alpha=0.1
    )
    
    assert round(controller.smoothed_surplus_w, 1) == 3950.0
    assert target2 == 5
    assert action2 == "HOLD"
