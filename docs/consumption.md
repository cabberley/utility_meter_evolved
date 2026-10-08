# Consumption meters

[All guides](README.md) · [Source and option reference](getting-started.md)

## Daily electricity

**Goal:** show electricity used today, rather than the lifetime reading.

**Prerequisite:** a cumulative energy sensor such as `sensor.grid_import_energy`, reporting kWh.

1. Open **Settings → Devices & services → Helpers → Create helper → Utility Meter Next Gen**.
2. Enter `Electricity today` as the name.
3. Select your grid import energy sensor as **Input sensor for Metering**.
4. Leave **Input Calculation Sensor** empty.
5. Choose **Create using a Predefined reset cycle** and submit.
6. Use these settings, then submit:

| Setting | Value |
| --- | --- |
| **Predefined Reset Cycle** | Daily |
| **Offset** | All zero |
| **Tariffs** | Empty |
| **Delta Values** | Off |
| **Net Consumption** | Off |
| **Periodically resetting** | Off for a never-resetting lifetime counter; on if it can reset |
| **Calibration Value for Consumption** | `0` |
| **Calibration Sensor for Consumption** | Empty |

**Check:** with a baseline of `2450.00 kWh`, the next reading of `2450.75 kWh` adds `0.75 kWh`. With zero offset, the daily meter resets at local midnight. Inspect `last_period` after the reset to see yesterday's collected consumption.

If you also need month/year totals, use the [multiple-cycle guide](multiple-cycles.md) instead of creating each meter separately.

## Monthly water or gas

**Goal:** show consumption during the calendar month.

Follow the daily electricity steps, with these changes:

| Field | Water example | Gas example |
| --- | --- | --- |
| Name | `Water this month` | `Gas this month` |
| Source | Cumulative water sensor in m³ | Cumulative gas sensor in m³ or kWh |
| Cycle | Monthly | Monthly |
| Calculation input | Empty | Empty |

Use Delta Values off for a cumulative counter and select Periodically resetting according to the device's behavior.

**Check:** a water reading from `82.100` to `82.125 m³` adds `0.025 m³` (25 litres). The meter retains the source's units; it does not automatically convert m³ to litres or gas volume into kWh.

For a billing month starting on the 15th, use [a custom billing schedule](schedules.md#monthly-billing-on-the-15th). For water priced per m³, the [cost guide](costs.md) works with that unit too. Gas priced per kWh needs an energy source or a separate, appropriate volume-to-energy conversion upstream.

## Import, export, and net consumption

For solar installations, separate import and export sources are usually easiest to understand:

1. Create a daily import meter from the cumulative **import energy** sensor.
2. Create a second daily export meter from the cumulative **export energy** sensor.
3. Leave **Net Consumption** off on both if both source counters only increase.
4. Add both entities to your dashboard; use separate rates if import cost and export revenue differ.

An increasing export counter is not a decreasing net counter. **Net Consumption** is for a source whose numeric changes can legitimately be positive or negative.

For example, a cumulative net-energy reading moving from `100` to `98 kWh` contributes `-2 kWh` when Net Consumption is enabled. With it disabled, that negative adjustment is ignored.

Do not combine import and export into one cost meter if they have different prices: a single calculation input cannot distinguish the import price from the export price.

## Sources that report increments

Enable **Delta Values** only when each source update is a fresh amount since the previous report.

Example: reports of `0.20`, `0.30`, and `0.10 kWh` contribute `0.60 kWh` in total. With a cumulative source, those same settings would incorrectly add the entire counter on each update.

Verify that the source integration emits each report, including consecutive equal amounts. This meter listens to source state changes; identical repeated increments that do not generate a state-change event will not be counted.

## Sources that reset

Leave **Periodically resetting** on for a device counter that resets to zero, and Net Consumption off unless genuine negative usage is intended.

A downward counter change is ignored with Net Consumption off; later positive changes are collected again. Do not assume this recovers consumption between the last report and a device reboot. Check the source's reporting behavior and compare against its own totals.

For a never-resetting counter, turning Periodically resetting off lets the meter compare a recovered reading against the last valid reading after an unavailable interval. Recovery is only reliable if the counter really did not reset during that interval.
