# Process Model

## Tank

- Opening the inlet valve raises tank level.
- Running the pump lowers tank level.
- Higher pump speed increases the drain rate.
- Tank level is clamped between 0% and 100%.

## Pressure

- Pressure rises toward a target based on pump speed while the pump is running.
- Pressure decays toward zero when the pump stops.

## Temperature

- Temperature trends toward ambient when the pump is stopped.
- Running the pump raises the target temperature according to pump speed.

## Automatic Mode

- The pump starts when tank level reaches the automatic start level.
- The pump stops when tank level reaches the automatic stop level.
- The inlet valve remains operator-controlled.

## Alarms

- High-level alarm
- Low-level alarm
- High-temperature alarm

Alarm bits are also combined into an alarm word:

| Bit | Value | Alarm |
|---:|---:|---|
| 0 | 1 | High level |
| 1 | 2 | High temperature |
| 2 | 4 | Low level |

Examples:

- Alarm word `1` = high level
- Alarm word `4` = low level
- Alarm word `3` = high level and high temperature
