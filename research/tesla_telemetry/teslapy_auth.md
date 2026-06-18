# TeslaPy Integration & Authentication Notes

This research document details the integration of the open-source `TeslaPy` Python library for vehicle telemetry and charging current control.

## 1. Overview of TeslaPy
*   **Library:** `teslapy` (https://github.com/tdorssers/TeslaPy)
*   **Purpose:** Exposes a Pythonic interface to the Tesla Owners API / Fleet API, handling OAuth2 flows, multi-factor authentication (MFA), token refresh, and vehicle commands.
*   **Dependencies:** `requests`, `requests_oauthlib`, `websocket-client`, `beautifulsoup4` (for legacy/automated login steps), `urllib3`.

## 2. Authentication Flow & Token Caching
Tesla uses standard OAuth2 authentication with multi-factor authentication.

### Token Cache Control
*   TeslaPy manages token persistence via a local **`cache.json`** file stored in the working directory.
*   Once authenticated, the `access_token` and `refresh_token` are cached in this file.
*   During subsequent executions, TeslaPy checks the cache, verifies token validity, and automatically handles token renewal using the `refresh_token` if expired.
*   **Security Boundary:** The `cache.json` file must be secured (e.g. standard file permissions `600`) as it contains raw API keys allowing vehicle control.

### Python Authentication Hook
```python
import teslapy

# Initialize Tesla instance with your email
tesla = teslapy.Tesla('user@example.com')

if not tesla.authorized:
    # 1. Generate authorization URL
    auth_url = tesla.authorization_url()
    print(f"Please log in via the browser and copy the resulting redirect URL:")
    print(auth_url)
    
    # 2. Wait for user to paste redirect URL containing authentication code
    redirect_url = input("Paste redirect URL: ")
    tesla.fetch_token(authorization_response=redirect_url)
    print("Authentication successful and cached in cache.json.")
```

## 3. Core Vehicle Commands
Once authorized, we can retrieve vehicles and send charging commands.

### Vehicle Wakeup
Tesla vehicles fall into a deep sleep ("offline" state) to conserve battery. Sending commands requires waking the car first:
```python
vehicles = tesla.vehicle_list()
vehicle = vehicles[0]

# Synchronous wakeup (polls until car is ONLINE)
vehicle.sync_wake_up()
```

### Amperage Control Command
Adjusting the charging speed (current limit) is done via the `CHARGING_AMPS` command:
```python
# Set charging current to 10 Amperes
vehicle.command('CHARGING_AMPS', charging_amps=10)
```
*   **Clamping:** Tesla allows integers between `5` and `32`/`48` (depending on the vehicle's onboard charger capacity: Model 3/Y RWD is typically 32A, Long Range is 48A).
*   **Minimum Limit:** The Tesla API rejects commands setting amperage below `5A`. Setting it below 5A requires pausing the charging session completely.

### Charging Control Commands
*   **Start Charging:** `vehicle.command('START_CHARGE')`
*   **Stop Charging:** `vehicle.command('STOP_CHARGE')`
*   **Set Charge Limit (SOC%):** `vehicle.command('CHANGE_CHARGE_LIMIT', percent=80)`

## 4. Automation Safety & API Polling Constraints
1.  **Sleep Cycle Maintenance:** Polling the Tesla API too frequently (e.g. every 10 seconds) will prevent the vehicle from going to sleep when it is parked and not charging, leading to substantial phantom battery drain.
2.  **State-Aware Polling:**
    *   **Active Charging:** Poll every 10 seconds to dynamically scale amperage to match solar.
    *   **Inactive Charging & Unplugged:** Increase poll interval to 15-30 minutes to let the vehicle sleep. Check the vehicle's state (`vehicle['state']`) before initiating a wakeup sequence.
3.  **Command Failure Fallback:** Amperage commands can fail due to temporary cellular connectivity issues. The control loop must implement a retry mechanism (e.g. back off and retry once).
