#!/usr/bin/env python3

import csv
import time
from datetime import datetime, timezone
from pathlib import Path

from pymodbus.client import ModbusTcpClient

PLC_HOST = "127.0.0.1"
PLC_PORT = 5020
DEVICE_ID = 1
SAMPLE_INTERVAL_SECONDS = 2

LOG_DIR = Path(__file__).resolve().parent / "logs"
PROCESS_LOG = LOG_DIR / "process_history.csv"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    new_file = not PROCESS_LOG.exists()

    client = ModbusTcpClient(PLC_HOST, port=PLC_PORT, timeout=3)
    if not client.connect():
        print(f"Could not connect to PLC at {PLC_HOST}:{PLC_PORT}")
        return

    with PROCESS_LOG.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)

        if new_file:
            writer.writerow(
                [
                    "timestamp_utc",
                    "tank_level_percent",
                    "temperature_c",
                    "pressure_psi",
                    "alarm_word",
                    "pump_running",
                    "inlet_valve_open",
                    "pump_speed_percent",
                    "mode",
                ]
            )

        try:
            print(f"Historian logging to {PROCESS_LOG}")
            print("Press Ctrl+C to stop.")

            while True:
                inputs = client.read_input_registers(
                    address=0,
                    count=4,
                    device_id=DEVICE_ID,
                )
                holdings = client.read_holding_registers(
                    address=0,
                    count=7,
                    device_id=DEVICE_ID,
                )
                coils = client.read_coils(
                    address=0,
                    count=4,
                    device_id=DEVICE_ID,
                )

                if any(result is None or result.isError() for result in (inputs, holdings, coils)):
                    print("Historian read failed; retrying.")
                    time.sleep(SAMPLE_INTERVAL_SECONDS)
                    continue

                writer.writerow(
                    [
                        utc_now(),
                        inputs.registers[0] / 10,
                        inputs.registers[1] / 10,
                        inputs.registers[2] / 10,
                        inputs.registers[3],
                        int(bool(coils.bits[0])),
                        int(bool(coils.bits[1])),
                        holdings.registers[0],
                        "automatic" if holdings.registers[3] else "manual",
                    ]
                )
                handle.flush()
                time.sleep(SAMPLE_INTERVAL_SECONDS)

        except KeyboardInterrupt:
            print("\nStopping historian.")
        finally:
            client.close()


if __name__ == "__main__":
    main()
