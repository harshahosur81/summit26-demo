/**
 * Tesla Solar Sync - Config & SSO Modal Module
 * Coordinates system blueprint parameter adjustments, validations, and secure SSO redirects.
 */

export class BlueprintConfigManager {
    constructor() {
        this.form = document.getElementById("config-form");
        this.resetBtn = document.getElementById("btn-reset-form");
        this.alphaSlider = document.getElementById("cfg-ema-alpha");
        this.alphaBadge = document.getElementById("val-cfg-alpha");
        
        // Loop Tuning Elements
        this.tuningSlider = document.getElementById("ema-tuning-slider");
        this.tuningNixieVal = document.getElementById("nixie-ema-alpha-val");
        this.tuningWindow = document.getElementById("val-tuning-window");
        this.tuningSafety = document.getElementById("val-tuning-safety");
        this.tuningJitter = document.getElementById("val-tuning-jitter");
        
        // Auth Modal Elements
        this.btnShowAuth = document.getElementById("btn-show-auth");
        this.authModal = document.getElementById("auth-modal");
        this.closeAuthModal = document.getElementById("close-auth-modal");
        this.teslaSsoLink = document.getElementById("tesla-sso-link");
        this.redirectUrlInput = document.getElementById("redirect-url-input");
        this.submitAuthBtn = document.getElementById("submit-auth-btn");
        
        this.ticker = document.getElementById("system-log-ticker");

        this.serverConfig = {};
        this.init();
    }

    /**
     * Initializes elements, fetches current setup parameters, and registers triggers.
     */
    async init() {
        if (!this.form) return;

        // Warm up and fetch configuration
        await this.fetchServerConfig();

        // Wire up Alpha Slider Badge instant updater
        this.alphaSlider.addEventListener("input", (e) => {
            const val = parseFloat(e.target.value);
            this.alphaBadge.textContent = val.toFixed(2);
            if (this.tuningSlider) {
                this.tuningSlider.value = val;
                this.updateTuningUI(val);
            }
        });

        // Wire up Loop Tuning Slider instant updater
        if (this.tuningSlider) {
            this.tuningSlider.addEventListener("input", (e) => {
                const val = parseFloat(e.target.value);
                this.updateTuningUI(val);
                if (this.alphaSlider) {
                    this.alphaSlider.value = val;
                    this.alphaBadge.textContent = val.toFixed(2);
                }
            });
            this.tuningSlider.addEventListener("change", async (e) => {
                const val = parseFloat(e.target.value);
                await this.pushTuningConfig(val);
            });
        }

        // Wire up Save and Discard
        this.form.addEventListener("submit", (e) => this.handleSave(e));
        this.resetBtn.addEventListener("click", () => this.applyConfigToForm(this.serverConfig));

        // Wire up SSO triggers
        if (this.btnShowAuth) {
            this.btnShowAuth.addEventListener("click", () => this.openSsoModal());
        }
        if (this.closeAuthModal) {
            this.closeAuthModal.addEventListener("click", () => this.closeSsoModal());
        }
        if (this.submitAuthBtn) {
            this.submitAuthBtn.addEventListener("click", () => this.submitSsoCallback());
        }
    }

    /**
     * Fetches current configuration from backend database.
     */
    async fetchServerConfig() {
        try {
            const resp = await fetch("/api/v1/config");
            if (!resp.ok) throw new Error("Could not retrieve operational specs.");
            this.serverConfig = await resp.json();
            this.applyConfigToForm(this.serverConfig);
        } catch (err) {
            this.logToTicker(`ERR: Failed to sync configuration schema: ${err.message}`);
        }
    }

    /**
     * Syncs configuration values coming from real-time status packets without spamming logs.
     */
    syncConfig(cfg) {
        if (!cfg) return;

        // Ensure user is not currently sliding/tuning controls when syncing from server
        const activeEl = document.activeElement;
        if (activeEl !== this.alphaSlider && activeEl !== this.tuningSlider) {
            this.serverConfig = cfg;
            this.applyConfigToForm(cfg, true);
        }
    }

