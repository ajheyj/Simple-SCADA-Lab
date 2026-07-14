# Environment Setup

Use the existing Ubuntu SCADA VM and attack/analysis VM on a VMware Host-Only network.

Recommended addressing:

| System | Address |
|---|---|
| Ubuntu SCADA VM | `192.168.50.10/24` |
| Attack/analysis VM | `192.168.50.30/24` |
| Gateway | None |
| DNS | None |

Verify there is no default route:

```bash
ip route
```

Create and activate the project environment:

```bash
cd ~/scada-lab
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install pymodbus
```

Copy the Version 2 source files into the project directory, then run each component in a separate terminal.
