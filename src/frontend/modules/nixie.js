/**
 * Tesla Solar Sync - Nixie Display Module
 * Manages physical warm amber filament glowing values with cathode flicker effects.
 */

export class NixieDisplay {
    /**
     * Updates an element with an amber glowing numeric Nixie tube representation.
     * Optionally pads with leading zeros to maintain physical vacuum tube dimensions.
     * 
     * @param {string|HTMLElement} target - Element ID or HTMLElement to update.
     * @param {number|string} value - Numerical or string value to render.
     * @param {number} [padLength=0] - Optional digits padding (e.g. 5 for "00250").
     */
    static update(target, value, padLength = 0) {
        const el = typeof target === 'string' ? document.getElementById(target) : target;
        if (!el) return;

        let strValue = Math.round(Number(value) || 0).toString();
        if (typeof value === 'string' && isNaN(Number(value))) {
            strValue = value; // Preserve string if non-numeric
        }

        // Apply physical leading zero padding if requested
        if (padLength > 0 && !isNaN(Number(value))) {
            strValue = strValue.padStart(padLength, '0');
        }

        // Build individual vacuum tube envelope characters to look stacked
        const chars = strValue.split('');
        const html = chars.map(char => {
            const isDigit = !isNaN(parseInt(char));
            const fontStyle = isDigit ? '' : 'style="font-size: 0.85em; vertical-align: middle;"';
            // Introduce subtle randomized delay to simulate warm filament heat up
            const randomFlickerDelay = (Math.random() * 0.15).toFixed(2);
            return `<span class="nixie-char" ${fontStyle} style="animation-delay: ${randomFlickerDelay}s;">${char}</span>`;
        }).join('');

        // Apply to DOM only if changed to avoid unnecessary reflow and flicker triggers
        if (el.innerHTML !== html) {
            el.innerHTML = html;
            
            // Apply micro trigger of cathode sputter on update
            el.classList.remove('nixie-sputter');
            void el.offsetWidth; // Force CSS reflow
            el.classList.add('nixie-sputter');
        }
    }
}
