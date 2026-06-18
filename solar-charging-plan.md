# Antigravity Master Orchestration Plan: Smart Solar EV Charging

This master configuration serves as the end-to-end SDLC lifecycle manager for the Antigravity Smart Solar EV Charging application. It enforces deterministic state transitions across five distinct phases, preventing "vibe coding" by requiring automated multi-agent research, design contracts, structural quality gates, and mandatory human sign-offs.

---

## 1. Global Context & Operational Boundaries

* **Target Application:** Automated Smart Solar EV Charger.
* **Core Dynamic Logic:** Compute real-time excess solar generation using the following tracking equation:
  
  Excess Power = Solar Generation (Inverter) - Household Consumption
  
  Dynamically scale the Tesla vehicle's charging amperage based on this delta, completely eliminating grid export waste without requiring a home battery storage buffer.
* **Workspace Bounding:** **CRITICAL.** The `antigravity-cli` execution engine must isolate all operations to the current local working directory. Do not write, cache, or leak context to the global `~/.gemini/antigravity-cli` directory path.
* **Sequential Gate Policy:** No phase may initialize until all artifacts of the previous phase are completely written, reviewed via the `/artifact view` skill, subjected to structural clarification loops, and explicitly approved by the User. 

---

## 2. Target Project Tree Scaffolding

Upon execution, the CLI will immediately construct and enforce the following localized workspace structure relative to this base directory:

```text
./
├── agents.md                     # Pre-existing Agent Team Personas & Protocols
├── solar_charging_lifecycle.md   # This master orchestration lifecycle file
├── research/                     # Localized telemetry & integration audits
│   ├── inverter_protocols/       # Inverter cloud/local API data mapping
│   ├── tesla_telemetry/          # TeslaPy integration & OAuth2 authentication flows
│   └── phase1_discovery_report.md # Final Phase 1 Review Artifact
├── docs/                         # System Design & Requirements Specifications
│   ├── requirements_sdd.md       # Target capture file for Phase 2 consolidation
│   ├── implementation_plan.md    # Pre-coding execution step blueprint (GATED AT PHASE 4)
│   ├── design/                   # Architectural blueprints and UI layout assets
│   │   ├── ui_ux_spec.md         # Data density and layout mapping
│   │   └── technical_architecture.md # API contracts, schemas, and IaC design
│   └── reviews/                  # Structural validation & QA testing logs
│       └── pull_request_audit.md # Target capture file for Phase 5 quality gate
└── src/                          # Modular production source code
    ├── frontend/                 # Responsive web application code (Mobile/PC)
    └── backend/                  # Core calculation engine and API webhooks
```

---

## 3. Sequential SDLC Execution Phases & Verification Gates

### PHASE 1: Discovery, Deep Domain Research & Ingestion
* **Active Personas:** `Cloud Architect`, `Security Architect`, `Backend Engineer`
* **Execution Strategy:** Parallel local research loops. No design or code compilation allowed.
* **Directives:**
    1. Investigate first-party internet-connected inverter integrations, evaluating local polling frequencies vs. cloud webhook streaming capabilities.
    2. Map out safe client authentication workflows for the TeslaPy open-source library, accounting for token caching and session persistence patterns.
    3. Ensure the high-level infrastructure footprint supports modular cloud deployment, capable of scaling dynamically to render uniformly as a mobile web app or desktop browser instance.
    4. **Output Artifact:** Compile all raw technical findings, token lifecycle management strategies, and API constraints into `./research/phase1_discovery_report.md`.
* **Phase Gate Review Protocol:** * The `Cloud Architect` must initiate a **minimum of 6 clarifying questions** using the `/grill-me` skill regarding the user's specific inverter model, cloud access tiers, and network constraints.
    * The system must load the output artifact via `/artifact view research/phase1_discovery_report.md`.
    * Execution freezes entirely; progress to Phase 2 is blocked until the user types an explicit approval string.

### PHASE 2: Requirements Elicitation
* **Active Personas:** `Program / Product Manager` (Facilitator), `UI/UX Architect`, `Engineering Manager`
* **Execution Strategy:** Human-in-the-loop interactive interrogation session in the terminal interface.
* **Directives:**
    1. Wake the `Program / Product Manager` to launch the automated `/grill-me` skill within the console.
    2. Extract precise, rigorous functional and non-functional requirements across three key development vectors:
        * **Front-End UI/UX:** Responsive grid behaviors, viewport adaptability, real-time solar-to-vehicle charging metrics visualization, and human-override charging toggles.
        * **Backend Engineering:** Data ingestion cadence, charging current adjustment calculation frequency, and safety fallback handling during severe weather disruptions (e.g., passing clouds dropping solar output rapidly).
        * **Security Architecture:** Decentralized API key retention, token persistence perimeters, and isolated session scopes.
    3. **Output Artifact:** Aggregate all user responses into a canonical requirements register at `./docs/requirements_sdd.md`.
* **Phase Gate Review Protocol:**
    * The `PM` must present a **minimum of 6 clarifying questions** using the `/grill-me` skill to resolve edge cases around user override actions and weather lag heuristics.
    * The system must load the output artifact via `/artifact view docs/requirements_sdd.md`.
    * Execution freezes entirely; progress to Phase 3 is blocked until the user types an explicit approval string.

