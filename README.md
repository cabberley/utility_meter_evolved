<h1 align="center">
  <a><img src="https://raw.githubusercontent.com/cabberley/utility_meter_evolved/main/images/Banner.png" width="480"></a>
  <br>
  <i>Utility Meter Next Generation</i>
  <br>
  <h3 align="center">
    <i>Home Assistant custom integration providing more options for utility meters.</i>
    <br>
  </h3>
</h1>

<p align="center">
  <a><img src="https://img.shields.io/github/v/release/cabberley/utility_meter_evolved?display_name=tag&include_prereleases&sort=semver" alt="Current version"></a> <img alt="GitHub Release Date" src="https://img.shields.io/github/release-date/cabberley/utility_meter_evolved">
  <img alt="GitHub" src="https://img.shields.io/github/license/cabberley/utility_meter_evolved"> <img alt="GitHub Actions Workflow Status" src="https://img.shields.io/github/actions/workflow/status/cabberley/utility_meter_evolved/validate.yml">
  <img alt="GitHub Issues or Pull Requests" src="https://img.shields.io/github/issues/cabberley/utility_meter_evolved"> <img alt="GitHub User's stars" src="https://img.shields.io/github/stars/cabberley"> <img alt="GitHub Downloads (all assets, all releases)" src="https://img.shields.io/github/downloads/cabberley/utility_meter_evolved/total">


</p>
<p align="center">
    <a href="https://github.com/hacs/integration"><img src="https://img.shields.io/badge/HACS-Custom-41BDF5.svg"></a>
</p>
<p align="center">
  <a href="https://www.buymeacoffee.com/cabberley" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-blue.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" ></a>
</p>

This custom HACS integration for Home Assistant provides an enhanced set of capabilities for the basic Utility Meter Helper.

Based on Home Assistant Core's Utility Meter component. Thanks to [DGomes](https://github.com/dgomes), the core Utility Meter code owner, for the original metering logic.

## Compatibility

Releases 2026.8.0 and newer require Home Assistant 2026.8.0 or later. Utility
Meter Next Gen entities link directly to their source device while the source
integration remains the device's sole owner, matching Home Assistant's current
device registry model.

## What can it do?

- Create consumption meters for one or several reset cycles from a single source.
- Split consumption into tariffs, with a continuously collecting `total` tariff.
- Accumulate costs using a rate sensor or `input_number`, optionally exposed as separate calculated sensors.
- Include a fixed charge or an entity-backed calibration value at each reset.
- Choose predefined schedules or enter custom CRON schedules in the UI.
- Reconfigure meters through the UI and inspect current/previous-period values.

Use accumulated **energy** (Wh/kWh/MWh), gas, or water readings as the source—not instantaneous power (W/kW) or flow rate. See [choosing a source](docs/getting-started.md#choose-your-source).

## Installation

**The Utility Meter Next Gen is now available directly from HACS, no need to add the repository anymore!!**

Go to the HACS Dashboard in your Home Assistant, and search for "Utility Meter Next Gen", download and restart your HA.

OR

1. Add this [repository](https://github.com/cabberley/utility_meter_evolved) via your custom Repositories option in the HACS dashboard as an "Integration Type" and then find "Utility Meter Next Gen" in the repository list, download and restart your Home Assistant.
2. Use the link below to add it to your system:

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=cabberley&repository=utility_meter_evolved&category=integration)

## Quick start

1. Install from HACS and restart Home Assistant.
2. Open **Settings → Devices & services → Helpers → Create helper**.
3. Choose **Utility Meter Next Gen**.
4. Give it a name, select a cumulative consumption sensor, and choose **Create using a Predefined reset cycle**.
5. Choose **Daily**, leave tariffs empty, and leave **Delta Values** and **Net Consumption** off for a normal cumulative import sensor.
6. Submit, then check the new entity in **Developer tools → States** after the source updates.

A new meter collects from setup onward; it does not reconstruct earlier consumption from history.

## Setup guides

Start with the [documentation hub](docs/README.md) or choose a scenario:

| What you want to track | Guide |
| --- | --- |
| Installation, source selection, and common settings | [Getting started](docs/getting-started.md) |
| Daily electricity, monthly water/gas, or solar import/export | [Consumption meters](docs/consumption.md) |
| Electricity cost, changing prices, and a daily standing charge | [Cost meters](docs/costs.md) |
| Peak/off-peak consumption with automatic tariff switching | [Tariffs](docs/tariffs.md) |
| Daily, monthly, and yearly sensors from one configuration | [Multiple reset cycles](docs/multiple-cycles.md) |
| Billing dates and custom reset times | [Schedules and CRON](docs/schedules.md) |
| Missing values, incorrect costs, calibration, and options | [Troubleshooting](docs/troubleshooting.md) |

The guides include worked examples, expected results, and labelled setup diagrams. The diagrams are illustrations, not screenshots of a live Home Assistant instance.

### Important details

- Select tariffs during initial setup if you need them. Existing tariff-based meters can have their tariff list edited later.
- Costs accumulate each consumption change multiplied by the **current** rate and adjustment factor. Changing the rate does not reprice previous consumption.
- Calibration sets a cycle's starting value; it is independent of the adjustment factor. Entity-backed calibration is read at initialization and each reset, not continuously.
- For a rate per kWh, use adjustment factor **1** for kWh, **0.001** for Wh, or **1000** for MWh. See the [conversion table](docs/costs.md#units-and-adjustment-factor).
- Entity IDs in the guides are examples. Use the IDs Home Assistant actually creates, and recheck dashboard/automation references after changing them.
