# GoodWe Local UDP Port 8899 Protocol Integration Notes

This research document details the local integration mapping for GoodWe hybrid and grid-tie inverters via the UDP port `8899` communication protocol.

## 1. Local Network Access Topology
*   **Protocol:** UDP (Connectionless)
*   **Default Port:** `8899`
*   **Inverter IP:** Assigned a static IP via DHCP reservation on the local router.
*   **Integration Library:** PyPI **`goodwe`** library (asynchronous Python client).
*   **How it Works:** The `goodwe` library connects asynchronously, sends query frames to port 8899, receives the raw binary streams, and parses them into structured sensor dictionary entries.

## 2. Key Telemetry Sensors
The `goodwe` library auto-detects the inverter model family (e.g., ET, EH, ES, SEC, etc.) and populates specific sensors. The sensors of interest for our automated dynamic charging are:

*   **`active_power` (W):**
    *   **Description:** Total active power measured at the grid connection point by the smart meter (Chint/Eastron DTSU666).
    *   **Sign Convention:**
        *   **Positive (+):** Grid Export (solar surplus flowing back into the grid).
        *   **Negative (-):** Grid Import (power being drawn from the grid to feed household loads).
*   **`house_consumption` (W):**
    *   **Description:** Real-time power being consumed by all household loads.
*   **`ppv` (W):**
    *   **Description:** Real-time solar PV generation output.
*   **`battery_soc` (%):**
    *   **Description:** State of Charge of the home battery (if any). Since the user does not have a Powerwall or external battery, this value may be absent or ignored.

## 3. Dynamic Current Calculation Formula (Three-Phase)
The home electrical supply is **three-phase 400V AC**. The charging power scales at **~690 Watts per Ampere** (3 phases × 230V):

$$\text{Power (W)} = 3 \times 230\text{V} \times I_{\text{amps}} \approx 690 \cdot I_{\text{amps}}$$

By reading `active_power` ($P_{\text{meter}}$) directly via the `goodwe` library, we calculate the surplus current $I_{\text{excess}}$:
$$I_{\text{excess}} = \frac{P_{\text{meter}}}{690}$$

*   **Start Charging Trigger:** Initiate when smoothed excess power $P_{\text{smooth}} \ge 3450\text{W}$ (which is equivalent to $5\text{A}$ minimum current on three-phase).
*   **Dynamic Scaling:**
    *   If $I_{\text{excess}} \ge 1$: We can safely increase the Tesla charging rate by $\lfloor I_{\text{excess}} \rfloor$ Amperes (up to a maximum of 16A).
    *   If $I_{\text{excess}} < 0$: We must immediately decrease the Tesla charging rate by $\lceil |I_{\text{excess}}| \rceil$ Amperes to avoid grid import.
*   **Stop Charging Trigger:** If smoothed excess power falls below 3450W for more than 3 minutes, suspend charging.

## 4. Code Implementation Example (Async Python)
```python
import asyncio
import goodwe

async def read_export_telemetry():
    # Inverter local static IP
    ip_address = '192.168.1.150'
    
    # Connect and auto-detect model
    inverter = await goodwe.connect(ip_address)
    
    # Read runtime data
    data = await inverter.read_runtime_data()
    
    # Read grid active power (smart meter)
    active_power = data.get('active_power', 0)
    
    print(f"Grid Active Power: {active_power} W")
    if active_power > 0:
        print(f"Solar Surplus: {active_power} W (Exporting)")
    else:
        print(f"Grid Draw: {abs(active_power)} W (Importing)")
        
    return active_power

asyncio.run(read_export_telemetry())
```