### PHASE 3: System & Architectural Design
* **Active Personas:** `Product Designer` (Lead), `UI/UX Architect`, `Cloud Architect`, `Security Architect`
* **Execution Strategy:** Technical blueprinting and data contract specification via `/planning`. Production code paths (`src/`) remain strictly empty.
* **Directives:**
    1. **UI/UX Design:** Translate approved requirements into high-fidelity component layouts and data-density hierarchies tailored for mobile and desktop views. Document tokens and states in `./docs/design/ui_ux_spec.md`.
    2. **Technical Design:** Define the database data schema for telemetry logging, map the OAuth2 cryptographic credential containerization, and author explicit JSON schemas defining frontend-to-backend API contracts. Document blueprints in `./docs/design/technical_architecture.md`.
* **Output Artifacts:** `./docs/design/ui_ux_spec.md` and `./docs/design/technical_architecture.md`.
* **Phase Gate Review Protocol:**
    * The `Cloud Architect` must initiate a **minimum of 6 clarifying design questions** using the `/planning` skill to lock down interface boundaries and schema constraints.
    * The system must present both files to the user sequentially using `/artifact view docs/design/ui_ux_spec.md` and `/artifact view docs/design/technical_architecture.md`.
    * The `Engineering Manager` presents a technical summary. Progress to the pre-implementation planning sub-gate is blocked until the user types an explicit design approval string.

### PHASE 4 PRE-REQUISITE GATE: Implementation Plan Blueprinting
* **Active Personas:** `Engineering Manager` (Lead), `Front-End Engineer`, `Backend Engineer`, `Security Architect`
* **Execution Strategy:** Drafting a highly detailed task breakdown sequence before running engineering pipelines. Source directories (`src/`) remain completely empty.
* **Directives:**
    1. Parse the approved architecture, interface contracts, and design tokens from Phase 3.
    2. Draft an explicit, step-by-step engineering roadmap detailing the staging file sequences, test scaffolding order, dependency chains, and environment variables.
    3. **Output Artifact:** Write the granular execution plan to `./docs/implementation_plan.md`.
* **Phase Gate Review Protocol:**
    * The `Engineering Manager` must present a **minimum of 6 tactical implementation questions** using the `/planning` skill regarding specific mock frameworks, build tool chains, and staging parameters.
    * The system must render the detailed blueprint using `/artifact view docs/implementation_plan.md`.
    * **CRITICAL GATE:** Feature implementation coding is explicitly blocked. The engineers cannot progress to actual code writing until the user explicitly reviews and approves the step-by-step implementation plan.

### PHASE 4: Concurrent Feature Implementation & Quality Gates
* **Active Personas:** `Front-End Engineer`, `Backend Engineer`, `Security Architect`
* **Execution Strategy:** Parallel code generation, code scanning, and structural implementation blockades based precisely on the approved implementation plan.
* **Directives:**
    1. **Tactical Task Execution:** Initialize the directory paths inside `./src/` as outlined in the implementation plan.
    2. **Concurrent Engineering:** * `Backend Engineer` writes the core mathematical dynamic amperage algorithms and integrates Tesla/Inverter endpoints inside `./src/backend/`.
        * `Front-End Engineer` develops the modular component layer matching the responsive design system tokens inside `./src/frontend/`.
        * Both engineers co-author comprehensive unit test suites alongside implementation code.
    3. **Security Scan:** The `Security Architect` runs automated security validation routines over the source tree, verifying that no tokens or API credentials are exposed in plaintext.
* **Output Artifact:** Compiled functional application source files inside the `./src/` tree.
* **Phase Gate Review Protocol:**
    * The `Engineering Manager` must present a **minimum of 6 structural validation questions** using the `/planning` skill regarding runtime hooks, deployment configurations, and test coverage metrics.
    * The user reviews the generated application files. Progress to Phase 5 is blocked until the user types an explicit implementation approval string.

### PHASE 5: Code Review Quality Gate
* **Active Personas:** `Code Reviewer`
* **Execution Strategy:** Line-by-line programmatic review, test validation, and static analysis execution.
* **Directives:**
    1. Intercept all generated source code from Phase 4 before code optimization or completion states are finalized.
    2. Evaluate code line-by-line for syntax patterns, error containment traps, race conditions, memory optimization, and strict pattern compliance with the Phase 3 technical architecture document.
    3. Verify that test coverage metrics satisfy the code reliability boundaries defined in the SDD.
    4. **Output Artifact:** Generate a final code quality validation log at `./docs/reviews/pull_request_audit.md`.
* **Phase Gate Review Protocol:**
    * The `Code Reviewer` must ask a **minimum of 6 compliance questions** using the `/grill-me` skill detailing code optimizations, identified anti-patterns, and technical debt tradeoffs.
    * The system must render the audit log using `/artifact view docs/reviews/pull_request_audit.md`.
    * Final deployment readiness state freezes; system halts until the user enters an explicit execution sign-off string.

---

## 4. Pipeline Initialisation Trigger

```bash
# Instruction to Antigravity CLI Context Processor:
# 1. Parse local root 'agents.md' to align and initialize the multi-agent workspace.
# 2. Lock directory scopes strictly to the localized execution directory.
# 3. Transition control to the Cloud Architect to kick off the Phase 1 Discovery loop.
```

### [Agent Pipeline Invocator] -> Assigning: `Cloud Architect`
"Initialize Phase 1 Discovery operations within this local workspace scope. Do not allow downstream design or code generation. Investigate the inverter and vehicle telemetry boundaries, generate the `./research/phase1_discovery_report.md` artifact, and trigger the minimum 6-question `/grill-me` loop for immediate user review and artifact view approval."
```
