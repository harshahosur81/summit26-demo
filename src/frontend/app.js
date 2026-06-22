/**
 * Tesla Solar Sync - Unified Client Orchestrator
 * Conducts WebSocket stream bindings, mechanical lever routing, physical tactile interactions,
 * and renders high-frequency CRT green-phosphor oscilloscope visualizer grids.
 */

import { NixieDisplay } from "./modules/nixie.js";
import { EnergyFlowDiagram } from "./modules/svg_flow.js";
import { BlueprintConfigManager } from "./modules/config.js";

class SteampunkControllerApp {
    constructor() {
        // UI Core
        this.overlay = document.getElementById("connection-overlay");
        this.serverTimeDisplay = document.getElementById("server-time-display");
        this.systemLogTicker = document.getElementById("system-log-ticker");
        this.gaugeNeedle = document.getElementById("header-gauge-needle");

        // Tabs Routing
        this.tabButtons = document.querySelectorAll(".tab-btn");
        this.tabPanels = document.querySelectorAll(".tab-panel");

        // Knife Switch & Potentiometer Override Elements
        this.knifeSwitch = document.getElementById("knife-switch");
        this.potentiometerWidget = document.getElementById("potentiometer-widget");
        this.currentSlider = document.getElementById("current-slider");
        this.lblSmart = document.getElementById("lbl-smart");
        this.lblManual = document.getElementById("lbl-manual");
        this.nixieCurrentTarget = document.getElementById("nixie-current-target");
        this.nixieCountdown = document.getElementById("nixie-countdown");

        // LED Indicators
        this.ledInverter = document.getElementById("led-inverter");
        this.ledTesla = document.getElementById("led-tesla");
        this.ledAutomation = document.getElementById("led-automation");

        // Odometer Metric Counters
        this.odometerSolar = document.getElementById("odometer-solar");
        this.odometerCo2 = document.getElementById("odometer-co2");
        this.odometerSavings = document.getElementById("odometer-savings");
        this.dailyLogTableBody = document.querySelector("#daily-log-table tbody");

        // Charting
        this.canvas = document.getElementById("crt-oscilloscope-canvas");
        this.ctx = this.canvas ? this.canvas.getContext("2d") : null;
        this.chartData = {
            solar: [],
            house: [],
            ev: [],
            grid: []
        };
        this.maxDataPoints = 60; // 1-minute window at 1Hz

        // State trackers
        this.flowDiagram = null;
        this.configManager = null;
        this.ws = null;
        this.isOverriding = false;
        this.wsActive = false;
        this.firstPacketReceived = false;

        this.init();
    }

    async init() {
        // 1. Initialize static modules
        this.flowDiagram = new EnergyFlowDiagram("svg-flow-wrapper");
        this.configManager = new BlueprintConfigManager();

        // 2. Wire up Tab Navigation Levers
        this.tabButtons.forEach(btn => {
            btn.addEventListener("click", () => this.handleTabSwitch(btn));
        });

        // 3. Wire up Tactile Knife Switch throw controls
        if (this.knifeSwitch) {
            this.knifeSwitch.addEventListener("click", () => this.handleKnifeSwitchThrow());
        }

        // 4. Wire up Current Slider input events
        if (this.currentSlider) {
            this.currentSlider.addEventListener("input", (e) => {
                const val = parseInt(e.target.value);
                NixieDisplay.update(this.nixieCurrentTarget, val, 2);
            });
            this.currentSlider.addEventListener("change", () => {
                if (this.isOverriding) {
                    this.sendOverrideCommand(true, parseInt(this.currentSlider.value));
                }
            });
        }

        // 5. Handle canvas resizing on display changes
        if (this.canvas) {
            window.addEventListener("resize", () => this.resizeCanvas());
            this.resizeCanvas();
        }

        // 6. Connect live pipelines
        this.connectWebSocket();

        // 7. Initial query of historical registers
        await this.syncHistoricalRegisters();

        // 8. Start continuous canvas paint animation
        this.startCanvasAnimation();
    }

