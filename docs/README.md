# Utility Meter Next Gen setup guides

[Repository README](../README.md)

These guides describe the Home Assistant UI configuration of **Utility Meter Next Gen** (`utility_meter_next_gen`), not the built-in Utility Meter helper.

## Choose a scenario

| Scenario | Start here | What you will create |
| --- | --- | --- |
| First installation | [Getting started](getting-started.md) | A helper with the right source and settings |
| Electricity used today | [Daily consumption](consumption.md#daily-electricity) | A daily kWh sensor |
| Water or gas used this month | [Water and gas](consumption.md#monthly-water-or-gas) | A monthly volume or energy sensor |
| Solar import and export | [Import, export, and net consumption](consumption.md#import-export-and-net-consumption) | Separate import/export meters or a net meter |
| Energy cost and standing charge | [Cost meters](costs.md) | A consumption sensor and optional cost sensor |
| Peak/off-peak electricity | [Tariffs](tariffs.md) | Tariff sensors, a total, and a tariff selector |
| Several reporting periods | [Multiple reset cycles](multiple-cycles.md) | Independent daily/monthly/yearly meters |
| Billing on a particular date | [Schedules and CRON](schedules.md) | A meter with a custom reset schedule |
| Something is not working | [Troubleshooting](troubleshooting.md) | Checks for sources, prices, schedules, and options |

## Before following an example

- Releases 2026.8.0 and newer require Home Assistant 2026.8.0 or later.
- Entity IDs, prices, units, and tariff times are examples; replace them with your own.
- A meter collects new readings. It does not backfill earlier data.
- Reset periods follow Home Assistant's configured local time zone.
- Costs are estimates based on the readings and rates available at each update, not a replacement for a supplier bill.

## Visual walkthroughs

The [setup flow](getting-started.md#setup-flow) and [tariff diagram](tariffs.md#how-the-sensors-work) illustrate the configuration. They are **not live UI screenshots**: no configured Home Assistant instance was available to capture. Field order and wording may vary by version or language; the settings tables provide the values to enter.
