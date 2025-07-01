<h1 align="center">
  <a><img src="https://raw.githubusercontent.com/cabberley/utility_meter_evolved/main/images/Banner.png" width="480"></a>
  <br>
  <i>Utility Meter Next Generation</i>
  <br>
  <h3 align="center">
    <i>Home Assistant Custom Integration provding more options for Utility Meters. </i>
    <br>
  </h3>
</h1>

<p align="center">
  <href="https://github.com/cabberley/utility_meter_evolved/releases"><img src="https://img.shields.io/github/v/release/cabberley/utility_meter_evolved?display_name=tag&include_prereleases&sort=semver" alt="Current version"> <img alt="GitHub Release Date" src="https://img.shields.io/github/release-date/cabberley/utility_meter_evolved">
  <img alt="GitHub" src="https://img.shields.io/github/license/cabberley/utility_meter_evolved"> <img alt="GitHub Actions Workflow Status" src="https://img.shields.io/github/actions/workflow/status/cabberley/utility_meter_evolved/validate.yml">
  <img alt="GitHub Issues or Pull Requests" src="https://img.shields.io/github/issues/cabberley/utility_meter_evolved"> <img alt="GitHub User's stars" src="https://img.shields.io/github/stars/cabberley">

</p>
<p align="center">
    <a href="https://github.com/hacs/integration"><img src="https://img.shields.io/badge/HACS-Custom-41BDF5.svg"></a>
</p>
<p align="center">
  <a href="https://www.buymeacoffee.com/cabberley" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-blue.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" ></a>
</p>

This custom HACS integration for Home Assistant provides an enhanced set of capabilities for the basic Utility Meter Helper.

Based on the current "Utility Meter" component code in the Home-Assistant/Core. Acknowledgements to [DGomes](https://github.com/dgomes) who is the Code Owner of the core utlity Meter who really did all the hard logic work for the Meter Utility.

The main enhancements that the Utility Meter Next Gen has added to the original Utility Meter include:

- Creating Cron schedule patterns via the Frontend of HA, you no longer need to create them in configuration.yaml!
- Additional Predefined schedules that should accomodate the majority of people's needs.
- All settings of the Meter can be modified through the Frontend. The options reflect the schedule type you created the Meter with (Predefined or CRON).
- An option to create a "Total" Tariff that will not pause like a normal Tariff does. (You can create a sungle Sensor set that collects for each tariff period plus the total)
- The addition of an optional secondary sensor/entity that will be used to calculate a value based on the Meters value.
- Additional extra attributes have been added to the Sensor, so you can see quickly the key information about the sensor and what it is doing.
- Additional attributes that don't change are not recorded in thhe Recorder DB to avoid unnecessary recorder data bloat.
- Calibration values can now be set and modified through the Utility Meter configuration.

These enhancements should provide a very versatile solution to simplify creating, using meters and calculating a secondary value.

## Installation

Add this [repository](https://github.com/cabberley/utility_meter_evolved) via your custom Repositories option in the HACS dashboard as an "Integration Type" and then find "Utility Meter Next Gen" in the repository list, download and restart your Home Assistant.

Or preferably easier use the link below to add it to your system:

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=cabberley&repository=utility_meter_evolved&category=integration)

> **NOTE: Currently waiting for this new integration to be added to the HACS repository of Custom Integrations.**

## Using the Utility Meter Next Gen

After installing the integration, you should now find **Utility Meter Next Gen** in the **Create Helper** list under the Settings --> Devices & services --> Helpers dashboard.

Follow the instructions to setup your new Meter with an optional Caculation Sensor.

## Some Additional helpers

### Selection of Sensors to Monitor

**Some notes on selecting Input Sensor:**

1. Make sure to select the right type of sensor to Meter, for example if you wanting to monitor Energy Consumption, make usre it is an Energy Wh/kWh/MWh are monitoring, not a Power (W/kW/MW). it should be a State Class that is "Total"/"Total Increasing" not a Measurement.
2. To enable flexibility, the setup only checks that the Input Sensor has a numeric Value, i.e. it should reject a text value. However if it is a mix of numbers and text, it will strip out the text and use the numbers it finds. This could lead to strange results.

**Some notes on selecting Calculation Sensor:**

1. This should be a sensor that has a numeric value, not a text value, it is going to multiply its value with the input sensor.
2. This sensor, for example if you are calculating the cost of your energy, would be a one that has a currency value reflecting the cost per x at the time.
3. The Sensor updates the calculation value when the input sensor value changes, the calculation will use the current value of the Calculation sensor in the calculation at that time, instances where there is a lag in the Calculation Sensor's new value for the period will be reflected in the calaculations until the new value for the calaculation sensor updates for the period. In theory by the end of the period it would be assumed that the Calculation Sensor reflects the true/final value for that period and the last calculations for the period should now be correct. Unfortunately, there isn't really anything to address this without creating all sorts of weird case handling scenarios.

**Some notes on the Calibration setting:**

1. There are seperate calibration settings for the consumption sensor and the Calculating sensor, these are independant of each other.
2. Each time the meter is reset, the calibration value will be applied to the starting value for the next cycle.

A good example of using the calibration sensor is if you are tracking the Cost of your Energy consumption each day. Your energy supplier my have a fixed "Daily" charge in addition to your consumption charges. By Calibrating the Cost sensor to the daily charge, you can combine your fixed and variable costs into the value giving you a more accurate value of your daily costs.

**Some notes on the Multiplier setting:**

1. This value is used to align your **RAW** Consumption value to the Calculation Sensors scale.
2. If you do not need to adjust the multiplier leave it set to 1, if you change it to 0 then your calculated value will always be 0.

**Examples:**

- if your Consumption is being recorded as MWh and your Calculation Sensor is $/kWh then you want to convert your MWh to kWH to achieve this the multiplier should be set to 1000.
- if your Consumption is being recorded as Wh and your Calculation Sensor is $/kWh then you want to convert your MWh to kWH to achieve this the multiplier should be set to 0.0001.

### If you want to track one of the attributes like "Last period calculated value" as a Sensor?

If you want to track via another sensor the calculated attribute variable, I would suggest another Great HACS Custom Integration written by gjohansson-ST [Attribute as Sensor](https://github.com/gjohansson-ST/attribute_as_sensor) this integration can monitor an attribute in the Utility Meter Next Gen and surface it as a Sensor in its own right.
