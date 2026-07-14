# PLC Setup

The PLC listens on TCP port `5020` and runs a one-second process scan.

Start it with:

```bash
cd ~/scada-lab
source .venv/bin/activate
python plc_server.py
```

The PLC now provides:

- Dynamic tank level
- Pump-dependent pressure
- Pump-dependent temperature
- High-level, low-level, and high-temperature alarms
- Alarm acknowledgement and reset handling
- Manual and automatic modes
- PLC event logging

The event log is written to:

```text
logs/plc_events.csv
```
