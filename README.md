# PyModbus SCADA Training Lab — Version 2

This version adds dynamic process behavior, alarms, automatic control, historian logging, and an improved terminal HMI.

Security-testing components are intentionally excluded. They can be added later as a separate project or module.

## Included Components

- `plc_server.py` — Modbus TCP PLC and process simulation
- `hmi_client.py` — live HMI with colors, alarms, communication state, and tank trend
- `operator_controls.py` — confirmed operator commands and setpoint management
- `historian.py` — CSV process historian
- `logs/plc_events.csv` — PLC events and alarm transitions
- `logs/process_history.csv` — sampled process data

## Documentation

- [Setup](docs/SETUP.md)
- [PLC](docs/PLC_SETUP.md)
- [HMI](docs/HMI_SETUP.md)
- [Operator Controls](docs/OPERATOR_CONTROLS_SETUP.md)
- [Historian](docs/HISTORIAN_SETUP.md)
- [Process Model](docs/PROCESS_MODEL.md)

## Recommended Run Order

```bash
python plc_server.py
python hmi_client.py
python operator_controls.py
python historian.py
```

Run each command in its own terminal after activating `.venv`.

## Isolation

Keep this lab on a VMware Host-Only network with no default gateway, NAT adapter, or bridged adapter.