    /**
     * Applies a config object directly onto form fields and tuning dials.
     */
    applyConfigToForm(cfg, silent = false) {
        if (!cfg) return;
        
        // Phases
        if (cfg.grid_phases === 1) {
            document.getElementById("cfg-phases-1").checked = true;
        } else {
            document.getElementById("cfg-phases-3").checked = true;
        }

        // EMA Alpha
        this.alphaSlider.value = cfg.ema_alpha;
        this.alphaBadge.textContent = parseFloat(cfg.ema_alpha).toFixed(2);

        // Override Lock Duration
        document.getElementById("cfg-override-duration").value = cfg.override_duration_mins;
        
        // Update Tuning Panel UI elements
        this.updateTuningUI(cfg.ema_alpha);
        
        if (!silent) {
            this.logToTicker("Operational specifications synced from central database.");
        }
    }

    /**
     * Updates loop tuning visual elements, safety text and active light segments.
     */
    updateTuningUI(alpha) {
        if (!this.tuningSlider) return;

        this.tuningSlider.value = alpha;
        if (this.tuningNixieVal) {
            this.tuningNixieVal.textContent = parseFloat(alpha).toFixed(2);
        }

        const windowSecs = Math.round(10 / alpha);
        if (this.tuningWindow) {
            this.tuningWindow.textContent = `~${windowSecs} seconds`;
        }

        const segments = [
            document.getElementById("seg-1"),
            document.getElementById("seg-2"),
            document.getElementById("seg-3"),
            document.getElementById("seg-4"),
            document.getElementById("seg-5")
        ];

        // Reset segments
        segments.forEach(seg => {
            if (seg) seg.className = "light-segment";
        });

        if (alpha <= 0.05) {
            if (this.tuningSafety) {
                this.tuningSafety.textContent = "MAXIMUM SAFE";
                this.tuningSafety.style.color = "var(--color-teal)";
                this.tuningSafety.style.textShadow = "0 0 4px var(--color-teal-glow)";
            }
            if (this.tuningJitter) {
                this.tuningJitter.textContent = "LOW";
                this.tuningJitter.style.color = "var(--color-teal)";
                this.tuningJitter.style.textShadow = "0 0 4px var(--color-teal-glow)";
            }
            segments.forEach(seg => seg && seg.classList.add("active-teal"));
        } else if (alpha <= 0.15) {
            if (this.tuningSafety) {
                this.tuningSafety.textContent = "BALANCED";
                this.tuningSafety.style.color = "var(--color-teal)";
                this.tuningSafety.style.textShadow = "0 0 4px var(--color-teal-glow)";
            }
            if (this.tuningJitter) {
                this.tuningJitter.textContent = "LOW";
                this.tuningJitter.style.color = "var(--color-teal)";
                this.tuningJitter.style.textShadow = "0 0 4px var(--color-teal-glow)";
            }
            for (let i = 0; i < 4; i++) {
                if (segments[i]) segments[i].classList.add("active-teal");
            }
        } else if (alpha <= 0.35) {
            if (this.tuningSafety) {
                this.tuningSafety.textContent = "MODERATE";
                this.tuningSafety.style.color = "var(--color-nixie-orange)";
                this.tuningSafety.style.textShadow = "0 0 4px var(--color-nixie-glow)";
            }
            if (this.tuningJitter) {
                this.tuningJitter.textContent = "MODERATE";
                this.tuningJitter.style.color = "var(--color-nixie-orange)";
                this.tuningJitter.style.textShadow = "0 0 4px var(--color-nixie-glow)";
            }
            for (let i = 0; i < 3; i++) {
                if (segments[i]) segments[i].classList.add("active-amber");
            }
        } else if (alpha <= 0.70) {
            if (this.tuningSafety) {
                this.tuningSafety.textContent = "LOW DAMPENING";
                this.tuningSafety.style.color = "var(--color-nixie-orange)";
                this.tuningSafety.style.textShadow = "0 0 4px var(--color-nixie-glow)";
            }
            if (this.tuningJitter) {
                this.tuningJitter.textContent = "HIGH";
                this.tuningJitter.style.color = "var(--color-crimson)";
                this.tuningJitter.style.textShadow = "0 0 4px var(--color-crimson-glow)";
            }
            if (segments[0]) segments[0].classList.add("active-amber");
            if (segments[1]) segments[1].classList.add("active-amber");
            if (segments[2]) segments[2].classList.add("active-crimson");
        } else {
            if (this.tuningSafety) {
                this.tuningSafety.textContent = "UNPROTECTED (RAW)";
                this.tuningSafety.style.color = "var(--color-crimson)";
                this.tuningSafety.style.textShadow = "0 0 4px var(--color-crimson-glow)";
            }
            if (this.tuningJitter) {
                this.tuningJitter.textContent = "SEVERE";
                this.tuningJitter.style.color = "var(--color-crimson)";
                this.tuningJitter.style.textShadow = "0 0 4px var(--color-crimson-glow)";
            }
            if (segments[0]) segments[0].classList.add("active-crimson");
        }
    }

