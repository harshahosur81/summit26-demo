# Tesla Solar Sync - Steampunk Grid Controller

An automated, highly dynamic EV charging current controller (5A to 16A scaling) that maximizes zero-grid-export efficiency via local UDP polling of a GoodWe hybrid inverter and vehicle commanding using `teslapy` wrapped around a secure local cryptographic token vault. It features a stunning, tactile Neo-Futuristic Steampunk dashboard.

---

## 🛠️ Deployment & Setup Instructions

> [!IMPORTANT]
> **Default & Recommended Deployment (Google Cloud Platform)**
> This application is architected to run as a production-grade service on **Google Cloud** via Cloud Run with dynamic GCS FUSE mounting and Secret Manager.
> 
> For the complete, automated 3-phase Terraform configuration and instructions, please refer directly to the **[DEPLOY.md](DEPLOY.md)** guide.

---

### Local Development Setup

Ensure your target machine has **Python 3.10+** and **Git** installed.

### 1. Clone the Repository
```bash
git clone https://github.com/harshahosur81/summit26-demo.git
cd summit26-demo
```

### 2. Establish Virtual Environment & Install Dependencies
```bash
# Initialize a local virtual environment
python3 -m venv .venv

# Activate the environment
# On MacOS/Linux:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

# Upgrade pip and install all required modules
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure the Environment
The application will automatically generate a secure 32-character `AES_VAULT_KEY` key in `.env` upon the first execution if it is missing. 

You can also create a `.env` file manually at the root to specify custom configuration parameters:
```env
# Vault Crypto Secret Key (AES-256 PBKDF2 derivative)
AES_VAULT_KEY=your_secure_32_character_key_here

# Hardware configuration
INVERTER_IP=192.168.1.150  # Leave empty or unreachable to engage the dynamic GoodWe simulator
TESLA_EMAIL=user@example.com  # Set to your registered Tesla Account Email
```

---

## 🚀 Running the Engine Server

To fire up the FastAPI app engine and serve the tactile steampunk frontend dashboard:
```bash
PYTHONPATH=. uvicorn src.backend.main:app --host 0.0.0.0 --port 8888 --reload
```
Once started, open your web browser and navigate to:
**[http://localhost:8888](http://localhost:8888)**

---

## 🧪 Running the Quality Test Suite
To confirm all systems, EMA calculations, and cryptographic vault handlers are operating cleanly:
```bash
PYTHONPATH=. pytest
```

---

## 🎨 Dashboard Design Aesthetics
- **Kinetic Power Flow:** Features an animated brass SVG pipeline showing real-time flowing power particles where speed and directions respond directly to energy measurements.
- **Glowing Nixie Meters:** Digit displays constructed out of amber-glowing vacuum tubes incorporating dynamic physical wire cathode startup delay flickers.
- **CRT Telemetry Oscilloscope:** Direct HTML5 Canvas drawing rendering high-frequency green-phosphor waves tracking system parameters in real-time.
- **Tactile Switches:** Authentic metal knife-switches to toggle between automatic solar tracking and manual override currents.
- **Blueprint Terminal:** Built-in dashboard configuration sheets to modify smoothing coefficients and grid phase wiring formats.
