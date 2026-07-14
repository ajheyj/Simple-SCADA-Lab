#!/usr/bin/env python3

import csv
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from pymodbus import pymodbus_apply_logging_config
from pymodbus.datastore import (
    ModbusDeviceContext,
    ModbusSequentialDataBlock,
    ModbusServerContext,
)
from pymodbus.server import StartTcpServer

PLC_ADDRESS = "0.0.0.0"
PLC_PORT = 5020
SCAN_INTERVAL_SECONDS = 1.0

LOG_DIR = Path(__file__).resolve().parent / "logs"
EVENT_LOG = LOG_DIR / "plc_events.csv"

# Coils
PUMP_COIL = 0
INLET_VALVE_COIL = 1
ALARM_ACK_COMMAND_COIL = 2
ALARM_RESET_COMMAND_COIL = 3

# Discrete inputs
HIGH_LEVEL_ALARM_DI = 0
HIGH_TEMP_ALARM_DI = 1
LOW_LEVEL_ALARM_DI = 2
ALARM_ACKNOWLEDGED_DI = 3

# Input registers (scaled by 10 where noted)
TANK_LEVEL_IR = 0
TEMPERATURE_IR = 1
PRESSURE_IR = 2
ALARM_WORD_IR = 3

# Holding registers
PUMP_SPEED_HR = 0
HIGH_LEVEL_SETPOINT_HR = 1
HIGH_TEMP_SETPOINT_HR = 2
MODE_HR = 3
LOW_LEVEL_SETPOINT_HR = 4
AUTO_START_LEVEL_HR = 5
AUTO_STOP_LEVEL_HR = 6

MODE_MANUAL = 0
MODE_AUTOMATIC = 1


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_event(event_type: str, message: str) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    new_file = not EVENT_LOG.exists()

    with EVENT_LOG.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        if new_file:
            writer.writerow(["timestamp_utc", "event_type", "message"])
        writer.writerow([utc_now(), event_type, message])


def build_device() -> ModbusDeviceContext:
    coils = ModbusSequentialDataBlock(1, [False] * 100)
    discrete_inputs = ModbusSequentialDataBlock(1, [False] * 100)

    input_values = [
        500,  # Tank level: 50.0%
        250,  # Temperature: 25.0 C
        0,    # Pressure: 0.0 PSI
        0,    # Alarm word
    ] + ([0] * 96)

    holding_values = [
        50,   # Pump speed: 50%
        800,  # High-level alarm: 80.0%
        700,  # High-temperature alarm: 70.0 C
        0,    # Mode: 0 manual, 1 automatic
        150,  # Low-level alarm: 15.0%
        700,  # Automatic pump start level: 70.0%
        300,  # Automatic pump stop level: 30.0%
    ] + ([0] * 93)

    return ModbusDeviceContext(
        di=discrete_inputs,
        co=coils,
        ir=ModbusSequentialDataBlock(1, input_values),
        hr=ModbusSequentialDataBlock(1, holding_values),
    )


def read_values(device: ModbusDeviceContext, function_code: int, address: int, count: int):
    return device.getValues(function_code, address, count=count)


def write_values(device: ModbusDeviceContext, function_code: int, address: int, values):
    device.setValues(function_code, address, values)


