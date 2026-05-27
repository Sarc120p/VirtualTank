# VirtualTank – Industrial SCADA Simulator

<div align="center">

![Python](https://img.shields.io/badge/python-3.9+-blue.svg?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/flask-3.0-lightgrey.svg?style=for-the-badge&logo=flask&logoColor=white)
![Modbus](https://img.shields.io/badge/protocol-modbus_tcp-orange.svg?style=for-the-badge)
![SQLite](https://img.shields.io/badge/database-sqlite-003B57.svg?style=for-the-badge&logo=sqlite&logoColor=white)
![Docker](https://img.shields.io/badge/docker-ready-2496ED.svg?style=for-the-badge&logo=docker&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green.svg?style=for-the-badge)

**A fully functional industrial SCADA simulator — no hardware required.**

[Features](#features) · [Installation](#installation) · [Usage](#usage) · [Architecture](#architecture) · [Contributing](#contributing)

</div>

---

## Overview

**VirtualTank** is an open-source SCADA/HMI simulator built with **Python**, **Flask**, and **Modbus TCP**. It replicates a real industrial environment — a fermentation tank controlled by a virtual PLC — complete with a real-time dark-themed dashboard, batch state machine, alarm system, trend charts, and recipe management.

Designed for engineers, students, and hobbyists who want to learn, test, or demonstrate industrial automation concepts without physical hardware.

---

## Features

| Category | What's Included |
|---|---|
| **PLC Simulation** | Modbus TCP server mimicking a real PLC, updating process variables in real time |
| **SCADA Dashboard** | Dark-themed UI with gauges, sliders, trend charts, and live data via vanilla JS + Chart.js |
| **Batch State Machine** | Fill → Ferment → Empty → Clean transitions with automatic batch counting |
| **Process Variables** | Temperature, pressure, level, agitator speed, cooling, drain valve, and PRV |
| **Alarm System** | Visual alerts for high temperature, low pressure, and high pressure |
| **Recipe Management** | Upload and activate fermentation recipes (CSV) directly from the dashboard |
| **Data History** | SQLite-backed process logging for trend review and audit |
| **Security** | CSRF tokens, input validation, XSS prevention, environment-based secrets |
| **Docker Support** | `Dockerfile` + `docker-compose.yml` included for one-command deployment |

---

## Installation

### Prerequisites

- Python 3.9+
- pip

### 1. Clone the repository

```bash
git clone https://github.com/Sarc120p/VirtualTank.git
cd VirtualTank
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Linux / macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the PLC Simulator

In a dedicated terminal, run the Modbus server:

```bash
python simulador_clp.py
```

### 5. Start the Web Server

In a second terminal, launch Flask:

```bash
python app.py
```

Open your browser at **[http://localhost:5000](http://localhost:5000)**.

---

### Docker (Alternative)

```bash
docker-compose up --build
```

Everything starts automatically. Access the dashboard at **[http://localhost:5000](http://localhost:5000)**.

---

## Usage

### Batch Control

Use the **FILL**, **FERMENT**, **EMPTY**, and **CLEAN** buttons to advance the batch state. The PLC simulator reacts immediately and the dashboard updates in real time.

### Manual Commands

| Control | Description |
|---|---|
| Agitator Speed Slider | Adjust RPM in real time |
| Cooling Toggle | Enable or disable the cooling system |
| Drain Valve | Open or close the drain |
| PRV Button | Activate the Pressure Relief Valve to release excess pressure |

### Alarms

Alarms flash automatically when:
- Temperature exceeds **28 °C**
- Pressure drops below **99 kPa**
- Pressure exceeds **105 kPa**

### Recipes

Place `.csv` recipe files in the `receitas/` folder. Select and activate them directly from the dashboard to apply a fermentation profile.

> Recipe management is under active development — contributions welcome!

---

## Architecture

```
VirtualTank/
├── app.py
├── simulador_clp.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── README.md
├── LICENSE
├── database/
├── receitas/
├── static/
│   ├── css/
│   │   └── main.css
│   └── js/
│       └── dashboard.js
└── templates/
    └── dashboard.html
```

---

## Tech Stack

| Technology | Role |
|---|---|
| Python 3.9+ | Core language |
| Flask 3.0 | Web framework & REST API |
| Flask-SQLAlchemy | ORM for process history |
| pymodbus 2.5.3 | Modbus TCP client & server |
| SQLite | Persistent data storage |
| Chart.js | Real-time trend visualisation |
| Vanilla JavaScript | Dashboard interactivity |
| Docker | Optional containerised deployment |

---

## Security

- **CSRF Protection** – Unique tokens on all state-changing endpoints (POST / PUT / DELETE)
- **Input Validation** – Strict type and range checks on the backend
- **XSS Prevention** – All user-supplied content is escaped before rendering
- **No Hardcoded Secrets** – Sensitive values loaded from environment variables

---

## Roadmap

- [ ] Complete recipe activation workflow
- [ ] Export process history to CSV / PDF
- [ ] Multi-tank support
- [ ] REST API documentation (OpenAPI / Swagger)
- [ ] Unit and integration test suite

---

## Contributing

Contributions are welcome! If you plan a significant change, please open an issue first to discuss it.

```bash
git checkout -b feature/your-feature
git commit -m "feat: add your feature"
git push origin feature/your-feature
```

Please follow the existing code style and include relevant tests where possible.

---

## License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.

---

<div align="center">
Built with passion for industrial automation and clean code.
</div>
