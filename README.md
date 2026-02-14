# Fractal Fire Mamba: Advanced Forest Fire Detection System

**A next-generation, multi-modal fire detection network leveraging Mamba State Space Models, Fractal Chaos Theory, and Heterogeneous Mesh Networking.**

---

## 🔥 System Overview

**Fractal Fire Mamba** is a decentralized, AI-driven forest fire monitoring system designed for early detection and rigorous false-positive rejection. It fuses data from:
1.  **Visual Mamba (Vision)**: Low-latency smoke/fire detection using State Space Models (SSM) instead of Transformers.
2.  **Thermal Imaging**: 32x24 MLX90640 sensors for heat signature verification.
3.  **Chemical Sensors**: BME680 (Gas/VOC) and MQ-2 (Smoke) for particulate analysis.
4.  **Fractal Analysis**: Hurst Exponent & Lyapunov Exponent calculations to distinguish organic fire chaos from random noise.

The system operates on a **"Hive" Architecture**, consisting of powerful **Queen Nodes** (Gateways) and lightweight **Drone Nodes** (Sensors), connected via a LoRa Mesh network with Satellite backhaul.

---

## 🐝 "The Hive" Hardware Architecture

The network is a **heterogeneous mesh** designed for cost-efficiency and wide-area coverage (~5km² per cell).

### 1. Queen Node (Gateway)
*   **Role**: Central processing, Satellite Uplink, Mesh Coordinator.
*   **Hardware**: Raspberry Pi 4B (4GB/8GB).
*   **Comms**: 
    *   **LoRa**: RFM95W (915 MHz) with High-Gain Antenna (5-8dBi).
    *   **Satellite**: RockBLOCK 9603 (Iridium) for emergency alerts when offline.
*   **Power**: 12V 10Ah LiFePO4 Battery + 50W Solar Panel.

### 2. Drone Node (Sensor Scout)
*   **Role**: Distributed sensing, visual/thermal monitoring, mesh relay.
*   **Hardware**: Raspberry Pi Zero 2 W.
*   **Comms**: LoRa RFM95W (Relays data to Queen). **No Satellite Modem** (Cost optimization).
*   **Power**: 6.4V 3000mAh LiFePO4 + 20W Solar Panel + **Buck-Boost Converter** (Critical for stable 5V).

---

## 🚀 Key Features

*   **Mamba Architecture**: Uses `mamba-130m` for visual recognition, offering faster inference and linear scaling compared to traditional ViTs.
*   **Chaos Kernel**: Computes **Hurst Exponent (H)** and **Lyapunov Exponent (λ)** on sensor streams. 
    *   *Fire is structured chaos (H > 0.5, λ > 0)*.
    *   *Noise is random (H ~ 0.5)*.
*   **Fractal Gate**: A logical gate that only allows alerts if both Visual/Thermal confidence and Fractal Chaos metrics align.
*   **Mesh Networking**: Custom persistent-state mesh protocol. Nodes relay messages to the Queen; Queen aggregates and uplinks to Satellite if WAN is down.
*   **Command Center Dashboard**: Real-time web UI for monitoring all 50+ nodes, analyzing telemetry, and viewing tactical maps.

---

## 🛠️ Installation & Setup

### Prerequisites
*   Python 3.8+
*   Git

### 1. Clone & Install
```bash
git clone https://github.com/Fractal-Forest-Fire-Detection/fractal_fire_mamba.git
cd fractal_fire_mamba

# Create Virtual Environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install Dependencies
pip install -r requirements.txt
```

### 2. Download Mamba Model (Required)
The Mamba weights are not in the repo. Download them using the provided script:
```bash
python scripts/download_mamba.py
```
*This fetches `state-spaces/mamba-130m-hf` and saves it to `models/`.*

### 3. Hardware Setup (Raspberry Pi)
Enable required interfaces on your Pi:
```bash
sudo raspi-config
# Enable: I2C, SPI, Serial, Camera
```

---

## 🖥️ Usage

### Start the Server (Backend)
Runs the FastAPI backend, Mesh Simulator, and Sensor Fusion engine.
```bash
uvicorn server:app --reload
```
*The server will start on `http://localhost:8000`.*

### Launch the Dashboard (Frontend)
Open `frontend/index.html` in your web browser. 
*   **Live Map**: Shows nodes (Queens/Drones) on a tactical map.
*   **Telemetry**: Click any node to see Humidity, Soil Moisture, Battery, and Risk Scores.
*   **Analysis**: View real-time Chaos/Fractal graphs.

---

## 📂 Project Structure
*   `server.py`: Main entry point (FastAPI).
*   `phases/`: Core processing logic (Communication, Sensing, Fractal Analysis).
*   `frontend/`: Web Dashboard (HTML/JS/CSS).
*   `models/`: Mamba model weights.
*   `hardware/`: Hardware integration scripts.

---
| **Team**: Evolve AI
