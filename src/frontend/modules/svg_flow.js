/**
 * Tesla Solar Sync - Kinetic SVG Flow Diagram Module
 * Renders local copper conduits, dynamic gear assemblies, and real-time energy flow particle streams.
 */

export class EnergyFlowDiagram {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) return;

        this.initialized = false;
        this.nodes = {};
        this.conduits = {};
        this.gears = [];
        
        this.init();
    }

    /**
     * Initializes the static SVG structures, copper pipelines, and steam brass junctions.
     */
    init() {
        if (this.initialized) return;

        const svgNamespace = "http://www.w3.org/2000/svg";
        const svg = document.createElementNS(svgNamespace, "svg");
        svg.setAttribute("viewBox", "0 0 600 400");
        svg.setAttribute("width", "100%");
        svg.setAttribute("height", "100%");
        svg.style.background = "#060606";
        svg.style.display = "block";

        // Define premium SVG gradients & patterns (brass, copper, glow filters)
        svg.innerHTML = `
            <defs>
                <!-- Glowing filters -->
                <filter id="glow-amber" x="-20%" y="-20%" width="140%" height="140%">
                    <feGaussianBlur stdDeviation="4" result="blur" />
                    <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
                <filter id="glow-green" x="-20%" y="-20%" width="140%" height="140%">
                    <feGaussianBlur stdDeviation="4" result="blur" />
                    <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
                <filter id="glow-crimson" x="-20%" y="-20%" width="140%" height="140%">
                    <feGaussianBlur stdDeviation="4" result="blur" />
                    <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>

                <!-- Metallic gradients -->
                <linearGradient id="metal-brass" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#f5d77f" />
                    <stop offset="40%" stop-color="#bda154" />
                    <stop offset="100%" stop-color="#4d3e17" />
                </linearGradient>
                <linearGradient id="metal-copper" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#f1ab86" />
                    <stop offset="40%" stop-color="#c36241" />
                    <stop offset="100%" stop-color="#5a2211" />
                </linearGradient>
                <linearGradient id="metal-iron" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#555" />
                    <stop offset="50%" stop-color="#2c2c2c" />
                    <stop offset="100%" stop-color="#111" />
                </linearGradient>
            </defs>

            <!-- Grid Backdrop lines for technical drafting style -->
            <g opacity="0.12">
                <path d="M 50,0 L 50,400 M 100,0 L 100,400 M 150,0 L 150,400 M 200,0 L 200,400 M 250,0 L 250,400 M 300,0 L 300,400 M 350,0 L 350,400 M 400,0 L 400,400 M 450,0 L 450,400 M 500,0 L 500,400 M 550,0 L 550,400" stroke="#499ff5" stroke-width="0.5" />
                <path d="M 0,50 L 600,50 M 0,100 L 600,100 M 0,150 L 600,150 M 0,200 L 600,200 M 0,250 L 600,250 M 0,300 L 600,300 M 0,350 L 600,350" stroke="#499ff5" stroke-width="0.5" />
            </g>

            <!-- ================= CONDUIT CHANNELS (BACKPIPE) ================= -->
            <!-- Solar to Inverter -->
            <path id="pipe-solar" d="M 120,110 L 260,180" stroke="url(#metal-iron)" stroke-width="12" stroke-linecap="round" fill="none" />
            <!-- Inverter to House Load -->
            <path id="pipe-house" d="M 340,180 L 480,110" stroke="url(#metal-iron)" stroke-width="12" stroke-linecap="round" fill="none" />
            <!-- Grid to Inverter (Bi-directional) -->
            <path id="pipe-grid" d="M 120,290 L 260,220" stroke="url(#metal-iron)" stroke-width="12" stroke-linecap="round" fill="none" />
            <!-- Inverter to Tesla EV -->
            <path id="pipe-tesla" d="M 340,220 L 480,290" stroke="url(#metal-iron)" stroke-width="12" stroke-linecap="round" fill="none" />

            <!-- ================= ENERGY GLOW CONDUITS (FOREGROUND) ================= -->
            <!-- Solar Flow -->
            <path id="flow-solar" d="M 120,110 L 260,180" stroke="#ff8c00" stroke-width="4" stroke-dasharray="10, 15" fill="none" opacity="0.8" style="mix-blend-mode: screen;" />
            <!-- House Flow -->
            <path id="flow-house" d="M 340,180 L 480,110" stroke="#8a887b" stroke-width="4" stroke-dasharray="10, 15" fill="none" opacity="0.8" style="mix-blend-mode: screen;" />
            <!-- Grid Flow (Bi-directional) -->
            <path id="flow-grid" d="M 120,290 L 260,220" stroke="#14c2c2" stroke-width="4" stroke-dasharray="10, 15" fill="none" opacity="0.8" style="mix-blend-mode: screen;" />
            <!-- Tesla EV Flow -->
            <path id="flow-tesla" d="M 340,220 L 480,290" stroke="#c22929" stroke-width="4" stroke-dasharray="10, 15" fill="none" opacity="0.8" style="mix-blend-mode: screen;" />

            <!-- Pipe Rivets and Fittings at Junctions -->
            <circle cx="120" cy="110" r="10" fill="url(#metal-copper)" stroke="#111" stroke-width="2" />
            <circle cx="480" cy="110" r="10" fill="url(#metal-copper)" stroke="#111" stroke-width="2" />
            <circle cx="120" cy="290" r="10" fill="url(#metal-copper)" stroke="#111" stroke-width="2" />
            <circle cx="480" cy="290" r="10" fill="url(#metal-copper)" stroke="#111" stroke-width="2" />

            <!-- ================= ROTATING STEAM COGS ================= -->
            <!-- Central Inverter Gear Assembly -->
            <g id="gear-assembly" transform="translate(300, 200)">
                <circle r="45" fill="url(#metal-brass)" stroke="#111" stroke-width="2" />
                <circle r="25" fill="#151515" stroke="#111" stroke-width="2" />
                <!-- Cog teeth -->
                <path d="M-8,-52 L8,-52 L12,-45 L-12,-45 Z" fill="url(#metal-brass)" transform="rotate(0)" />
                <path d="M-8,-52 L8,-52 L12,-45 L-12,-45 Z" fill="url(#metal-brass)" transform="rotate(30)" />
                <path d="M-8,-52 L8,-52 L12,-45 L-12,-45 Z" fill="url(#metal-brass)" transform="rotate(60)" />
                <path d="M-8,-52 L8,-52 L12,-45 L-12,-45 Z" fill="url(#metal-brass)" transform="rotate(90)" />
                <path d="M-8,-52 L8,-52 L12,-45 L-12,-45 Z" fill="url(#metal-brass)" transform="rotate(120)" />
                <path d="M-8,-52 L8,-52 L12,-45 L-12,-45 Z" fill="url(#metal-brass)" transform="rotate(150)" />
                <path d="M-8,-52 L8,-52 L12,-45 L-12,-45 Z" fill="url(#metal-brass)" transform="rotate(180)" />
                <path d="M-8,-52 L8,-52 L12,-45 L-12,-45 Z" fill="url(#metal-brass)" transform="rotate(210)" />
                <path d="M-8,-52 L8,-52 L12,-45 L-12,-45 Z" fill="url(#metal-brass)" transform="rotate(240)" />
                <path d="M-8,-52 L8,-52 L12,-45 L-12,-45 Z" fill="url(#metal-brass)" transform="rotate(270)" />
                <path d="M-8,-52 L8,-52 L12,-45 L-12,-45 Z" fill="url(#metal-brass)" transform="rotate(300)" />
                <path d="M-8,-52 L8,-52 L12,-45 L-12,-45 Z" fill="url(#metal-brass)" transform="rotate(330)" />
                <!-- Gear Center Bolt -->
                <polygon points="0,-8 7,-4 7,4 0,8 -7,4 -7,-4" fill="url(#metal-copper)" stroke="#111" />
            </g>

            <!-- ================= NODE JUNCTIONS (GLOWING DIALS) ================= -->
            
            <!-- 1. SOLAR HUB (Top Left) -->
            <g id="node-solar" transform="translate(100, 100)">
                <circle r="40" fill="url(#metal-iron)" stroke="url(#metal-brass)" stroke-width="4" filter="url(#glow-amber)" />
                <circle r="32" fill="#0d0d0d" stroke="#222" stroke-width="2" />
                <text y="-8" font-family="'Special Elite'" font-size="9" fill="#bda154" text-anchor="middle">SOLAR</text>
                <text id="val-flow-solar" y="12" font-family="'Share Tech Mono'" font-size="13" font-weight="bold" fill="#ff8c00" text-anchor="middle">0 W</text>
            </g>

            <!-- 2. HOME LOAD HUB (Top Right) -->
            <g id="node-house" transform="translate(500, 100)">
                <circle r="40" fill="url(#metal-iron)" stroke="#6b665c" stroke-width="4" />
                <circle r="32" fill="#0d0d0d" stroke="#222" stroke-width="2" />
                <text y="-8" font-family="'Special Elite'" font-size="9" fill="#a29d91" text-anchor="middle">HOUSE</text>
                <text id="val-flow-house" y="12" font-family="'Share Tech Mono'" font-size="13" font-weight="bold" fill="#eae7db" text-anchor="middle">0 W</text>
            </g>

            <!-- 3. POWER MAINS GRID HUB (Bottom Left) -->
            <g id="node-grid" transform="translate(100, 300)">
                <circle r="40" fill="url(#metal-iron)" stroke="url(#metal-copper)" stroke-width="4" />
                <circle r="32" fill="#0d0d0d" stroke="#222" stroke-width="2" />
                <text y="-8" font-family="'Special Elite'" font-size="9" fill="#c36241" text-anchor="middle">GRID</text>
                <text id="val-flow-grid" y="12" font-family="'Share Tech Mono'" font-size="13" font-weight="bold" fill="#14c2c2" text-anchor="middle">0 W</text>
            </g>

            <!-- 4. TESLA EV HUB (Bottom Right) -->
            <g id="node-tesla" transform="translate(500, 300)">
                <circle r="40" fill="url(#metal-iron)" stroke="#c22929" stroke-width="4" filter="url(#glow-crimson)" />
                <circle r="32" fill="#0d0d0d" stroke="#222" stroke-width="2" />
                <text y="-8" font-family="'Special Elite'" font-size="9" fill="#c22929" text-anchor="middle">TESLA</text>
                <text id="val-flow-tesla" y="12" font-family="'Share Tech Mono'" font-size="13" font-weight="bold" fill="#c22929" text-anchor="middle">OFFLINE</text>
            </g>

            <!-- CENTRAL INVERTER OVERLAY COVER -->
            <g transform="translate(300, 200)">
                <circle r="20" fill="rgba(20,20,20,0.85)" stroke="#111" stroke-width="2" />
                <text y="4" font-family="'Special Elite'" font-size="8" fill="#bda154" text-anchor="middle">CORE</text>
            </g>
        `;

        this.container.appendChild(svg);

        // Map key dynamic components
        this.nodes = {
            solarText: svg.getElementById("val-flow-solar"),
            houseText: svg.getElementById("val-flow-house"),
            gridText: svg.getElementById("val-flow-grid"),
            teslaText: svg.getElementById("val-flow-tesla"),
            solarNode: svg.getElementById("node-solar"),
            gridNode: svg.getElementById("node-grid"),
            teslaNode: svg.getElementById("node-tesla")
        };

        this.conduits = {
            solarFlow: svg.getElementById("flow-solar"),
            houseFlow: svg.getElementById("flow-house"),
            gridFlow: svg.getElementById("flow-grid"),
            teslaFlow: svg.getElementById("flow-tesla")
        };

        this.centralGear = svg.getElementById("gear-assembly");
        
        this.initialized = true;
        this.gearRotation = 0;
        this.lastTime = performance.now();

        // Start active render tickers for gears and streams
        this.tick();
    }

    /**
     * Animates physical brass gear dynamics with high precision frame timing.
     */
    tick() {
        const animate = (time) => {
            if (!this.initialized) return;

            const delta = (time - this.lastTime) / 1000;
            this.lastTime = time;

            // Apply rotation with a physics coefficient based on system load (default speed)
            if (this.gearSpeed && this.gearSpeed > 0) {
                this.gearRotation += this.gearSpeed * 45 * delta; // Rotates degrees/sec
                this.gearRotation %= 360;
                this.centralGear.setAttribute("transform", `translate(300, 200) rotate(${this.gearRotation})`);
            }

            requestAnimationFrame(animate);
        };
        requestAnimationFrame(animate);
    }

    /**
     * Dynamically updates node values and conduits flow based on active energy levels.
     * 
     * @param {Object} telemetry - GoodWe inverter and active household telemetry.
     * @param {Object} tesla - Vehicle battery, current and active status.
     * @param {number} phases - Phase coefficient count (1 or 3).
     */
    update(telemetry, tesla, phases) {
        if (!this.initialized) return;

        const solarW = Math.round(telemetry.solar_power_w || 0);
        const houseW = Math.round(telemetry.house_consumption_w || 0);
        const gridW = Math.round(telemetry.grid_export_w || 0); // Positive = Exporting, Negative = Importing
        
        // Compute active EV power based on amperage draw config
        const voltPerAmp = phases === 3 ? 690.0 : 230.0;
        const isCharging = tesla.charging_state === "Charging";
        const evPowerW = isCharging ? Math.round(tesla.charge_current_request * voltPerAmp) : 0;

        // 1. Update text fields
        this.nodes.solarText.textContent = `${solarW} W`;
        this.nodes.houseText.textContent = `${houseW} W`;
        
        if (gridW >= 0) {
            this.nodes.gridText.textContent = `EXP ${gridW} W`;
            this.nodes.gridText.setAttribute("fill", "#14c2c2");
            this.nodes.gridNode.querySelector('circle').setAttribute("stroke", "#14c2c2");
            this.nodes.gridNode.querySelector('circle').setAttribute("filter", "url(#glow-green)");
        } else {
            this.nodes.gridText.textContent = `IMP ${Math.abs(gridW)} W`;
            this.nodes.gridText.setAttribute("fill", "#c22929");
            this.nodes.gridNode.querySelector('circle').setAttribute("stroke", "#c22929");
            this.nodes.gridNode.querySelector('circle').setAttribute("filter", "url(#glow-crimson)");
        }

        if (tesla.state === "online" || tesla.state === "charging") {
            const evDisplay = isCharging ? `${evPowerW} W` : `STBY (${tesla.battery_level}%)`;
            this.nodes.teslaText.textContent = evDisplay;
            this.nodes.teslaText.setAttribute("fill", isCharging ? "#c22929" : "#bda154");
            this.nodes.teslaNode.querySelector('circle').setAttribute("stroke", isCharging ? "#c22929" : "#bda154");
        } else {
            this.nodes.teslaText.textContent = "OFFLINE";
            this.nodes.teslaText.setAttribute("fill", "#555");
            this.nodes.teslaNode.querySelector('circle').setAttribute("stroke", "#444");
        }

        // 2. Compute flow speeds (dash offsets) and update styles
        // Speed scaling factors based on maximum safety wattage levels (capped bounds)
        const getFlowSpeed = (watts, maxVal = 5000) => {
            if (watts <= 10) return 0;
            const ratio = Math.min(watts / maxVal, 1.0);
            return 1 + ratio * 8; // returns animation duration (lower is faster)
        };

        // Solar flow
        const solarSpeed = getFlowSpeed(solarW);
        this.updatePathAnimation(this.conduits.solarFlow, solarSpeed, false);

        // House flow
        const houseSpeed = getFlowSpeed(houseW);
        this.updatePathAnimation(this.conduits.houseFlow, houseSpeed, false);

        // Grid flow
        const gridSpeed = getFlowSpeed(Math.abs(gridW));
        // Reverse conduit particles flow direction if importing!
        this.updatePathAnimation(this.conduits.gridFlow, gridSpeed, gridW < 0);

        // Tesla EV flow
        const teslaSpeed = getFlowSpeed(evPowerW);
        this.updatePathAnimation(this.conduits.teslaFlow, teslaSpeed, false);

        // 3. Update central cog rotational speed based on overall solar generated and throughput
        const throughputPower = solarW + houseW + Math.abs(gridW) + evPowerW;
        if (throughputPower > 40) {
            this.gearSpeed = Math.min(0.2 + (throughputPower / 10000) * 2, 2.5); // Gear rotation multiplier
        } else {
            this.gearSpeed = 0; // stop cogs if generator is dormant
        }
    }

    /**
     * Updates individual flow path animation speeds and reverse flows.
     */
    updatePathAnimation(pathEl, speed, reverse = false) {
        if (!pathEl) return;

        if (speed === 0) {
            pathEl.style.animation = "none";
            pathEl.style.opacity = "0.15";
            return;
        }

        pathEl.style.opacity = "0.85";
        
        // Set standard keyframe animation
        const direction = reverse ? "flow-reverse" : "flow-forward";
        pathEl.style.animation = `${direction} ${12 / speed}s linear infinite`;
    }
}

// Inject keyframes globally inside document stylesheet once
if (!document.getElementById("svg-flow-keyframes")) {
    const style = document.createElement("style");
    style.id = "svg-flow-keyframes";
    style.innerHTML = `
        @keyframes flow-forward {
            from { stroke-dashoffset: 50; }
            to { stroke-dashoffset: 0; }
        }
        @keyframes flow-reverse {
            from { stroke-dashoffset: 0; }
            to { stroke-dashoffset: 50; }
        }
        .nixie-char {
            display: inline-block;
            transition: color 0.15s ease-out;
        }
        @keyframes nixie-flicker-anim {
            0%, 100% { opacity: 1; }
            23% { opacity: 0.94; }
            24% { opacity: 0.72; }
            25% { opacity: 1; }
            70% { opacity: 1; }
            71% { opacity: 0.82; }
            72% { opacity: 1; }
        }
        .nixie-sputter .nixie-char {
            animation: nixie-flicker-anim 0.2s cubic-bezier(0.1, 0.8, 0.1, 1);
        }
    `;
    document.head.appendChild(style);
}
