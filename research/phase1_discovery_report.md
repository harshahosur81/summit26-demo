# Phase 1 Discovery Report: GoodWe (UDP 8899) & TeslaPy Smart Solar EV Charging

This report details the technical discovery, integration audits, and architectural constraints identified during Phase 1 of the Smart Solar EV Charging system. It has been updated to reflect the user's specific physical hardware and network parameters.

---

## 1. Inverter Integration Analysis (GoodWe Local UDP)

### Local UDP Polling (Primary)
*   **Protocol:** Proprietary GoodWe local UDP polling over port `8899`.
*   **Inverter Hardware:** GoodWe Hybrid Inverter (ET/EH/ES/SEC series) connected to the local network via a LAN or Wi-Fi dongle.
*   **IP Resolution:** Assigned a **static local IP** via DHCP reservation.
*   **Integration Library:** PyPI open-source **`goodwe`** library (asynchronous Python client).
*   **Smart Meter Telemetry:** The library communicates with the inverter via local UDP port 8899 to read real-time registers from the grid smart meter (Chint/Eastron DTSU666).
*   **Critical Sensor IDs:**
    *   `active_power`: Power measured by the smart meter at the grid boundary (Positive = Grid Export / Surplus; Negative = Grid Import).
    *   `house_consumption`: Household load consumption in Watts.
    *   `ppv`: Total PV generation power in Watts.
*   **Decision:** The system will use the **`goodwe`** Python library to perform local asynchronous UDP polling on port 8899. This avoids the need for Modbus TCP (port 502) setup and is highly reliable, with low latency (sub-second queries).

---

## 2. Vehicle Control Integration (TeslaPy)

### Authentication & Token Security
*   **Library:** `teslapy` (Python 3) using Tesla's OAuth2 SSO service.
*   **Token Storage:** PERSISTED locally in `cache.json` with secure file permissions (`600`).
*   **Authentication Flow:** One-time manual login step where the user logs into the official Tesla SSO portal in a browser and pastes the resulting redirect URL into the backend console, fully supporting Multi-Factor Authentication (MFA).
*   **Token Refresh:** Automated by the library using the OAuth2 `refresh_token` flow upon expiry.

### Vehicle Command Set
*   **Wake Up:** `vehicle.sync_wake_up()` - pulls the car from deep sleep to receive commands.
*   **Set Charge Current:** `vehicle.command('CHARGING_AMPS', charging_amps=I_target)`
    *   *Constraint:* Accepted range is integers `[5, 16]` based on standard Model 3/Y three-phase charging limits.
*   **Start Charge:** `vehicle.command('START_CHARGE')` (used to start a session when surplus crosses 5A threshold).
*   **Stop Charge:** `vehicle.command('STOP_CHARGE')` (used to suspend a session when solar is insufficient).

---

## 3. Dynamic Control Logic & Three-Phase Calculations

The household and charging setup uses a **Three-Phase Supply (400V AC)**. This introduces specific power scaling parameters that differ from standard single-phase equations:

### Three-Phase Power Scaling
Charging power on three-phase scales at **~690 Watts per Ampere**:
$$\text{Power (W)} = 3 \times 230\text{V} \times I_{\text{amps}} \approx 690 \cdot I_{\text{amps}}$$

*   **Minimum Charging Current (5A):**
    $$P_{\text{min}} = 3 \times 230\text{V} \times 5\text{A} = 3450\text{W}$$
    *The automation loop will only initiate charging when smoothed excess solar surplus exceeds **3,450 Watts**.*
*   **Maximum Charging Current (16A):**
    $$P_{\text{max}} = 3 \times 230\text{V} \times 16\text{A} = 11040\text{W}$$
    *The maximum rate at which the Tesla will charge on this three-phase connection is **11.04 kW**.*

### Smoothing Heuristics
To protect the vehicle's electrical contactors and prevent rapid, cloud-induced current flickering:
1.  **Exponential Moving Average (EMA):**
    We smooth the raw `active_power` export readings using an EMA ($\alpha = 0.1$, corresponding to a ~100-second smoothing window):
    $$P_{\text{smooth}, t} = \alpha \cdot P_{\text{raw}, t} + (1 - \alpha) \cdot P_{\text{smooth}, t-1}$$
2.  **Fast Drop / Slow Climb Hysteresis:**
    *   **Cloud Drop:** If export drops below 0W (importing), we immediately reduce amperage to 5A or suspend charging to prevent grid import.
    *   **Solar Surge:** If export surges, we increment the current slowly (maximum +2A per 20 seconds) to ensure the solar output is stable.
3.  **Contactor Protection Timer:**
    When suspending charging (solar drops below 5A equivalent for more than 3 minutes), the system pauses. A minimum of **3 minutes** must elapse before restarting a charging session to protect the vehicle's electrical contactors.

---

## 4. Proposed Technical Architecture & Topology

*   **Backend Runtime:** Python 3.10+ (to leverage the `teslapy` and `goodwe` async libraries).
*   **Backend Server:** **FastAPI** (asynchronous, highly performant, type-safe API schemas).
*   **Local Storage:** **SQLite** for database logging and transient state.
*   **Frontend Interface:** Modern, glassmorphic single-page web app built with Vanilla JS, HTML5, and CSS, served directly from the FastAPI backend.
*   **Inter-Process Communication:** FastAPI exposes REST endpoints and WebSockets for real-time telemetry streaming to the UI.

---

## 5. Summary of Integration Boundaries

| Parameter | Constraint / Value | Source |
| :--- | :--- | :--- |
| **Inverter Address** | Configurable IP on Local LAN (Static) | Local Router (DHCP) |
| **Inverter UDP Port** | `8899` | GoodWe UDP Specification |
| **Inverter Library** | `goodwe` (PyPI library) | Open Source Community |
| **Tesla Min Amperage** | `5A` (~3.45 kW on three-phase) | Tesla API Boundary |
| **Tesla Max Amperage** | `16A` (~11.04 kW on three-phase) | User Hardware Constraint |
| **Telemetry Cadence** | `10 seconds` (Active charging) | SDD Constraint |
| **MFA Authentication** | Browser SSO Redirect URL paste | Tesla Auth Flow |
| **Encryption (at rest)** | AES-256-GCM for credentials (or secure JSON file) | Security Standard |
