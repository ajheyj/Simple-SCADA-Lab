#!/usr/bin/env python3

from pymodbus.client import ModbusTcpClient

PLC_HOST = "127.0.0.1"
PLC_PORT = 5020
DEVICE_ID = 1

PUMP_COIL = 0
INLET_VALVE_COIL = 1
ALARM_ACK_COIL = 2
ALARM_RESET_COIL = 3

PUMP_SPEED_REGISTER = 0
HIGH_LEVEL_REGISTER = 1
HIGH_TEMP_REGISTER = 2
MODE_REGISTER = 3
LOW_LEVEL_REGISTER = 4
AUTO_START_REGISTER = 5
AUTO_STOP_REGISTER = 6


def write_succeeded(result) -> bool:
    if result is None:
        print("No response received from PLC.")
        return False
    if result.isError():
        print(f"PLC returned an error: {result}")
        return False
    return True


def read_integer(prompt: str, minimum: int, maximum: int) -> int | None:
    try:
        value = int(input(prompt).strip())
    except ValueError:
        print("Enter a whole number.")
        return None

    if not minimum <= value <= maximum:
        print(f"Value must be between {minimum} and {maximum}.")
        return None

    return value


def confirm(prompt: str) -> bool:
    return input(f"{prompt} [y/N]: ").strip().lower() == "y"


def show_menu() -> None:
    print(
        """
============ OPERATOR CONTROLS ============

1.  Start pump
2.  Stop pump
3.  Open inlet valve
4.  Close inlet valve
5.  Set pump speed
6.  Set high-level alarm
7.  Set low-level alarm
8.  Set high-temperature alarm
9.  Select manual mode
10. Select automatic mode
11. Set automatic pump start level
12. Set automatic pump stop level
13. Acknowledge active alarms
14. Reset cleared alarms
15. Show current PLC values
0.  Exit

===========================================
"""
    )


def show_status(client: ModbusTcpClient) -> None:
    coils = client.read_coils(address=0, count=4, device_id=DEVICE_ID)
    discrete = client.read_discrete_inputs(address=0, count=4, device_id=DEVICE_ID)
    inputs = client.read_input_registers(address=0, count=4, device_id=DEVICE_ID)
    holdings = client.read_holding_registers(address=0, count=7, device_id=DEVICE_ID)

    if any(result is None or result.isError() for result in (coils, discrete, inputs, holdings)):
        print("Unable to read complete PLC status.")
        return

    print("\n--------------- PLC STATUS ---------------")
    print(f"Pump:                    {'ON' if coils.bits[0] else 'OFF'}")
    print(f"Inlet valve:             {'OPEN' if coils.bits[1] else 'CLOSED'}")
    print(f"Tank level:              {inputs.registers[0] / 10:.1f}%")
    print(f"Temperature:             {inputs.registers[1] / 10:.1f} C")
    print(f"Pressure:                {inputs.registers[2] / 10:.1f} PSI")
    print(f"Alarm word:              {inputs.registers[3]}")
    print(f"Pump speed:              {holdings.registers[0]}%")
    print(f"High-level setpoint:     {holdings.registers[1] / 10:.1f}%")
    print(f"High-temp setpoint:      {holdings.registers[2] / 10:.1f} C")
    print(f"Operating mode:          {'AUTOMATIC' if holdings.registers[3] else 'MANUAL'}")
    print(f"Low-level setpoint:      {holdings.registers[4] / 10:.1f}%")
    print(f"Auto pump start level:   {holdings.registers[5] / 10:.1f}%")
    print(f"Auto pump stop level:    {holdings.registers[6] / 10:.1f}%")
    print(f"High-level alarm:        {'ACTIVE' if discrete.bits[0] else 'NORMAL'}")
    print(f"High-temperature alarm: {'ACTIVE' if discrete.bits[1] else 'NORMAL'}")
    print(f"Low-level alarm:         {'ACTIVE' if discrete.bits[2] else 'NORMAL'}")
    print(f"Alarm acknowledged:      {'YES' if discrete.bits[3] else 'NO'}")
    print("------------------------------------------\n")


