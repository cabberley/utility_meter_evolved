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
  <img alt="GitHub Issues or Pull Requests" src="https://img.shields.io/github/issues/cabberley/utility_meter_evolved"> <img alt="GitHub User's stars" src="https://img.shields.io/github/stars/cabberley"> <img alt="GitHub Downloads (all assets, all releases)" src="https://img.shields.io/github/downloads/cabberley/utility_meter_evolved/total">


</p>
<p align="center">
    <a href="https://github.com/hacs/integration"><img src="https://img.shields.io/badge/HACS-Custom-41BDF5.svg"></a>
</p>
<p align="center">
  <a href="https://www.buymeacoffee.com/cabberley" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-blue.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" ></a>
</p>

This custom HACS integration for Home Assistant provides an enhanced set of capabilities for the basic Utility Meter Helper.

Based on the current "Utility Meter" component code in the Home-Assistant/Core. Acknowledgements to [DGomes](https://github.com/dgomes) who is the Code Owner of the core utlity Meter who really did all the hard logic work for the Meter Utility.

There are lots of enhancements that the Utility Meter Next Gen has added to the original Utility Meter include:

- **Create multiple period sensors, optionally with Tariffs and individual Calculation sensors from a single Source and Calculation Sensor**
- Creating Cron schedule patterns via the Frontend of HA, you no longer need to create them in configuration.yaml!
- Additional Predefined schedules that should accomodate the majority of people's needs.
- The addition of an optional secondary sensor/entity that will be used to calculate a value based on the Meters value.
- Option to create an additional Sensor for the Calculated Value, if you have added a sensor to create a calculated value.
- All settings of the Meter can be modified through the Frontend. The options reflect the schedule type you created the Meter with (Predefined or CRON).
- An option to create a "Total" Tariff that will not pause like a normal Tariff does. (You can create a single Sensor set that collects for each tariff period plus the total)
- Additional extra attributes have been added to the Sensor, so you can see quickly the key information about the sensor and what it is doing.
- Additional attributes that don't change are not recorded in thhe Recorder DB to avoid unnecessary recorder data bloat.
- Calibration values can now be set and modified through the Utility Meter configuration.

These enhancements should provide a very versatile solution to simplify creating, using meters and calculating a secondary value.

## Installation

**The Utility Meter Next Gen is now available directly from HACS, no need to add the repository anymore!!**

Go to the HACS Dashboard in your Home Assistant, and search for "Utility Meter Next Gen", download and restart your HA.

OR

1. Add this [repository](https://github.com/cabberley/utility_meter_evolved) via your custom Repositories option in the HACS dashboard as an "Integration Type" and then find "Utility Meter Next Gen" in the repository list, download and restart your Home Assistant.
2. Use the link below to add it to your system:

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=cabberley&repository=utility_meter_evolved&category=integration)

## Using the Utility Meter Next Gen

After installing the integration, you should now find **Utility Meter Next Gen** in the **Create Helper** list under the Settings --> Devices & services --> Helpers dashboard.

Follow the instructions to setup your new Meter with an optional Caculation Sensor.

## Using the Multi Predefined reset cycle Meters

This great new feature will take the pain away from setting multiple individual Meters to track your usuage and $$. If you like to track your meters for various periods like every 5 minutes, 30 minutes, hourly, daily, monthly or yearly, this feature enables you to create a single config that will deliver:

- Individual sensors for each time period.
- Individual Tariff based sensors for each tariff for each time period.
- Create a separate Calculation Sensor for every Meter created.
- A single Select for the tariff selection that will pause/collect all the sensors in alignment with your Select choice.
- After creation, you can go back and change (add/remove) Predefiend Reset Cycles and if you created a Tariff based set change the list of Tariffs. You can also add or remove the Calculation Sensor if you created a Utility Meter with a Calculation source.

In addition to all of that, this special Multiple sensor config, always you to calibrate one of those periods. For example, those that are tracking their daily energy costs, may have a daily "service/connection" charge. With this Config, you can tell the setup to only apply the calibration calculation value to just the "Daily" meter.

When you create a new Utlity Meter using the new "Multi Predefined reset cycle Meters", it is very similar to creating a normal predefined recycle Meter with a few additional options.

1. After choosing your Source Sensors, you are then presented with the next step, select the various time periods you would like meters for. You can choose 1 or choose them all!
2. After submitting the Predefined list you are then able to optional add some other more granular settings.
3. The settings will be familiar to the normal Predefined Recycle Meter with the following changes:
   1. For both the calibration sensors there is a new option to select which of the predefined cycles to apply it to.
   2. For simplicity, the ability to set an Offset to the recycle times has been removed.

## Some Additional helpers

### Warning

**Do not change the "Entity ID" after creating your meter, it will break the Sensors that this integration creates**

### Selection of Sensors to Monitor

**Some notes on selecting Input Sensor:**

1. Make sure to select the right type of sensor to Meter, for example if you wanting to monitor Energy Consumption, make usre it is an Energy Wh/kWh/MWh are monitoring, not a Power (W/kW/MW). it should be a State Class that is "Total"/"Total Increasing" not a Measurement.
2. To enable flexibility, the setup only checks that the Input Sensor has a numeric Value, i.e. it should reject a text value. However if it is a mix of numbers and text, it will strip out the text and use the numbers it finds. This could lead to strange results.

**Some notes on selecting Calculation Sensor:**

1. This should be a sensor that has a numeric value, not a text value, it is going to multiply its value with the input sensor.
2. This sensor, for example if you are calculating the cost of your energy, would be a one that has a currency value reflecting the cost per x at the time.
3. The Sensor updates the calculation value when the input sensor value changes, the calculation will use the current value of the Calculation sensor in the calculation at that time, instances where there is a lag in the Calculation Sensor's new value for the period will be reflected in the calaculations until the new value for the calaculation sensor updates for the period. In theory by the end of the period it would be assumed that the Calculation Sensor reflects the true/final value for that period and the last calculations for the period should now be correct. Unfortunately, there isn't really anything to address this without creating all sorts of weird case handling scenarios.

### Some notes on optional configuration settings for your Meters

**Some notes on the use of Tariffs**

1. You only have the option to create Tariffs when you initally create the Utlity Meter.
2. If you did create a Tariff you can remove or add additional tariffs and reconfigure.

**Some notes on the Calibration setting:**

1. There are seperate calibration settings for the consumption sensor and the Calculating sensor, these are independant of each other.
2. Each time the meter is reset, the calibration value will be applied to the starting value for the next cycle.
3. If you are using Tariffs, the Calibration will only apply to a "Total" tariff, not the other ones you create.

A good example of using the calibration sensor is if you are tracking the Cost of your Energy consumption each day. Your energy supplier my have a fixed "Daily" charge in addition to your consumption charges. By Calibrating the Cost sensor to the daily charge, you can combine your fixed and variable costs into the value giving you a more accurate value of your daily costs.

**Some notes on the Multiplier setting:**

1. This value is used to align your **RAW** Consumption value to the Calculation Sensors scale.
2. If you do not need to adjust the multiplier leave it set to 1, if you change it to 0 then your calculated value will always be 0.

**Examples:**

- if your Consumption is being recorded as MWh and your Calculation Sensor is $/kWh then you want to convert your MWh to kWH to achieve this the multiplier should be set to 1000.
- if your Consumption is being recorded as Wh and your Calculation Sensor is $/kWh then you want to convert your MWh to kWH to achieve this the multiplier should be set to 0.0001.