def process_loop(device: ModbusDeviceContext) -> None:
    tank_level = 50.0
    temperature = 25.0
    pressure = 0.0

    acknowledged = False
    previous_alarm_word = 0
    previous_pump = False
    previous_valve = False
    previous_mode = MODE_MANUAL

    append_event("SYSTEM", "PLC process simulation started")

    while True:
        cycle_start = time.monotonic()

        coils = read_values(device, 1, 0, 4)
        holdings = read_values(device, 3, 0, 7)

        pump_command = bool(coils[PUMP_COIL])
        inlet_open = bool(coils[INLET_VALVE_COIL])
        ack_command = bool(coils[ALARM_ACK_COMMAND_COIL])
        reset_command = bool(coils[ALARM_RESET_COMMAND_COIL])

        pump_speed = max(0, min(100, int(holdings[PUMP_SPEED_HR])))
        high_level_setpoint = holdings[HIGH_LEVEL_SETPOINT_HR] / 10.0
        high_temp_setpoint = holdings[HIGH_TEMP_SETPOINT_HR] / 10.0
        mode = int(holdings[MODE_HR])
        low_level_setpoint = holdings[LOW_LEVEL_SETPOINT_HR] / 10.0
        auto_start_level = holdings[AUTO_START_LEVEL_HR] / 10.0
        auto_stop_level = holdings[AUTO_STOP_LEVEL_HR] / 10.0

        if mode == MODE_AUTOMATIC:
            if tank_level >= auto_start_level:
                pump_command = True
            elif tank_level <= auto_stop_level:
                pump_command = False
            write_values(device, 5, PUMP_COIL, [pump_command])

        inlet_rate = 0.9 if inlet_open else 0.0
        pump_rate = (pump_speed / 100.0) * 1.4 if pump_command else 0.0
        tank_level += inlet_rate - pump_rate
        tank_level = max(0.0, min(100.0, tank_level))

        target_pressure = (pump_speed / 100.0) * 45.0 if pump_command else 0.0
        pressure += (target_pressure - pressure) * 0.35

        ambient_temperature = 25.0
        heat_target = ambient_temperature + ((pump_speed / 100.0) * 18.0 if pump_command else 0.0)
        temperature += (heat_target - temperature) * 0.05

        high_level_alarm = tank_level >= high_level_setpoint
        high_temp_alarm = temperature >= high_temp_setpoint
        low_level_alarm = tank_level <= low_level_setpoint

        alarm_word = (
            (1 if high_level_alarm else 0)
            | (2 if high_temp_alarm else 0)
            | (4 if low_level_alarm else 0)
        )

        if alarm_word == 0:
            acknowledged = False
        elif ack_command:
            acknowledged = True
            write_values(device, 5, ALARM_ACK_COMMAND_COIL, [False])

        if reset_command:
            if alarm_word == 0:
                acknowledged = False
                append_event("ALARM_RESET", "Alarm reset completed")
            else:
                append_event("ALARM_RESET_REJECTED", "Reset requested while alarm condition remains active")
            write_values(device, 5, ALARM_RESET_COMMAND_COIL, [False])

        write_values(
            device,
            4,
            0,
            [
                int(round(tank_level * 10)),
                int(round(temperature * 10)),
                int(round(pressure * 10)),
                alarm_word,
            ],
        )

        write_values(
            device,
            2,
            0,
            [
                high_level_alarm,
                high_temp_alarm,
                low_level_alarm,
                acknowledged,
            ],
        )

        if pump_command != previous_pump:
            append_event("PUMP", f"Pump {'started' if pump_command else 'stopped'}")
            previous_pump = pump_command

        if inlet_open != previous_valve:
            append_event("INLET_VALVE", f"Inlet valve {'opened' if inlet_open else 'closed'}")
            previous_valve = inlet_open

        if mode != previous_mode:
            append_event("MODE", "Automatic mode selected" if mode == MODE_AUTOMATIC else "Manual mode selected")
            previous_mode = mode

        if alarm_word != previous_alarm_word:
            if alarm_word:
                append_event("ALARM", f"Alarm word changed to {alarm_word}")
            else:
                append_event("ALARM_CLEAR", "All alarm conditions cleared")
            previous_alarm_word = alarm_word

        elapsed = time.monotonic() - cycle_start
        time.sleep(max(0.0, SCAN_INTERVAL_SECONDS - elapsed))


def main() -> None:
    pymodbus_apply_logging_config("INFO")
    device = build_device()
    context = ModbusServerContext(devices=device, single=True)

    worker = threading.Thread(
        target=process_loop,
        args=(device,),
        daemon=True,
        name="plc-process-loop",
    )
    worker.start()

    print(f"Starting simulated PLC on {PLC_ADDRESS}:{PLC_PORT}")
    print("Dynamic process simulation is active.")
    print("Press Ctrl+C to stop.")

    StartTcpServer(
        context=context,
        address=(PLC_ADDRESS, PLC_PORT),
    )


if __name__ == "__main__":
    main()
