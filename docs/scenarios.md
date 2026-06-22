# Live Demonstration Playbook: Tesla Solar Sync Agent Scenarios

This document serves as the canonical playbook for live demonstrations of the Tesla Solar Sync application. It outlines three high-impact developer agent scenarios—spanning **Fix**, **Feature**, and **Optimization** categories—designed to showcase real-time platform evolution, autonomous issue remediation, and iterative enhancements.

---

## Scenario Overview Matrix

| ID | Category | Scenario Name | Primary Files Involved | Target Impact | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **SC-1** | **Fix** | Kinetic Power Flow & CRT Viewport Fix | `src/frontend/modules/svg_flow.js`<br>`src/frontend/index.css` | Align SVG conduits on-axis, round telemetry floats, and constrain CRT container overflow. | **Approved & Live** |
| **SC-2** | **Feature** | Integrated "Lux Sync" Green Cohesion Dial | `src/frontend/modules/svg_flow.js` | Create an integrated central dial measuring real-time solar self-sufficiency. | **Approved & Live** |
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

## SC-2: Integrated "Lux Sync" Green Cohesion Dial (The "Feature" Scenario)

### 1. Concept & User Experience
To ground the dashboard metrics in intuitive electrical charging context, we created the **"Lux Sync" Green Cohesion Dial** directly inside the central gear core assembly. This gauge measures how cleanly the EV is charging using local solar vs. utility grid power:
* **The Formula:** Calculates the fraction of total consumption (house + EV) covered by local solar generation, returning a value from $0\%$ to $100\%$:
  $$\text{Cohesion (\%)} = \min\left(\frac{\text{Solar Generation}}{\text{House Load} + \text{EV Charging Power}}, 1.0\right) \times 100$$
* **100% Cohesion (High Efficiency):** Needle sweeps clockwise to $+110^\circ$ (colored Green/Teal) indicating that local solar is completely meeting all active household loads and charging demand.
* **Low Cohesion (High Grid Stress):** Needle sweeps counter-clockwise to $-110^\circ$ (colored Crimson/Red) indicating that the system is heavily dependent on imported utility power.
* **Steampunk Name:** `LUX SYNC COHESION GAUGE`

### 2. Technical Implementation Architecture

#### Central SVG Core Dial (`src/frontend/modules/svg_flow.js`)
Rather than creating an isolated panel, we integrated the gauge directly overlaying the rotating central gears of our SVG flow diagram:
```html
            <!-- GREEN SYNC COHESION GAUGE CORE -->
            <g transform="translate(300, 200)">
                <!-- Bezel and dial backplate -->
                <circle r="36" fill="url(#metal-copper)" stroke="#111" stroke-width="2" />
                <circle r="31" fill="#0c0a08" stroke="#1f1812" stroke-width="1.5" />
                
                <!-- Cohesion Scale Arc (From 0% Red on Left to 100% Green/Teal on Right) -->
                <path d="M -22,12 A 25,22 0 0,1 22,12" fill="none" stroke="#221c15" stroke-width="2" />
                <!-- 0% to 50% Red zone -->
                <path d="M -22,12 A 25,22 0 0,1 0,-25" fill="none" stroke="#c22929" stroke-width="2" stroke-dasharray="1 3" opacity="0.6" />
                <!-- 50% to 100% Teal zone -->
                <path d="M 0,-25 A 25,22 0 0,1 22,12" fill="none" stroke="#14c2c2" stroke-width="2" stroke-dasharray="1 3" opacity="0.8" />
                
                <!-- Central Core Label -->
                <text y="-13" font-family="'Special Elite'" font-size="7" fill="#bda154" text-anchor="middle">LUX SYNC</text>
                
                <!-- Dynamic % Display -->
                <text id="gauge-cohesion" y="21" font-family="'Share Tech Mono'" font-size="9" font-weight="bold" fill="#14c2c2" text-anchor="middle">100%</text>
                
                <!-- Sync Needle -->
                <line id="gauge-needle" x1="0" y1="0" x2="0" y2="-26" stroke="#14c2c2" stroke-width="2" stroke-linecap="round" filter="url(#glow-green)" />
                
                <!-- Hub cover nut -->
                <circle cx="0" cy="0" r="5" fill="url(#metal-copper)" stroke="#111" stroke-width="1.5" />
            </g>
```

#### Client-Side Controller updates (`src/frontend/modules/svg_flow.js`)
The needle's transform is adjusted on-the-fly, dynamically shifting color filters based on cohesion tiers:
```javascript
        const totalLoadW = houseW + evPowerW;
        let cohesionPct = 100;
        
        if (totalLoadW > 0) {
            cohesionPct = Math.round(Math.min(solarW / totalLoadW, 1.0) * 100);
        }
        
        const angle = -110 + (cohesionPct / 100) * 220; // Maps 0-100% to -110deg to +110deg
        this.nodes.gaugeNeedle.setAttribute("transform", `rotate(${angle})`);
```

### 3. Demonstration Flow during Live Pitch
1. **The Set-up:** Load the app. The **Solar** is producing a robust **>3200W** (optimized to never fall to 0W). The car is standby. The central **Lux Sync** gauge reads **100% Cohesion** (Teal/Green needle), showing maximum solar self-sufficiency.
2. **The Grid Stress Trigger:** Flick the copper knife-switch to **Manual Mode** and slide the EV charging current up to **16A**.
3. **The Real-Time Reaction:** As the EV charging power jumps to $11,040\text{W}$ (at 3-phase), demand suddenly dwarfs solar. The needle sweeps counter-clockwise to **~30%**, shifting to **Amber/Red** to indicate a heavy grid import requirement.
4. **The Resolution:** Flip the switch back to **Automatic Smart Tracking**. The charging rate throttles down instantly, grid draw returns to zero, and the central needle sweeps smoothly back to **100%** (Teal/Green).

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
