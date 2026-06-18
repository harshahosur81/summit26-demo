# UI/UX Visual Specification: Smart Solar EV Charging

This document specifies the custom visual design system, typography, color palettes, tabbed layout structures, and real-time SVG animation vectors for the Smart Solar EV Charging dashboard.

---

## 1. Design Aesthetics: Neo-Futuristic with Steampunk Accents

To completely break away from generic, "AI-generated front-end slop" (standard glassmorphic blue-violet cards), this interface implements a custom **Neo-Futuristic Steampunk** visual language. It blends industrial weight, physical metal textures, and raw copper conduits with glowing neon indicators, high-contrast digital displays, and rotating gear-train animations.

### Color Palette (Metallic & Neon)
*   **Background (Obscured Obsidian):** `hsl(225, 15%, 4%)` (`#0a0b0d`) — Very dark charcoal with raw carbon-fiber texturing.
*   **Card Base (Dark Iron Plate):** `hsla(225, 10%, 10%, 0.85)` — Deep oiled iron paneling with subtle riveted borders.
*   **Copper Conduits (Accents):** `hsl(21, 62%, 46%)` (`#b85a2b`) — Rich burnished copper vectors for path lines.
*   **Amber Filament Glow (Primary Metric):** `hsl(38, 100%, 50%)` (`#ff9900`) — A warm, high-intensity vacuum-tube amber glow.
*   **Cathode Red (Tesla EV / Alarm):** `hsl(354, 85%, 48%)` (`#d90f23`) — Glowing neon crimson.
*   **Phosphor Teal (Grid Net):** `hsl(166, 100%, 37%)` (`#00cc99`) — Bright vintage laboratory terminal green/teal.
*   **Brass Gear Accents:** `hsl(43, 48%, 52%)` (`#c5a059`) — Warm gold/brass highlights for moving components.

### Typography & Display
*   **Body & Control Font:** `Outfit` or `Space Grotesk` (Modern, high-tech geometric sans-serif).
*   **Metric Fonts (Nixie/Vacuum Tube):** `Share Tech Mono` or `Courier Prime` (resembles glowing vintage digital filaments or typewriters).

### Tactile Shadows & Metal Borders
*   **Rivet Borders:** Panel borders feature tiny structural rivet indicators (`border-image` or CSS radial-gradients at card corners).
*   **Industrial Glows:** High-contrast `box-shadow` values using long, saturated amber filaments (`0 0 15px hsla(38, 100%, 50%, 0.25)`).
*   **Material Transitions:** Sliders, toggle-clats, and tabs have physical inertial animations (`transition: all 0.35s cubic-bezier(0.25, 0.8, 0.25, 1)`).

---

## 2. Layout & Multi-Tab Interface Structure

The layout utilizes a robust multi-tab interface with heavy-duty side margins, structured with an asymmetric industrial layout.

### Main Dashboard Shell
*   **Header:** Framed in a dark iron header bar with brass screws. Features the brand "Tesla Solar Sync" in a rugged sans-serif, with raw mechanical status gauges (glowing nixie-tube style lights showing connection health).
*   **Tab Controller:** A segmented mechanical lever selector or a heavy-duty copper-rimmed button group:
    *   `[ Status ]`  `[ Analytics ]`  `[ History ]`  `[ Config ]`

### Tab 1: Real-Time Status View (Core Panel)
*   **Primary Panel (The Mechanical Power Flow):**
    Renders an interactive **Power Flow** diagram using customized SVG graphics representing mechanical-to-electrical conduits.
    *   *Nodes:*
        1.  **Solar Array (The Boiler / Amber Node):** Rendered as a heavy solar collector icon with glowing orange filament coils showing live power (W).
        2.  **Smart Meter (The Pressure Valve / Teal Node):** Rendered as an industrial dials gauge showing grid import/export pressure.
        3.  **Household Loads (The Generator / Slate Node):** Rendered as a structural mechanical factory outline.
        4.  **Tesla Vehicle (The Dynamo / Crimson Node):** A stylized electric vehicle outline containing glowing crimson batteries.
    *   *Paths & Gears:* Instead of simple lines, the energy paths are styled as **copper-pipe conduits**. 
    *   *Gears Animation:* Inside the Solar and Tesla nodes, subtle **interlocking brass cogs/gears** rotate in real-time. The rotation velocity of the gears scales proportionally with the power:
        $$\omega_{\text{gears}} \propto P_{\text{power}}$$
        If solar generation surges, the cogs rotate rapidly. If charging stops, the gears slowly grind to a complete halt.
    *   *Energy Particles:* Glowing plasma-amber sparks drift through the copper conduits.
*   **Secondary Panel (The Console Override):**
    A control board modeled after retro lab equipment, housing:
    *   A heavy-duty manual knife-switch toggle.
    *   A brushed brass slider knob for controlling the amperage limit `[5A - 16A]`.
    *   An amber Nixie countdown display showing override time remaining.

### Tab 2: Analytics & Telemetry Charts
*   **CRT Monitor Chart:**
    A line chart designed to resemble an old cathode-ray tube oscilloscope screen with a subtle green-phosphor background scanline effect, plotting:
    *   Solar Generation (Amber solid wave).
    *   Household Load (Dark steel wave).
    *   Tesla Power Draw (Crimson jagged wave).

### Tab 3: Historical Session Logs
*   **The Brass Register:**
    *   Data is presented in a typewriter-slab tabular grid.
    *   *Summary Cards:* Structured as heavy mechanical odometer readouts for *Total Solar Diverted*, *Capture Efficiency*, and *Utility Tariff Savings*.

### Tab 4: System Configurations
*   **The Blueprint Terminal:**
    *   Config entries styled with technical drawings (blueprints) in the background.
    *   Features clean input terminals for Inverter IP, Voltage (230V/240V), and Target limits.

---

## 3. Micro-Animations & Shader Effects

1.  **Inertial Cog Rotations:**
    ```css
    @keyframes spin-clockwise {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
    .brass-cog {
      transform-origin: center;
      animation: spin-clockwise var(--cog-speed) linear infinite;
    }
    ```
    The variable `--cog-speed` is computed as:
    *   `16 Amps (Max)` $\to$ `1.5s` (high velocity spin)
    *   `5 Amps (Min)` $\to$ `8s` (slow heavy grind)
    *   `0 Amps (Paused)` $\to$ `animation-play-state: paused`
2.  **Cathode Flicker:** Subtle $0.5\%$ opacity flicker on glowing Nixie numbers to simulate hot physical wire filaments.
3.  **Haptic Hover Feedback:** Interactive metallic knobs click (with a microscopic scale-down `active` state and shadow intensity transition) on user click.
