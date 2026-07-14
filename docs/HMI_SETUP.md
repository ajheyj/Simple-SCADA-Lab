# HMI Setup

Start the PLC first, then run:

```bash
cd ~/scada-lab
source .venv/bin/activate
python hmi_client.py
```

The HMI polls once per second and displays:

- Communication state
- Last successful poll time
- Tank level and trend
- Temperature
- Pressure
- Pump and valve states
- Operating mode
- Alarm setpoints
- Automatic-control setpoints
- Active and acknowledged alarms

ANSI terminal colors are used for alarm state.
