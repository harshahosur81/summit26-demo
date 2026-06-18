# Implementation Plan: Smart Solar EV Charging

This document outlines the step-by-step engineering roadmap, file staging sequences, dependency configurations, and environment parameters required to implement the Smart Solar EV Charging system.

---

## 1. Technical Stack & Core Dependencies

The application utilizes a purely localized Python backend and a lightweight, zero-framework Vanilla JS frontend to maximize speed and eliminate "Vite/Tailwind node_modules slop."

### Backend Dependencies (`requirements.txt`)
*   `fastapi==0.110.0` — Lightweight async REST and WebSocket router.
*   `uvicorn==0.28.0` — Asynchronous ASGI server.
*   `goodwe==0.2.22` — Official community library for GoodWe local UDP polling on port 8899.
*   `teslapy==3.0.0` — Python-native Tesla Owner API client with OAuth2 SSO and token caching.
*   `pycryptodome==3.20.0` — AES-256-GCM cryptographic operations.
*   `websockets==12.0` — High-velocity WebSocket server support.
*   `aiosqlite==0.20.0` — Non-blocking asynchronous SQLite database driver.
*   `pytest==8.1.1` — Testing framework.
*   `pytest-asyncio==0.23.5` — Async testing support.

### Frontend Libraries
*   *None* — 100% Vanilla HTML5, Vanilla ES6 JavaScript modules, and highly optimized custom Vanilla CSS variables to preserve maximum performance and avoid layout bloat.

### Environmental Variables (`.env`)
```bash
VAULT_SECRET=""                                                # Left blank to automatically generate a secure 32-character password
TESLA_EMAIL="user@example.com"                                 # Set to actual Tesla email for real mode; default 'user@example.com' activates Mock Vehicle
INVERTER_IP="192.168.1.150"                                    # Static local IP of GoodWe; if omitted/unreachable, defaults to Mock Inverter
PORT=8888                                                      # Custom high port to avoid conflicts
EMA_ALPHA=0.1                                                  # Dynamic smoothing (0.1 = ~100s window)
GRID_PHASES=3                                                  # Default grid phase configuration (1 or 3, configurable in UI)
OVERRIDE_DURATION_MINS=120                                     # Default manual override duration in minutes (configurable in UI)
```

---

## 2. Directory Structure Setup

Before coding, we will scaffold the localized repository structure:

```text
src/
├── backend/
│   ├── __init__.py
│   ├── main.py                # FastAPI app & WebSocket stream manager
│   ├── config.py              # Environment configuration loader
│   ├── database.py            # SQLite database connection & DDL definitions using aiosqlite
│   ├── vault.py               # AES-256-GCM credential encryption/decryption
│   ├── drivers/
│   │   ├── __init__.py
│   │   ├── goodwe_driver.py   # UDP Port 8899 Inverter & Meter telemetry client
│   │   └── tesla_driver.py    # TeslaPy vehicle control wrapper
│   ├── data/
│   │   └── .gitkeep           # Placeholder for local SQLite DB storage
│   └── tests/
│       ├── __init__.py
│       ├── test_vault.py      # AES encryption/decryption validation
│       └── test_control_loop.py # Telemetry calculations & EMA testing
└── frontend/
    ├── index.html             # Industrial panel layout structure
    ├── index.css              # Custom Neo-Futuristic Steampunk visual themes
    ├── app.js                 # Frontend orchestration launcher
    └── modules/               # Modular ES6 frontend scripts
        ├── config.js          # Forms, API settings, and dynamic config inputs
        ├── nixie.js           # Vacuum-tube metrics rendering
        └── svg_flow.js        # Copper conduit SVG layout, particles, and brass cogs
```

---

## 3. Step-by-Step Staging Sequence

To enforce systematic quality gates, development is staged in 8 incremental steps. No downstream step begins until the upstream step has been validated:

### Step 1: Python Virtual Environment & Configuration (`config.py`, `database.py`)
*   **Action:** 
    1.  Create a localized virtual environment `.venv` inside the project root (`python3 -m venv .venv`).
    2.  Implement environmental variables loading and validation. Initialize the SQLite database with DDL definitions using **`aiosqlite`** for non-blocking operations, defining tables for system configuration, 7-day high-resolution telemetry log table, daily aggregates, and charge session tracking.
