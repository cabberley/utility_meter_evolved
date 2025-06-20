"""Constants for the utility meter component."""

DOMAIN = "utility_meter_evolved"

EVERY_FIVE_MINUTES = "every-five-minutes"
HALF_HOURLY = "half-hourly"
QUARTER_HOURLY = "quarter-hourly"
HOURLY = "hourly"
DAILY = "daily"
WEEKLY = "weekly"
MONTHLY = "monthly"
BIMONTHLY = "bimonthly"
QUARTERLY = "quarterly"
HALF_YEARLY = "half-yearly"
YEARLY = "yearly"

METER_TYPES = [
    EVERY_FIVE_MINUTES,
    QUARTER_HOURLY,
    HALF_HOURLY,
    HOURLY,
    DAILY,
    WEEKLY,
    MONTHLY,
    BIMONTHLY,
    QUARTERLY,
    HALF_YEARLY,
    YEARLY,
]

DATA_UTILITY = "utility_meter_evolved_data"
DATA_TARIFF_SENSORS = "utility_meter_evolved_sensors"

CONF_CONFIG_CRON = "cron"
CONF_CONFIG_PREDEFINED = "predefined"
CONF_CONFIG_TYPE = "config_type"
CONF_CRON_PATTERN = "cron"
CONF_METER = "meter"
CONF_METER_TYPE = "cycle"
CONF_METER_OFFSET = "offset"
CONF_METER_OFFSET_DURATION_DEFAULT = {"days":0, "hours":0, "minutes":0, "seconds":0}
CONF_METER_DELTA_VALUES = "delta_values"
CONF_METER_NET_CONSUMPTION = "net_consumption"
CONF_METER_PERIODICALLY_RESETTING = "periodically_resetting"
CONF_PAUSED = "paused"
CONF_REMOVE_CALC_SENSOR = "remove_calc_sensor"
CONF_SOURCE_CALC_SENSOR = "source_calc_sensor"
CONF_SOURCE_SENSOR = "source"
CONF_TARIFFS = "tariffs"
CONF_TARIFF = "tariff"
CONF_TARIFF_ENTITY = "tariff_entity"

CONF_SENSOR_ALWAYS_AVAILABLE = "always_available"

CONFIG_TYPES = [
    CONF_CONFIG_CRON,
    CONF_CONFIG_PREDEFINED,
]

ATTR_TARIFF = "tariff"
ATTR_TARIFFS = "tariffs"
ATTR_VALUE = "value"
ATTR_CRON_PATTERN = "cron pattern"
ATTR_NEXT_RESET = "next_reset"

SIGNAL_START_PAUSE_METER = "utility_meter_evolved_start_pause"
SIGNAL_RESET_METER = "utility_meter_evolved_reset"

SERVICE_RESET = "reset"
SERVICE_CALIBRATE_METER = "calibrate"
