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
  <img alt="GitHub" src="https://img.shields.io/github/license/cabberley/utility_meter_evolved"> <img alt="GitHub Actions Workflow Status" src="https://img.shields.io/github/actions/workflow/status/cabberley/utility_meter_evolved/validate.yaml">
  <img alt="GitHub Issues or Pull Requests" src="https://img.shields.io/github/issues/cabberley/utility_meter_evolved"> <img alt="GitHub User's stars" src="https://img.shields.io/github/stars/cabberley">

</p>
<p align="center">
    <a href="https://github.com/hacs/integration"><img src="https://img.shields.io/badge/HACS-Custom-41BDF5.svg"></a>
</p>
<p align="center">
  <a href="https://www.buymeacoffee.com/cabberley" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-blue.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" ></a>
</p>

Based on the current "Utility Meter" component code in the Home-Assistant/Core. Acknowledgements to [DGomes](https://github.com/dgomes) who is the Code Owner of the core utlity Meter who really did all the hard logic work for the Meter Utility.

This Next Gen version should enable creation of any variation/flavour of scheduling of the recycle via the Home Assistant "Add Helper" and hopefully:

- Has completely removed reliance on manual configuration.yaml setups.
- Supports creating CRON scedules dirstly in the Helper.
- Adding several additional Predefined cycles, including 5min and 30min.
- Added more attributes to see what the parameters for the Meter are, these have been exlcuded from the recorder so won't add unnecessary data.
- Provided options capability to completely reconfigure the meter through the helper.

Optionally, this next gen utility meter can have a secondary sensor added to it to calculate a value at the end of the cycle period.


## Installation
Add this repository to your HACS repository list and then find "Utility Meter Next Gen"  and install or:

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=cabberley&repository=utility_meter_evolved&category=integration)

If you want to track via another sensor the calculated attribute variable, I would suggest another Great HACS Custom Integration written by gjohansson-ST [Attribute as Sensor](https://github.com/gjohansson-ST/attribute_as_sensor) this integration can monitor the attribute in the Utility Meter Next Gen and surface it as a Sensor in its own right.


