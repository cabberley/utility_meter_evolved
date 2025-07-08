"""Constants for the utility meter component."""

DOMAIN = "utility_meter_next_gen"

METER_NAME_EVERY_FIVE_MINUTES = "5 Minute"
METER_NAME_EVERY_TEN_MINUTES = "10 Minute"
METER_NAME_EVERY_TWENTY_MINUTES = "20 Minute"
METER_NAME_HALF_HOURLY = "30 Minute"
METER_NAME_QUARTER_HOURLY = "15 Minute"
METER_NAME_HOURLY = "Hourly"
METER_NAME_DAILY = "Daily"
METER_NAME_WEEKLY = "Weekly"
METER_NAME_MONTHLY = "Monthly"
METER_NAME_BIMONTHLY = "Bi Monthly"
METER_NAME_QUARTERLY = "Quarterly"
METER_NAME_HALF_YEARLY = "Half Yearly"
METER_NAME_YEARLY = "Yearly"

# Meter types
EVERY_FIVE_MINUTES = "every-five-minutes"
EVERY_TEN_MINUTES = "every-ten-minutes"
EVERY_TWENTY_MINUTES = "every-twenty-minutes"
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

# Meter type names
METER_NAME_TYPES = {
    EVERY_FIVE_MINUTES: METER_NAME_EVERY_FIVE_MINUTES,
    EVERY_TEN_MINUTES: METER_NAME_EVERY_TEN_MINUTES,
    QUARTER_HOURLY: METER_NAME_QUARTER_HOURLY,
    EVERY_TWENTY_MINUTES: METER_NAME_EVERY_TWENTY_MINUTES,
    HALF_HOURLY: METER_NAME_HALF_HOURLY,
    HOURLY: METER_NAME_HOURLY,
    DAILY: METER_NAME_DAILY,
    WEEKLY: METER_NAME_WEEKLY,
    MONTHLY: METER_NAME_MONTHLY,
    BIMONTHLY: METER_NAME_BIMONTHLY,
    QUARTERLY: METER_NAME_QUARTERLY,
    HALF_YEARLY: METER_NAME_HALF_YEARLY,
    YEARLY: METER_NAME_YEARLY,
}
# List of meter types
# This list is used to validate the meter type in the configuration.
# It should match the keys in METER_NAME_TYPES.
# The order of the list is important for the UI display.
METER_TYPES = [
    "none",
    EVERY_FIVE_MINUTES,
    EVERY_TEN_MINUTES,
    QUARTER_HOURLY,
    EVERY_TWENTY_MINUTES,
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
MULTI_METER_TYPES = [
    EVERY_FIVE_MINUTES,
    EVERY_TEN_MINUTES,
    QUARTER_HOURLY,
    EVERY_TWENTY_MINUTES,
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

DATA_UTILITY = "utility_meter_next_gen_data"
DATA_TARIFF_SENSORS = "utility_meter_next_gen_sensors"

COLLECTING = "collecting"
PRECISION = 5
PAUSED = "paused"
SINGLE_TARIFF = "single_tariff"
TOTAL_TARIFF = "total"

CONF_CONFIG_CALIBRATE_APPLY = "calibrate_apply"
CONF_CONFIG_CALIBRATE_CALC_APPLY = "calibrate_calc_apply"
CONF_CONFIG_CALIBRATE_CALC_VALUE = "calibrate_calc_value"
CONF_CONFIG_CALIBRATE_VALUE = "calibrate_value"
CONF_CONFIG_CRON = "cron"
CONF_CONFIG_MULTI = "multi"
CONF_CONFIG_PREDEFINED = "predefined"
CONF_CONFIG_TYPE = "config_type"
CONF_CREATE_CALCULATION_SENSOR = "create_calculation_sensor"
CONF_CREATE_CALCULATION_SENSOR_DEFAULT = False
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
CONF_SENSOR_ALWAYS_AVAILABLE = "always_available"
CONF_SOURCE_CALC_MULTIPLIER = "source_calc_multiplier"
CONF_SOURCE_CALC_SENSOR = "source_calc_sensor"
CONF_SOURCE_SENSOR = "source"
CONF_TARIFFS = "tariffs"
CONF_TARIFF = "tariff"
CONF_TARIFF_ENTITY = "tariff_entity"

CONFIG_TYPES = [
    CONF_CONFIG_CRON,
    CONF_CONFIG_PREDEFINED,
    CONF_CONFIG_MULTI,
]

CONF_METER_TYPES = [
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

#Entity related constants
ATTR_CALC_CURRENT_VALUE = "current_period_calculated_value"
ATTR_CALC_LAST_VALUE = "last_period_calculated_value"
ATTR_CRON_PATTERN = "cron pattern"
ATTR_LAST_PERIOD = "last_period"
ATTR_LAST_VALID_STATE = "last_valid_state"
ATTR_LINKED_METER = "linked_utility_meter"
ATTR_NEXT_RESET = "next_reset"
ATTR_PERIOD = "meter_period"
ATTR_PREDEFINED_CYCLE = "Predefined Cycle"
ATTR_SOURCE_ID = "source"
ATTR_STATUS = "status"
ATTR_TARIFF = "tariff"
ATTR_TARIFFS = "tariffs"
ATTR_VALUE = "value"

SIGNAL_START_PAUSE_METER = "utility_meter_next_gen_start_pause"
SIGNAL_RESET_METER = "utility_meter_next_gen_reset"

#Action related constants
SERVICE_RESET = "reset"
SERVICE_CALIBRATE_METER = "calibrate"

DEVICE_CLASSES_METER = [
    "data_size",
    "distance",
    "duration",
    "energy",
    "energy_storage",
    "gas",
    "precipitation",
    "reactive_energy",
    "volume",
    "volume_storage",
    "water",
    "weight"
]

PERIOD2CRON = {
    EVERY_FIVE_MINUTES: "{minute}/5 * * * *",
    EVERY_TEN_MINUTES: "{minute}/10 * * * *",
    QUARTER_HOURLY: "{minute}/15 * * * *",
    EVERY_TWENTY_MINUTES: "{minute}/20 * * * *",
    HALF_HOURLY: "{minute}/30 * * * *",
    HOURLY: "{minute} * * * *",
    DAILY: "{minute} {hour} * * *",
    WEEKLY: "{minute} {hour} * * {day}",
    MONTHLY: "{minute} {hour} 1 * *",
    BIMONTHLY: "{minute} {hour} 1 */2 *",
    QUARTERLY: "{minute} {hour} 1 */3 *",
    HALF_YEARLY: "{minute} {hour} 1 */6 *",
    YEARLY: "{minute} {hour} 1 1 *",
}