    /**
     * Commits adjusted settings into backend storage.
     */
    async handleSave(e) {
        if (e) e.preventDefault();

        const grid_phases = parseInt(this.form.querySelector('input[name="grid_phases"]:checked').value);
        const ema_alpha = parseFloat(this.alphaSlider.value);
        const override_duration_mins = parseInt(document.getElementById("cfg-override-duration").value);

        const payload = { grid_phases, ema_alpha, override_duration_mins };

        try {
            const resp = await fetch("/api/v1/config", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            if (!resp.ok) {
                const detail = await resp.json();
                throw new Error(detail.detail || "Validation check failed.");
            }

            this.serverConfig = payload;
            this.logToTicker("Operational parameters successfully committed to database registry.");
        } catch (err) {
            this.logToTicker(`ERR: Failed to commit blueprint adjustments: ${err.message}`);
        }
    }

    /**
     * Pushes real-time slider tuning adjustments down to the REST controller.
     */
    async pushTuningConfig(alpha) {
        const grid_phases = parseInt(this.form.querySelector('input[name="grid_phases"]:checked').value) || 3;
        const override_duration_mins = parseInt(document.getElementById("cfg-override-duration").value) || 120;

        const payload = { grid_phases, ema_alpha: alpha, override_duration_mins };

        try {
            const resp = await fetch("/api/v1/config", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            if (!resp.ok) {
                const detail = await resp.json();
                throw new Error(detail.detail || "Validation check failed.");
            }

            this.serverConfig = payload;
            this.logToTicker(`Live Loop Optimization parameter committed: alpha set to ${alpha.toFixed(2)}.`);
        } catch (err) {
            this.logToTicker(`ERR: Failed to update tuning coefficient: ${err.message}`);
        }
    }

    /**
     * Opens the official Tesla SSO Modal and retrieves the secure link.
     */
    async openSsoModal() {
        this.authModal.classList.add("active");
        this.teslaSsoLink.classList.add("disabled");
        this.teslaSsoLink.textContent = "GENERATING SSO LINK...";
        this.redirectUrlInput.value = "";

        try {
            const resp = await fetch("/api/v1/auth");
            if (!resp.ok) throw new Error("Auth service currently congested.");
            const data = await resp.json();
            
            this.teslaSsoLink.href = data.auth_url;
            this.teslaSsoLink.classList.remove("disabled");
            this.teslaSsoLink.textContent = "OPEN TESLA SSO PORTAL";
            this.logToTicker("SSO link successfully established. Ready for user checkout.");
        } catch (err) {
            this.logToTicker(`ERR: Auth Service Error: ${err.message}`);
            this.teslaSsoLink.textContent = "FAILED TO GENERATE SSO LINK";
        }
    }

    closeSsoModal() {
        this.authModal.classList.remove("active");
        this.redirectUrlInput.value = "";
    }

    /**
     * Submits the user-completed SSO Callback URI to the vault for GCM decryption.
     */
    async submitSsoCallback() {
        const callbackUrl = this.redirectUrlInput.value.trim();
        if (!callbackUrl) {
            this.logToTicker("ERR: Please enter a valid redirect callback URL before registering.");
            return;
        }

        this.submitAuthBtn.disabled = true;
        this.submitAuthBtn.textContent = "ENCRYPTING & VAULTING...";

        try {
            const resp = await fetch("/api/v1/auth/callback", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ redirect_url: callbackUrl })
            });

            if (!resp.ok) {
                const detail = await resp.json();
                throw new Error(detail.detail || "Invalid code callback parameter.");
            }

            const data = await resp.json();
            this.logToTicker(`SUCCESS: ${data.message || "Tesla credentials securely registered."}`);
            this.closeSsoModal();
        } catch (err) {
            this.logToTicker(`ERR: Credential registry failed: ${err.message}`);
            alert(`Authentication registration error: ${err.message}`);
        } finally {
            this.submitAuthBtn.disabled = false;
            this.submitAuthBtn.textContent = "REGISTER CREDENTIALS";
        }
    }

    /**
     * Appends a log line inside the main retro oily metal engine log ticker.
     */
    logToTicker(message) {
        if (this.ticker) {
            this.ticker.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
        }
    }
}
