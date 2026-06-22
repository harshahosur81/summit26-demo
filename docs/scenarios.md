# Live Demonstration Playbook: Tesla Solar Sync Agent Scenarios

This document serves as the canonical playbook for live demonstrations of the Tesla Solar Sync application. It outlines three high-impact developer agent scenarios—spanning **Fix**, **Feature**, and **Optimization** categories—designed to showcase real-time platform evolution, autonomous issue remediation, and iterative enhancements.

---

## Scenario Overview Matrix

| ID | Category | Scenario Name | Primary Files Involved | Target Impact | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **SC-1** | **Fix** | Kinetic Power Flow & CRT Viewport Fix | `src/frontend/modules/svg_flow.js`<br>`src/frontend/index.css` | Align SVG conduits on-axis, round telemetry floats, and constrain CRT container overflow. | **Approved & Live** |
| **SC-2** | **Feature** | Grid Stress Analog Steam Gauge | `src/frontend/index.html`<br>`src/frontend/modules/steam_gauge.js`<br>`src/backend/main.py` | Create an analog-style steampunk dial depicting live grid import/export intensity. | **Ready for Dev** |
| **SC-3** | **Optimization** | Dynamic EMA Alpha Control Loop Tuning | `src/frontend/modules/config.js`<br>`src/backend/main.py`<br>`src/backend/drivers/goodwe_driver.py` | Add a tactile configuration slider to adjust solar data smoothing on-the-fly. | **Ready for Dev** |

---

## SC-1: Kinetic Power Flow & CRT Viewport Fix (The "Fix" Scenario)

### 1. Problem Statement & Audit Findings
During system testing and UI evaluation, three core issues were identified on the live Steampunk Dashboard:
1. **Off-Axis Conduit Trajectories:** The copper conduits representing energy pathways (`pipe-house`, `pipe-tesla`, `flow-house`, `flow-tesla`) were not mathematically aligned, resulting in jagged, off-axis SVG vectors leading into the central cog assembly.
2. **Telemetry Decimal Overflow:** Raw float values (e.g., `595.7459956625174 W`) streamed directly from WebSocket payloads to the SVG text nodes, overlapping UI labels and cluttering the aesthetic.
3. **CRT Shadow Bleed:** The `.crt-monitor-frame` had a fixed vertical constraints calculation (`calc(100vh - 220px)`), which caused bottom bezel shadows, CRT scanlines, and glow filters to overflow, stretching over and masking the footer's main ticker console.

### 2. Remediation Strategy & Code Edits
The agent identified and made the following precise structural corrections:

#### JS Refinement: Conduit Alignment & Float Rounding
We adjusted the geometric anchor points of the SVG coordinates to match clean $\pm 0.5$ slope lines, ensuring perfectly straight, symmetry-aligned pipelines. Additionally, we wrapped all telemetry outputs in `Math.round()` to force integer precision.

```diff
             <!-- Inverter to House Load -->
-            <path id="pipe-house" d="M 340,210 L 480,130" stroke="url(#metal-iron)" stroke-width="12" stroke-linecap="round" fill="none" />
+            <path id="pipe-house" d="M 340,180 L 480,110" stroke="url(#metal-iron)" stroke-width="12" stroke-linecap="round" fill="none" />
...
             <!-- Inverter to Tesla EV -->
-            <path id="pipe-tesla" d="M 340,190 L 480,270" stroke="url(#metal-iron)" stroke-width="12" stroke-linecap="round" fill="none" />
+            <path id="pipe-tesla" d="M 340,220 L 480,290" stroke="url(#metal-iron)" stroke-width="12" stroke-linecap="round" fill="none" />
```

```javascript
// Rounded telemetry readings in update()
const solarW = Math.round(telemetry.solar_power_w || 0);
const houseW = Math.round(telemetry.house_consumption_w || 0);
const gridW = Math.round(telemetry.grid_export_w || 0);
const evPowerW = isCharging ? Math.round(tesla.charge_current_request * voltPerAmp) : 0;
```

#### CSS Refinement: CRT Screen Constraint
Constrained the active oscilloscope layout and the surrounding CRT glass screen frame to fit perfectly inside the designated flex/grid panel instead of extending past viewport boundaries.

```css
.analytics-layout {
    height: 100%;
    margin-bottom: 0;
}

.crt-monitor-frame {
    height: 100%;
    padding: 10px;
    background: #111111;
    ...
}
```