    /**
     * Conducts mechanical switch throwing to toggle override control matrices.
     */
    async handleKnifeSwitchThrow() {
        const active = !this.knifeSwitch.classList.contains("override-active");
        const targetAmps = parseInt(this.currentSlider.value);
        
        // Throw mechanical feedback
        this.updateOverrideUIState(active, targetAmps);
        
        // Dispatch to network
        await this.sendOverrideCommand(active, targetAmps);
    }

    /**
     * Updates client styling structures for Manual Override matrices.
     */
    updateOverrideUIState(active, targetAmps) {
        this.isOverriding = active;
        
        if (active) {
            this.knifeSwitch.classList.add("override-active");
            this.potentiometerWidget.classList.remove("disabled");
            this.currentSlider.removeAttribute("disabled");
            this.lblManual.classList.add("active");
            this.lblSmart.classList.remove("active");
            
            // LED adjustments
            this.ledAutomation.className = "indicator-led active-amber";
            NixieDisplay.update(this.nixieCurrentTarget, targetAmps, 2);
        } else {
            this.knifeSwitch.classList.remove("override-active");
            this.potentiometerWidget.classList.add("disabled");
            this.currentSlider.setAttribute("disabled", "true");
            this.lblSmart.classList.add("active");
            this.lblManual.classList.remove("active");
            
            // LED adjustments
            this.ledAutomation.className = "indicator-led active-green";
            this.nixieCountdown.textContent = "00:00:00";
        }
    }

