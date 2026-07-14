# Historian Setup

The historian samples the PLC every two seconds and writes process data to CSV.

Start it with:

```bash
cd ~/scada-lab
source .venv/bin/activate
python historian.py
```

The output file is:

```text
logs/process_history.csv
```

Recorded fields include:

- UTC timestamp
- Tank level
- Temperature
- Pressure
- Alarm word
- Pump state
- Inlet valve state
- Pump speed
- Operating mode
