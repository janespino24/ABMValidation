# VIVAMACS — Agent-Based Cyber Risk Simulation

> **Companion code for:**
> Espino, J. (2025). *Agent-Based Cyber Risk Modeling*. [Working paper]

VIVAMACS is a stochastic, agent-based cyber risk simulation framework designed to support decision-making in enterprise network environments under conditions of **partial observability and incomplete data**.

Rather than predicting individual attack events, the framework estimates **distributions of cyber risk outcomes**—including intrusion prevalence and annual financial loss—as a function of user behavior, device configurations, network structure, and defensive controls.

---

## Overview

The simulation represents enterprise network nodes (users, PCs, mobile devices, servers, firewalls, internet gateways) as heterogeneous agents governed by probabilistic attack, detection, containment, and recovery processes. Extensive Monte Carlo simulations explore how variations in user security awareness, device hardening, and network characteristics influence emergent risk outcomes.

Key features:
- **Agent-based modeling** of enterprise network topology with VLAN segmentation
- **Stochastic infection and recovery dynamics** (Gaussian random draws, time-stepped simulation)
- **Monte Carlo parallelization** across CPU cores via `ProcessPoolExecutor`
- **Sensitivity and Sobol analyses** to identify dominant risk levers
- **Streamlit dashboard** (`app.py`) for interactive scenario exploration

---

## Project Structure

```
VIVAMACS/
├── src/
│   └── notebook_refactor/
│       ├── config.py        # Simulation constants (hours, propagation times)
│       ├── agents.py        # Agent class and device-type subclasses
│       ├── environment.py   # Data loading, VLAN parsing, strength/vulnerability math
│       ├── simulation.py    # Monte Carlo iteration loop
│       ├── sweep.py         # Parameter sweep utilities
│       └── main.py          # CLI entry point
├── data/
│   ├── Data2 (Good).csv             # Baseline scenario (default)
│   ├── Data_Best.csv                # Best-case configuration
│   ├── Data_Typical.csv             # Typical enterprise configuration
│   ├── Data_Worst.csv               # Worst-case configuration
│   ├── Data_ConfigA_20Server.csv    # 20-server large network
│   ├── Data_ConfigB_5Server_SMB.csv # 5-server SMB network
│   └── data.schema.md               # Column definitions
├── app.py                   # Streamlit interactive dashboard
├── requirements.txt
└── pyproject.toml
```

---

## Data Format

Each CSV file defines the network topology. See [`data/data.schema.md`](data/data.schema.md) for full details.

| Column | Type | Description |
|--------|------|-------------|
| `ID` | Integer | Unique agent identifier |
| `Type` | String | `Internet`, `Firewall`, `Server`, `User`, `PC`, `Mobile` |
| `Awareness` | Float (0–1) | User security awareness level |
| `AV` | Float (0–1) | Antivirus strength |
| `Patch` | Float (0–1) | Patch level |
| `Port` | Float (0–1) | Port exposure / vulnerability |
| `Value` | Float | Asset monetary value |
| `ConnectedTo` | String | Semicolon-separated list of connected agent IDs |

---

## Installation

```bash
git clone https://github.com/janespino24/VIVAMACS.git
cd VIVAMACS
pip install -r requirements.txt
```

Python 3.9+ is required.

---

## Usage

### Command-Line Simulation

```bash
# Run with defaults (Data2 baseline, 500 Monte Carlo runs, 365 days)
python3 -m src.notebook_refactor.main

# Custom configuration
python3 -m src.notebook_refactor.main \
    --data "data/Data_Typical.csv" \
    --runs 1000 \
    --days 365
```

### Streamlit Dashboard

```bash
streamlit run app.py
```

The dashboard provides an interactive interface for selecting network configurations, adjusting simulation parameters, and visualizing risk distributions.

---

## Simulation Logic

1. **Agents** are initialized with security attributes (AV, Patch, Awareness) drawn from the input CSV.
2. Each **time step** (5-minute periods within a working day) a Gaussian random draw determines attacker strength; if `attack > agent.strength`, the agent becomes infected.
3. **VLAN propagation**: infected agents mark all devices in the same VLAN as `nearby`, accelerating lateral movement.
4. **Recovery** occurs after fixed propagation times (configurable in `config.py`).
5. **Financial losses** (repair costs, data exfiltration value) are accumulated per run.
6. Results are aggregated across all Monte Carlo iterations to produce risk distributions.

---

## Citation

If you use this code in your research, please cite:

```
Espino, J. (2025). Agent-Based Cyber Risk Modeling. [Working paper]
```

---

## License

MIT License. See [LICENSE](LICENSE) for details.