### 3. Verification & Live Deployment
* **CI/CD Pipeline:** The agent pushed the updated code to personal fork branch `fix/diagram-flow`, triggering Google Cloud Build `4dd42e61-7939-45d2-aca6-05d84575c6ea` to compile a pristine container image (`solar-sync-app:latest`).
* **Cloud Run Update:** Executed `gcloud run services update tesla-solar-sync` in region `australia-southeast1`, force-pulling the new image using a unique deployment timestamp.
* **Result:** The visual paths are now perfectly straight, telemetry reads as integers, and the CRT screen bezel sits beautifully inside the panel without overlapping the footer log ticker.
* **Live Site:** [https://tesla-solar-sync-614327680171.australia-southeast1.run.app](https://tesla-solar-sync-614327680171.australia-southeast1.run.app)

---

## SC-2: Grid Stress Analog Steam Gauge (The "Feature" Scenario)

### 1. Concept & User Experience
To reinforce the Neo-Futuristic Steampunk theme, we will add an **Analog Steam Pressure Gauge** to the center console. This gauge represents "Grid Stress" (import vs. export intensity):
* **High Grid Import (Stress):** Needle swings aggressively clockwise into the "Overpressure / Crimson Red" zone ($100\%$ grid stress), indicating heavy fossil-fuel grid consumption.
* **Balanced Net-Zero ($0\text{W}$ Grid):** Needle settles at $50\%$ (vertical), showing perfect equilibrium.
* **High Solar Export (Venting):** Needle sweeps counter-clockwise into the "Venting / Brass Gold" zone, representing clean excess power returning to the grid.

### 2. Technical Implementation Architecture

#### HTML Shell additions (`src/frontend/index.html`)
Introduce a dedicated SVG gauge component within the central dashboard grid:
```html
<div class="steam-gauge-panel">
    <div class="panel-header">GRID STRESS STEAM PRESSURE</div>
    <svg id="steam-gauge" viewBox="0 0 200 200" width="100%" height="100%">
        <!-- Outer brass bezel -->
        <circle cx="100" cy="100" r="85" stroke="url(#metal-copper)" stroke-width="8" fill="#1e1b18" />
        <!-- Gauge face markings -->
        <path d="M 40,150 A 70,70 0 1,1 160,150" fill="none" stroke="#443c35" stroke-width="4" stroke-dasharray="2, 6" />
        <!-- Pressure Zones -->
        <path d="M 40,150 A 70,70 0 0,1 100,30" fill="none" stroke="#cca43b" stroke-width="6" opacity="0.6" /> <!-- Export -->
        <path d="M 100,30 A 70,70 0 0,1 160,150" fill="none" stroke="#c22929" stroke-width="6" opacity="0.6" /> <!-- Import -->
        <!-- Needle -->
        <line id="gauge-needle" x1="100" y1="100" x2="100" y2="40" stroke="#ff8c00" stroke-width="4" stroke-linecap="round" />
        <!-- Hub nut -->
        <circle cx="100" cy="100" r="12" fill="url(#metal-iron)" stroke="#cca43b" stroke-width="2" />
    </svg>
    <div class="pressure-reading" id="gauge-label">0% PSI</div>
</div>
```

#### Client-side script module (`src/frontend/modules/steam_gauge.js`)
Calculates the rotational angle of the gauge needle based on grid metrics.
* **Target angle range:** $-120^\circ$ (high export) to $+120^\circ$ (high import).
```javascript
export class SteamGauge {
    constructor() {
        this.needle = document.getElementById("gauge-needle");
        this.label = document.getElementById("gauge-label");
    }

    update(gridW) {
        // Grid Stress Logic: 
        // Max Export scale assumed to be 5000W, Max Import scale 5000W.
        const maxScale = 5000;
        let stress = 0; // -1 to +1

        if (gridW >= 0) {
            // Exporting: Needle moves counter-clockwise (- stress)
            stress = -Math.min(gridW / maxScale, 1);
        } else {
            // Importing: Needle moves clockwise (+ stress)
            stress = Math.min(Math.abs(gridW) / maxScale, 1);
        }

        const angle = stress * 120; // Scale to -120 to +120 deg
        this.needle.style.transform = `rotate(${angle}deg)`;
        this.needle.style.transformOrigin = "100px 100px";

        const percentage = Math.round(Math.abs(stress) * 100);
        const prefix = gridW >= 0 ? "VENTING (EXP)" : "OVERPRESSURE (IMP)";
        this.label.textContent = `${prefix}: ${percentage}% PSI`;
    }
}
```

### 3. Demonstration Flow during Live Pitch
1. **Step 1:** Activate "Manual Mode" knife switch and crank current to $16\text{A}$.
2. **Step 2:** Watch the **Steam Gauge** needle swing deep clockwise into the red "OVERPRESSURE" zone as solar output fails to cover the load and grid import climbs.
3. **Step 3:** Switch back to "Automatic Solar Tracking".
4. **Step 4:** Watch the charge rate drop dynamically, reducing grid draw, causing the **Steam Gauge** needle to slide back toward the balanced center ($0\%$ PSI).

---

## SC-3: Dynamic EMA Alpha Control Smoothing (The "Optimization" Scenario)

### 1. Concept & User Experience
The automated tracking loop utilizes an Exponential Moving Average (EMA) to smooth out solar jitter before commanding the vehicle's charger:
$$P_{\text{smoothed}} = \alpha \cdot P_{\text{raw}} + (1 - \alpha) \cdot P_{\text{smoothed\_prev}}$$
* **The Dilemma:** A high $\alpha$ value ($0.5$) tracks fast-moving clouds instantly but causes excessive vehicle contactor clicks, threatening Tesla battery relays. A low $\alpha$ value ($0.02$) protects the hardware but introduces grid import lag.
* **The Optimization Scenario:** Introduce a physical-looking "Dampening Dial" (potentiometer slider) on the frontend. Tuning this slider pushes real-time configuration changes down to the Python backend over a WebSocket or REST API, immediately changing the smoothing coefficient.

### 2. Technical Implementation Architecture

#### UI Slider Control (`src/frontend/index.html`)
```html
<div class="dampening-tuning-box">
    <div class="panel-header">ALPHA DAMPENING COEFFICIENT</div>
    <div class="potentiometer-wrapper">
        <input type="range" id="ema-alpha-slider" min="0.01" max="0.5" step="0.01" value="0.10" class="steampunk-slider" />
        <span class="pot-dial-readout" id="alpha-value-readout">0.10 (EMA Window ~100s)</span>
    </div>
</div>
```

#### Real-time API Endpoint (`src/backend/main.py`)
```python
@app.post("/api/v1/config/ema")
async def update_ema_alpha(alpha: float, db=Depends(get_db)):
    if not (0.01 <= alpha <= 1.0):
        raise HTTPException(status_code=400, detail="Alpha out of bounds [0.01, 1.0]")
    
    # Dynamically update in-memory control loop parameter
    config.EMA_ALPHA = alpha
    
    # Save parameter into database to persist across reboots
    await database.update_system_config("EMA_ALPHA", str(alpha))
    return {"status": "success", "ema_alpha": alpha}
```

#### Client-side Controller Integration (`src/frontend/modules/config.js`)
```javascript
const alphaSlider = document.getElementById("ema-alpha-slider");
const alphaReadout = document.getElementById("alpha-value-readout");

alphaSlider.addEventListener("change", async (e) => {
    const newAlpha = parseFloat(e.target.value);
    const windowSecs = Math.round(10 / newAlpha); // 10s polling interval
    alphaReadout.textContent = `${newAlpha.toFixed(2)} (Smoothing Window ~${windowSecs}s)`;

    // Push configuration down to backend API
    await fetch(`/api/v1/config/ema?alpha=${newAlpha}`, { method: "POST" });
});
```

### 3. Demonstration Flow during Live Pitch
1. **Step 1:** Select the **CRT Telemetry Oscilloscope** tab showing the live wave graphs.
2. **Step 2:** Slide the **Alpha Dampening** down to $0.02$. Notice how the green-phosphor wave plots a highly smoothed, flat solar trajectory, ignoring sudden cloud drops (which would result in transient grid import).
3. **Step 3:** Crank the slider up to $0.50$. Watch the smoothed telemetry wave instantly start aggressively tracking every minute deviation in solar output.
4. **Step 4:** Highlight the sweet spot ($0.10$) that balances grid safety with maximum solar utilization.