*   **Verification:** Run initial database migration script, ensuring `solar_sync.db` is correctly generated under `src/backend/data/`.

### Step 2: AES-256-GCM Cryptographic Vault (`vault.py`)
*   **Action:** Implement PBKDF2 key derivation (**100,000 iterations** using a static salt from the database) and AES-256-GCM file encryption/decryption drivers. This module intercepts the TeslaPy token cache file (`cache.json`) and encrypts it on-disk as `.cache.enc` at rest, performing pure in-memory decryption on start.
*   **Verification:** Execute programmatic `pytest` verifying decryption matches original inputs and that encryption uses randomized Initialization Vectors (IV) and secure authentication tags.

### Step 3: GoodWe Local UDP Driver (`goodwe_driver.py`)
*   **Action:** Implement local async polling using the `goodwe` library. Map the `active_power` smart meter sensor. Provide an automated **Mock Inverter Class** fallback emulator that runs automatically if the inverter cannot be reached on the network. It simulates a **compressed 24-hour sunrise-to-sunset bell-curve cycle running in exactly 15 minutes** of real-world time, containing passing cloud dropouts.
*   **Verification:** Query the local inverter (or run the emulator fallback) to print active power, solar power, and household consumption in the terminal.

### Step 4: TeslaPy Command Driver (`tesla_driver.py`)
*   **Action:** Wrap TeslaPy APIs. Implement synchronous wakeup, charge start/stop, and current command execution `vehicle.command('CHARGING_AMPS', charging_amps=I_target)`. Provide a strict **Mock Vehicle Subclass** that intercepts all commands, increments virtual charge currents in local memory, and validates that amperage falls within the `[5A - 16A]` safety range when no physical Tesla login is active.
*   **Verification:** Run automated unit tests using `pytest` to verify command clamping and safety bounds.

### Step 5: FastAPI Web Server & WS Stream (`main.py`)
*   **Action:** Bind backend drivers into a FastAPI application. Serve the front-end directory (`src/frontend/`) as static mounts directly from FastAPI, keeping everything contained in a single running process. Expose REST endpoints `/api/v1/override`, `/api/v1/config`, and a temporary secure `/api/v1/auth` endpoint that handles browser SSO redirects directly in-app. Establish a high-frequency WebSocket endpoint `/api/v1/live` pushing real-time metrics throttled to **1 update per second (1 Hz)**. Include the daily database pruning execution script on boot.
*   **Verification:** Start the server on **localhost port `8888`** and connect a dummy terminal client to the WebSocket stream to verify 1 Hz updates match the JSON schema contracts.

### Step 6: Frontend Neo-Futuristic Steampunk Layout (`index.html`)
*   **Action:** Author the semantic HTML5 dashboard shell with mechanical nixie indicators, industrial gauges, copper conduit SVG canvases, and tactile command override elements (potentiometer slider, knife-switch manual toggle). Hook ES6 modules dynamically using `<script type="module" src="app.js">`.
*   **Verification:** Open the HTML file directly in a local browser to confirm full responsiveness across mobile, tablet, and desktop breakpoints.

### Step 7: Steampunk Styles & Animations (`index.css`)
*   **Action:** Implement our rich dark iron plates, metallic rivets, vacuum-tube glows, phosphor crt effects, and custom CSS spinning keyframes (`.brass-cog { animation: spin-clockwise var(--cog-speed) linear infinite; }`).
*   **Verification:** Ensure no generic Tailwind modules are used. Verify that visual elements scale cleanly without pixelation.

### Step 8: Client-Side Dashboard Coordination (`app.js`, `modules/`)
*   **Action:** Implement JavaScript WebSocket connections with exponential backoff reconnections (`1s`, `2s`, `4s`, up to `30s`) and a blurred loading state overlay. In `modules/svg_flow.js`, parse real-time telemetry packets to dynamically adjust SVG energy particle drift speeds and calculate cogwheel spinning velocities proportional to live power. In `modules/nixie.js`, handle metric updates with hot-wire filament flicker. In `modules/config.js`, manage setting updates and the in-app Tesla SSO modal on `/api/v1/auth`.
*   **Verification:** Run the FastAPI backend alongside the frontend on port `8888`, confirming interactive sliders update the backend state and that real-time telemetry drives the animations smoothly.
