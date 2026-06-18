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
            this.alphaBadge.textContent = parseFloat(e.target.value).toFixed(2);
        });

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
     * Applies a config object directly onto form fields.
     */
    applyConfigToForm(cfg) {
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
        
        this.logToTicker("Operational specifications synced from central database.");
    }

    /**
     * Commits adjusted settings into backend storage.
     */
    async handleSave(e) {
        e.preventDefault();

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
