# Notice

New Custom Component currently in Dev
HAVE FUN! 😎

Based on the current "Utility Meter" component code in the Home-Assistant/Core. Acknowledgements to [DGomes](https://github.com/dgomes) who is the Code Owner of the core utlity Meter who really did all the hard logic work for the Meter Utility.

This Next Gen version should enable creation of any variation/flavour of scheduling of the recycle via the Home Assistant "Add Helper" and hopefully:
- has completely removed reliance on manual configuration.yaml setups.
- supports creating CRON scedules dirstly in the Helper.
- adding several additional Predefined cycles, including 5min and 30min.
- added more attributes to see what the parameters for the Meter are, these have been exlcuded from the recorder so won't add unnecessary data.
- provided options capability to completely reconfigure the meter through the helper.

Optionally, this next gen utility meter can have a secondary sensor added to it to calculate a value at the end of the cycle period.

> NOTE: With the secondary Sensor and the calculations, this Beta version only:
> - calculates at the end of the cycle and not during it.
> - Uses the value of the secondary sensor at that moment in time for the calculation
> - I'm still dreaming up ways to calculate during the cycle, with consideration that the secondary sensor value at the beginning my not be right when the meter sensor update event triggers the utlity meter to do its calcualtion.

## Installation
Add this repository to your HACS repository list and then find "Utility Meter Next Gen"  and install or:

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=cabberley&repository=utility_meter_evolved&category=integration)

If you want to track via another sensor the calculated attribute variable, I would suggest another Great HACS Custom Integration written by gjohansson-ST [Attribute as Sensor](https://github.com/gjohansson-ST/attribute_as_sensor) this integration can monitor the attribute in the Utility Meter Next Gen and surface it as a Sensor in its own right.


## Next steps
- More to Come as I tidy it up for Genernal Release

