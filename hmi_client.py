#!/usr/bin/env python3

import time
from collections import deque
from datetime import datetime

from pymodbus.client import ModbusTcpClient

PLC_HOST = "127.0.0.1"
PLC_PORT = 5020
DEVICE_ID = 1
POLL_INTERVAL_SECONDS = 1
TREND_POINTS = 30

RESET = "\033[0m"
RED = "\033[31m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
CYAN = "\033[36m"
BOLD = "\033[1m"

SPARKS = "▁▂▃▄▅▆▇█"


def sparkline(values) -> str:
    if not values:
        return ""

    minimum = min(values)
    maximum = max(values)

    if maximum == minimum:
        return SPARKS[0] * len(values)

    chars = []
    for value in values:
        index = int((value - minimum) / (maximum - minimum) * (len(SPARKS) - 1))
        chars.append(SPARKS[index])
    return "".join(chars)


def alarm_text(name: str, active: bool, acknowledged: bool) -> str:
    if not active:
        return f"{GREEN}NORMAL{RESET}"

    state = "ACKNOWLEDGED" if acknowledged else "UNACKNOWLEDGED"
    color = YELLOW if acknowledged else RED
    return f"{color}{BOLD}{name}: {state}{RESET}"


def main() -> None:
    client = ModbusTcpClient(PLC_HOST, port=PLC_PORT, timeout=3)
    tank_history = deque(maxlen=TREND_POINTS)
    failure_count = 0

    if not client.connect():
        print(f"Could not connect to PLC at {PLC_HOST}:{PLC_PORT}")
        return

    try:
        while True:
            poll_started = time.monotonic()

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
            discrete = client.read_discrete_inputs(
                address=0,
                count=4,
                device_id=DEVICE_ID,
            )

            results = (inputs, holdings, coils, discrete)
            if any(result is None or result.isError() for result in results):
                failure_count += 1
                print("\033[2J\033[H", end="")
                print(f"{RED}{BOLD}COMMUNICATION FAILURE{RESET}")
                print(f"Consecutive failed polls: {failure_count}")
                print(f"PLC: {PLC_HOST}:{PLC_PORT}")
                time.sleep(POLL_INTERVAL_SECONDS)
                continue

            failure_count = 0
            last_poll = datetime.now().astimezone()

            tank_level = inputs.registers[0] / 10
            temperature = inputs.registers[1] / 10
            pressure = inputs.registers[2] / 10
            alarm_word = inputs.registers[3]

            pump_speed = holdings.registers[0]
            high_level_setpoint = holdings.registers[1] / 10
            high_temp_setpoint = holdings.registers[2] / 10
            mode = "AUTOMATIC" if holdings.registers[3] else "MANUAL"
            low_level_setpoint = holdings.registers[4] / 10
            auto_start = holdings.registers[5] / 10
            auto_stop = holdings.registers[6] / 10

            pump = bool(coils.bits[0])
            inlet_open = bool(coils.bits[1])

            high_level_alarm = bool(discrete.bits[0])
            high_temp_alarm = bool(discrete.bits[1])
            low_level_alarm = bool(discrete.bits[2])
            acknowledged = bool(discrete.bits[3])

            tank_history.append(tank_level)

            print("\033[2J\033[H", end="")
            print(f"{CYAN}{BOLD}============== SCADA HMI =============={RESET}")
            print(f"Communication:        {GREEN}ONLINE{RESET}")
            print(f"Last successful poll: {last_poll.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            print(f"PLC endpoint:         {PLC_HOST}:{PLC_PORT}")
            print()
            print(f"Tank level:           {tank_level:6.1f}%")
            print(f"Tank trend:           {sparkline(tank_history)}")
            print(f"Temperature:          {temperature:6.1f} C")
            print(f"Pressure:             {pressure:6.1f} PSI")
            print()
            print(f"Pump:                 {'ON' if pump else 'OFF'}")
            print(f"Inlet valve:          {'OPEN' if inlet_open else 'CLOSED'}")
            print(f"Pump speed:           {pump_speed}%")
            print(f"Operating mode:       {mode}")
            print()
            print(f"High-level setpoint:  {high_level_setpoint:.1f}%")
            print(f"Low-level setpoint:   {low_level_setpoint:.1f}%")
            print(f"High-temp setpoint:   {high_temp_setpoint:.1f} C")
            print(f"Auto start level:     {auto_start:.1f}%")
            print(f"Auto stop level:      {auto_stop:.1f}%")
            print()
            print(f"{BOLD}ALARMS{RESET} — word {alarm_word}")
            print(alarm_text("High level", high_level_alarm, acknowledged))
            print(alarm_text("High temperature", high_temp_alarm, acknowledged))
            print(alarm_text("Low level", low_level_alarm, acknowledged))
            print(f"{CYAN}{BOLD}========================================{RESET}")

            elapsed = time.monotonic() - poll_started
            time.sleep(max(0.0, POLL_INTERVAL_SECONDS - elapsed))

    except KeyboardInterrupt:
        print("\nStopping HMI.")
    finally:
        client.close()


if __name__ == "__main__":
    main()
