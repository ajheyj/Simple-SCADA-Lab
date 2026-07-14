# Operator Controls Setup

Start the PLC first, then run:

```bash
cd ~/scada-lab
source .venv/bin/activate
python operator_controls.py
```

The console supports:

- Pump start and stop
- Inlet valve open and close
- Pump speed changes
- High-level, low-level, and high-temperature alarm setpoints
- Manual and automatic mode
- Automatic pump start and stop levels
- Alarm acknowledgement
- Alarm reset
- Current PLC status

Potentially disruptive commands require confirmation before being sent.