def write_coil(client, address: int, value: bool, message: str) -> None:
    result = client.write_coil(
        address=address,
        value=value,
        device_id=DEVICE_ID,
    )
    if write_succeeded(result):
        print(message)


def write_register(client, address: int, value: int, message: str) -> None:
    result = client.write_register(
        address=address,
        value=value,
        device_id=DEVICE_ID,
    )
    if write_succeeded(result):
        print(message)


def main() -> None:
    client = ModbusTcpClient(PLC_HOST, port=PLC_PORT, timeout=3)

    if not client.connect():
        print(f"Could not connect to PLC at {PLC_HOST}:{PLC_PORT}")
        return

    try:
        while True:
            show_menu()
            choice = input("Select an option: ").strip()

            if choice == "1" and confirm("Start the pump?"):
                write_coil(client, PUMP_COIL, True, "Pump start command accepted.")

            elif choice == "2" and confirm("Stop the pump?"):
                write_coil(client, PUMP_COIL, False, "Pump stop command accepted.")

            elif choice == "3" and confirm("Open the inlet valve?"):
                write_coil(client, INLET_VALVE_COIL, True, "Inlet valve open command accepted.")

            elif choice == "4" and confirm("Close the inlet valve?"):
                write_coil(client, INLET_VALVE_COIL, False, "Inlet valve close command accepted.")

            elif choice == "5":
                value = read_integer("Pump speed, 0-100%: ", 0, 100)
                if value is not None and confirm(f"Set pump speed to {value}%?"):
                    write_register(client, PUMP_SPEED_REGISTER, value, f"Pump speed set to {value}%.")

            elif choice == "6":
                value = read_integer("High-level alarm, 0-100%: ", 0, 100)
                if value is not None and confirm(f"Set high-level alarm to {value}%?"):
                    write_register(client, HIGH_LEVEL_REGISTER, value * 10, f"High-level alarm set to {value}%.")

            elif choice == "7":
                value = read_integer("Low-level alarm, 0-100%: ", 0, 100)
                if value is not None and confirm(f"Set low-level alarm to {value}%?"):
                    write_register(client, LOW_LEVEL_REGISTER, value * 10, f"Low-level alarm set to {value}%.")

            elif choice == "8":
                value = read_integer("High-temperature alarm, 0-150 C: ", 0, 150)
                if value is not None and confirm(f"Set high-temperature alarm to {value} C?"):
                    write_register(client, HIGH_TEMP_REGISTER, value * 10, f"High-temperature alarm set to {value} C.")

            elif choice == "9" and confirm("Place the PLC in manual mode?"):
                write_register(client, MODE_REGISTER, 0, "Manual mode selected.")

            elif choice == "10" and confirm("Place the PLC in automatic mode?"):
                write_register(client, MODE_REGISTER, 1, "Automatic mode selected.")

            elif choice == "11":
                value = read_integer("Automatic pump start level, 0-100%: ", 0, 100)
                if value is not None and confirm(f"Set automatic start level to {value}%?"):
                    write_register(client, AUTO_START_REGISTER, value * 10, f"Automatic start level set to {value}%.")

            elif choice == "12":
                value = read_integer("Automatic pump stop level, 0-100%: ", 0, 100)
                if value is not None and confirm(f"Set automatic stop level to {value}%?"):
                    write_register(client, AUTO_STOP_REGISTER, value * 10, f"Automatic stop level set to {value}%.")

            elif choice == "13" and confirm("Acknowledge all active alarms?"):
                write_coil(client, ALARM_ACK_COIL, True, "Alarm acknowledgement sent.")

            elif choice == "14" and confirm("Reset cleared alarms?"):
                write_coil(client, ALARM_RESET_COIL, True, "Alarm reset request sent.")

            elif choice == "15":
                show_status(client)

            elif choice == "0":
                break

            elif choice not in {str(number) for number in range(16)}:
                print("Unknown option.")

    except KeyboardInterrupt:
        print("\nClosing operator console.")
    finally:
        client.close()


if __name__ == "__main__":
    main()