    /**
     * Dispatches overriding currents to FastAPI rest controllers.
     */
    async sendOverrideCommand(active, targetAmps) {
        try {
            const resp = await fetch("/api/v1/override", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ active, target_amps: targetAmps })
            });
            if (!resp.ok) throw new Error("Controller command unacknowledged.");
            
            const state = await resp.json();
            this.logToTicker(active 
                ? `Manual command override thrown: locked EV current to ${targetAmps}A.` 
                : "Manual override disengaged. Core algorithm tracking solar surplus."
            );
        } catch (err) {
            this.logToTicker(`ERR: Failed to toggle override: ${err.message}`);
        }
    }

    /**
     * Implements mechanical lever sliding transitions on tab buttons.
     */
    handleTabSwitch(selectedButton) {
        const targetTabId = selectedButton.getAttribute("data-tab");

        this.tabButtons.forEach(btn => btn.classList.remove("active"));
        this.tabPanels.forEach(panel => panel.classList.remove("active"));

        selectedButton.classList.add("active");
        
        const targetPanel = document.getElementById(targetTabId);
        if (targetPanel) {
            targetPanel.classList.add("active");
        }

        // Reflow canvas inside CRT tab if selected
        if (targetTabId === "analytics-tab") {
            setTimeout(() => this.resizeCanvas(), 50);
        }
    }

    /**
     * Establishes real-time 1 Hz WebSocket stream connections.
     * Incorporates automatic exponential backoff to handle network drops.
     */
    connectWebSocket() {
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const wsUrl = `${protocol}//${window.location.host}/api/v1/live`;

        this.logToTicker("Stoking the network boilers... Connecting telemetry WebSocket.");
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            this.wsActive = true;
            this.logToTicker("WebSocket telemetry pipeline locked open at 1 Hz.");
        };

        this.ws.onmessage = (event) => {
            try {
                const status = JSON.parse(event.data);
                this.processRealTimeStatus(status);
            } catch (err) {
                console.error("Error unpacking telemetry packet:", err);
            }
        };

        this.ws.onclose = () => {
            this.wsActive = false;
            this.logToTicker("WebSocket pipeline severed. Retrying in 5 seconds...");
            setTimeout(() => this.connectWebSocket(), 5000);
        };

        this.ws.onerror = (err) => {
            console.error("WebSocket pipeline pressure error:", err);
            this.ws.close();
        };
    }

    /**
     * Consumes live telemetry packet data, animating dials, dials needles, and flowing pipes.
     */
    processRealTimeStatus(status) {
        if (!status) return;

        // Hide loader overlay on first packet receipt
        if (!this.firstPacketReceived) {
            this.firstPacketReceived = true;
            if (this.overlay) {
                this.overlay.classList.add("fade-out");
            }
        }

        const telemetry = status.telemetry || {};
        const tesla = status.tesla || {};
        const override = status.override || {};
        const config = status.config || {};

        // Sync real-time config to manager (tuning slider + blueprints)
        if (this.configManager) {
            this.configManager.syncConfig(config);
        }

        // 1. Sync Server Epoch time displays
        const dateObj = new Date(status.timestamp * 1000);
        this.serverTimeDisplay.textContent = dateObj.toLocaleTimeString();

        // 2. Sync main dashboard header dials
        const solarW = telemetry.solar_power_w || 0;
        const gridW = telemetry.grid_export_w || 0;

        // Gauge needle rotation (-90deg at 0W, to 90deg at 10kW)
        const needleAngle = Math.max(-90, Math.min(90, -90 + (solarW / 10000) * 180));
        if (this.gaugeNeedle) {
            this.gaugeNeedle.style.transform = `rotate(${needleAngle}deg)`;
        }

        // 3. Sync Nixie Main meters
        NixieDisplay.update("nixie-solar", solarW, 5);
        
        const absoluteGridW = Math.abs(gridW);
        NixieDisplay.update("nixie-grid", absoluteGridW, 5);

        // Update import vs export labeling colors
        const gridPressLabel = document.getElementById("grid-press-label");
        if (gridPressLabel) {
            if (gridW >= 0) {
                gridPressLabel.textContent = "EXPORT";
                gridPressLabel.style.color = "var(--color-teal)";
                gridPressLabel.style.textShadow = "0 0 5px var(--color-teal-glow)";
            } else {
                gridPressLabel.textContent = "IMPORT";
                gridPressLabel.style.color = "var(--color-crimson)";
                gridPressLabel.style.textShadow = "0 0 5px var(--color-crimson-glow)";
            }
        }

        // 4. Sync Tactile LEDs based on hardware states
        // Inverter LED (blinks green when operational)
        const isMockInverter = telemetry.is_mock_inverter;
        this.ledInverter.className = isMockInverter 
            ? "indicator-led active-amber" 
            : "indicator-led active-green";

        // Tesla LED (green if online/sleep, orange if charging, red if offline)
        if (tesla.state === "online") {
            if (tesla.charging_state === "Charging") {
                this.ledTesla.className = "indicator-led active-amber";
            } else {
                this.ledTesla.className = "indicator-led active-green";
            }
        } else {
            this.ledTesla.className = "indicator-led active-crimson";
        }

        // 5. Sync active potentiometer widget disabled layers
        if (override.active !== this.isOverriding) {
            this.updateOverrideUIState(override.active, override.target_amps);
            if (override.active && this.currentSlider) {
                this.currentSlider.value = override.target_amps;
            }
        }

        // Update countdown countdown Nixie
        if (override.active && override.seconds_remaining > 0) {
            const h = Math.floor(override.seconds_remaining / 3600).toString().padStart(2, "0");
            const m = Math.floor((override.seconds_remaining % 3600) / 60).toString().padStart(2, "0");
            const s = Math.floor(override.seconds_remaining % 60).toString().padStart(2, "0");
            this.nixieCountdown.textContent = `${h}:${m}:${s}`;
        } else {
            this.nixieCountdown.textContent = "00:00:00";
        }

        // 6. Update vehicle account widgets
        const valTeslaName = document.getElementById("val-tesla-name");
        const valTeslaState = document.getElementById("val-tesla-state");
        const valTeslaSoc = document.getElementById("val-tesla-soc");
        const valTeslaEnergy = document.getElementById("val-tesla-energy");
        const teslaModeTag = document.getElementById("tesla-mode-tag");

        if (valTeslaName) valTeslaName.textContent = tesla.display_name || "Dynamo";
        if (valTeslaState) valTeslaState.textContent = (tesla.state || "OFFLINE").toUpperCase();
        if (valTeslaSoc) valTeslaSoc.textContent = `${tesla.battery_level || 0}%`;
        if (valTeslaEnergy) valTeslaEnergy.textContent = `${parseFloat(tesla.charge_energy_added || 0).toFixed(2)} kWh`;
        
        if (teslaModeTag) {
            if (tesla.is_mock_tesla) {
                teslaModeTag.textContent = "MOCK MODE";
                teslaModeTag.className = "mode-tag mock-active";
            } else {
                teslaModeTag.textContent = "TESLA FLEET";
                teslaModeTag.className = "mode-tag real-active";
            }
        }

        // 7. Update Flow Diagram particle speeds and nodes
        if (this.flowDiagram) {
            this.flowDiagram.update(telemetry, tesla, config.grid_phases || 3);
        }

        // 8. Stream metrics into high-frequency telemetry registers
        this.appendChartTelemetry(solarW, telemetry.house_consumption_w || 0, tesla.charge_current_request || 0, gridW);
    }

    /**
     * Appends a log line inside the main retro oily metal engine log ticker.
     */
    logToTicker(message) {
        if (this.systemLogTicker) {
            this.systemLogTicker.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
        }
    }

    /**
     * Append live 1Hz telemetry entries into the chart series.
     */
    appendChartTelemetry(solar, house, teslaAmps, grid) {
        this.chartData.solar.push(solar);
        this.chartData.house.push(house);
        this.chartData.ev.push(teslaAmps * 230); // Approximate power equivalent
        this.chartData.grid.push(grid);

        // Limit length to keep sliding window
        Object.keys(this.chartData).forEach(key => {
            if (this.chartData[key].length > this.maxDataPoints) {
                this.chartData[key].shift();
            }
        });
    }

    /**
     * Queries daily statistics aggregates and recent historical typewriter journals.
     */
    async syncHistoricalRegisters() {
        try {
            const resp = await fetch("/api/v1/analytics/history");
            if (!resp.ok) throw new Error("History registry data locked.");
            const data = await resp.json();

            const aggregates = data.daily_aggregates || [];
            
            // 1. Calculate and update Odometer metrics
            let cumulativeSolar = 0.0;
            let cumulativeEv = 0.0;

            aggregates.forEach(day => {
                cumulativeSolar += day.solar_generated_kwh || 0.0;
                cumulativeEv += day.ev_charged_kwh || 0.0;
            });

            // If aggregates are empty, fall back to default simulations
            if (aggregates.length === 0) {
                cumulativeSolar = 1420.5;
                cumulativeEv = 480.2;
            }

            const co2Offset = cumulativeSolar * 0.70; // 0.70 kg CO2 offset per solar kWh
            const currencySavings = cumulativeEv * 0.18; // Utility grid vs solar arbitrage value

            if (this.odometerSolar) this.odometerSolar.textContent = cumulativeSolar.toFixed(1).padStart(8, "0");
            if (this.odometerCo2) this.odometerCo2.textContent = co2Offset.toFixed(1).padStart(8, "0");
            if (this.odometerSavings) this.odometerSavings.textContent = `$${currencySavings.toFixed(2).padStart(8, "0")}`;

            // 2. Render typewriter tabular grid
            if (this.dailyLogTableBody) {
                this.dailyLogTableBody.innerHTML = "";
                
                if (aggregates.length === 0) {
                    this.dailyLogTableBody.innerHTML = `<tr><td colspan="6" class="text-center italic text-dim">No historical daily summaries compiled yet. Engine stoking underway.</td></tr>`;
                    return;
                }

                aggregates.forEach(day => {
                    const row = document.createElement("tr");
                    row.innerHTML = `
                        <td>${day.date}</td>
                        <td>${(day.solar_generated_kwh || 0).toFixed(2)} kWh</td>
                        <td>${(day.ev_charged_kwh || 0).toFixed(2)} kWh</td>
                        <td>${(day.grid_imported_kwh || 0).toFixed(2)} kWh</td>
                        <td>${(day.grid_exported_kwh || 0).toFixed(2)} kWh</td>
                        <td style="color: var(--color-brass);">${(day.self_consumption_pct || 0).toFixed(1)}%</td>
                    `;
                    this.dailyLogTableBody.appendChild(row);
                });
            }
        } catch (err) {
            console.error("Failed to compile archives registers:", err);
            this.logToTicker(`ERR: Failed to sync archives registers: ${err.message}`);
        }
    }

    /**
     * Prepares full canvas width on window size change.
     */
    resizeCanvas() {
        if (!this.canvas) return;
        const rect = this.canvas.parentElement.getBoundingClientRect();
        this.canvas.width = rect.width;
        this.canvas.height = rect.height;
    }

    /**
     * Initiates the high-frequency HTML5 paint rendering loop inside the CRT screen.
     */
    startCanvasAnimation() {
        const render = () => {
            this.drawOscilloscope();
            requestAnimationFrame(render);
        };
        requestAnimationFrame(render);
    }

    /**
     * Draws a premium, green-phosphor fluorescent oscilloscope wave representing raw telemetry sensor states.
     */
    drawOscilloscope() {
        if (!this.ctx || !this.canvas) return;

        const w = this.canvas.width;
        const h = this.canvas.height;
        const ctx = this.ctx;

        // Clear canvas
        ctx.clearRect(0, 0, w, h);

        // 1. Draw Technical Oscilloscope gridlines (faint green-phosphor lines)
        ctx.strokeStyle = "rgba(57, 255, 20, 0.08)";
        ctx.lineWidth = 1;

        // Horizontal gridlines
        const gridSpacing = 40;
        for (let y = 0; y < h; y += gridSpacing) {
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(w, y);
            ctx.stroke();
        }

        // Vertical gridlines
        for (let x = 0; x < w; x += gridSpacing) {
            ctx.beginPath();
            ctx.moveTo(x, 0);
            ctx.lineTo(x, h);
            ctx.stroke();
        }

        // Draw central crosshairs
        ctx.strokeStyle = "rgba(57, 255, 20, 0.2)";
        ctx.beginPath();
        ctx.moveTo(0, h / 2);
        ctx.lineTo(w, h / 2);
        ctx.moveTo(w / 2, 0);
        ctx.lineTo(w / 2, h);
        ctx.stroke();

        // 2. Render Telemetry Lines (Solar, House, EV, Grid)
        const drawSeries = (series, color, shadowColor, maxVal = 8000) => {
            if (series.length < 2) return;

            ctx.strokeStyle = color;
            ctx.lineWidth = 2.5;
            ctx.shadowColor = shadowColor;
            ctx.shadowBlur = 8;
            ctx.lineJoin = "round";

            ctx.beginPath();
            
            const stepX = w / (this.maxDataPoints - 1);
            
            for (let i = 0; i < series.length; i++) {
                const x = i * stepX;
                // Center-aligned scaling: map positive/negative values around grid midpoint
                const val = series[i];
                // Scale value (e.g. maxVal corresponds to 40% height of screen)
                const scaledY = h / 2 - (val / maxVal) * (h * 0.4);
                
                if (i === 0) {
                    ctx.moveTo(x, scaledY);
                } else {
                    ctx.lineTo(x, scaledY);
                }
            }
            ctx.stroke();

            // Clear shadows
            ctx.shadowBlur = 0;
        };

        // Draw series lines
        drawSeries(this.chartData.solar, "#ff8c00", "rgba(255,140,0,0.5)", 6000);   // Solar amber
        drawSeries(this.chartData.house, "#8a887b", "rgba(138,136,123,0.3)", 6000);  // House grey
        drawSeries(this.chartData.ev, "#c22929", "rgba(194,41,41,0.5)", 6000);      // EV crimson
        drawSeries(this.chartData.grid, "#14c2c2", "rgba(20,194,194,0.5)", 6000);    // Grid teal
    }
}

// Instantiate App on Document Lock Complete
document.addEventListener("DOMContentLoaded", () => {
    window.app = new SteampunkControllerApp();
});
