"""Schemas for configuring the Utility Meter Next Gen component."""
import voluptuous as vol

from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.const import CONF_NAME
from homeassistant.helpers import selector

from .const import (
    BIMONTHLY,
    CONF_CONFIG_CALIBRATE_CALC_VALUE,
    CONF_CONFIG_CALIBRATE_VALUE,
    CONF_CONFIG_CRON,
    CONF_CONFIG_PREDEFINED,
    CONF_CONFIG_TYPE,
    CONF_METER_DELTA_VALUES,
    CONF_METER_NET_CONSUMPTION,
    CONF_METER_OFFSET,
    CONF_METER_OFFSET_DURATION_DEFAULT,
    CONF_METER_PERIODICALLY_RESETTING,
    CONF_METER_TYPE,
    CONF_REMOVE_CALC_SENSOR,
    CONF_SENSOR_ALWAYS_AVAILABLE,
    CONF_SOURCE_CALC_MULTIPLIER,
    CONF_SOURCE_CALC_SENSOR,
    CONF_SOURCE_SENSOR,
    CONF_TARIFFS,
    CONFIG_TYPES,
    DAILY,
    DEVICE_CLASSES_METER,
    EVERY_FIVE_MINUTES,
    HALF_HOURLY,
    HALF_YEARLY,
    HOURLY,
    MONTHLY,
    QUARTER_HOURLY,
    QUARTERLY,
    WEEKLY,
    YEARLY,
)

METER_TYPES = [
    "none",
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


BASE_CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): selector.TextSelector(),
        vol.Required(CONF_SOURCE_SENSOR): selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain=SENSOR_DOMAIN, filter={"device_class": DEVICE_CLASSES_METER}),
        ),
        vol.Optional(CONF_SOURCE_CALC_SENSOR): selector.EntitySelector(
            selector.EntitySelectorConfig(domain=SENSOR_DOMAIN),
        ),
        vol.Required(CONF_CONFIG_TYPE, default=[CONF_CONFIG_PREDEFINED]): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=CONFIG_TYPES,
                translation_key=CONF_CONFIG_TYPE,
                mode=selector.SelectSelectorMode.LIST,
                custom_value =False,
                multiple=False
            ),
        ),
    }
)

BASE_PREDEFINED_CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_METER_TYPE): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=METER_TYPES, translation_key=CONF_METER_TYPE
            ),
        ),
        vol.Optional(CONF_METER_OFFSET,
            default=CONF_METER_OFFSET_DURATION_DEFAULT): selector.DurationSelector(
            selector.DurationSelectorConfig(
                enable_day=True,
            ),
        ),
    }
)

BASE_CRON_CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CONFIG_CRON): selector.TextSelector(),
    }
)

def create_calc_extras_schema(data):
    """Create the calibration schema for predefined and cron cycles."""
    calibrate_default = data.get(CONF_CONFIG_CALIBRATE_CALC_VALUE,0)
    multiplier_default = data.get(CONF_SOURCE_CALC_MULTIPLIER, 1)
    if data[CONF_SOURCE_CALC_SENSOR] is not None:
        return {
            vol.Required(
                CONF_SOURCE_CALC_MULTIPLIER, default=multiplier_default
                ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    mode=selector.NumberSelectorMode.BOX,
                    step="any",
                    ),
                ),
            vol.Optional(
                CONF_CONFIG_CALIBRATE_CALC_VALUE,
                default=calibrate_default): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    mode=selector.NumberSelectorMode.BOX,
                    step="any",
                        ),
                ),
            }
    return {}



BASE_COMMON_CONFIG_SCHEMA = {
        vol.Optional(
            CONF_CONFIG_CALIBRATE_VALUE,
            default=0
            ): selector.NumberSelector(
            selector.NumberSelectorConfig(
                mode=selector.NumberSelectorMode.BOX,
                step="any",
                    ),
        ),
        vol.Required(CONF_TARIFFS, default=[]): selector.SelectSelector(
            selector.SelectSelectorConfig(options=[], custom_value=True, multiple=True),
        ),
        vol.Required(
            CONF_METER_NET_CONSUMPTION, default=False
        ): selector.BooleanSelector(),
        vol.Required(
            CONF_METER_DELTA_VALUES, default=False
        ): selector.BooleanSelector(),
        vol.Required(
            CONF_METER_PERIODICALLY_RESETTING,
            default=True,
        ): selector.BooleanSelector(),
        vol.Optional(
            CONF_SENSOR_ALWAYS_AVAILABLE,
            default=False,
        ): selector.BooleanSelector(),
}

def create_predefined_config_schema(data):
    """Create the configuration schema for predefined cycles."""

    return vol.Schema(
        {
            **BASE_PREDEFINED_CONFIG_SCHEMA.schema,
            **(create_calc_extras_schema(data) or {}),
            **BASE_COMMON_CONFIG_SCHEMA
        }
    )

def create_cron_config_schema(data):
    """Create the configuration schema for predefined cycles."""

    return vol.Schema(
        {
            **BASE_CRON_CONFIG_SCHEMA.schema,
            **(create_calc_extras_schema(data) or {}),
            **BASE_COMMON_CONFIG_SCHEMA
        }
    )


def create_base_predefined_option_schema(data):
    """Create the base options schema for predefined cycles."""

    return {
        vol.Required(CONF_METER_TYPE, default=data[CONF_METER_TYPE]): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=METER_TYPES, translation_key=CONF_METER_TYPE
            ),
        ),
        vol.Optional(CONF_METER_OFFSET,
            default=data[CONF_METER_OFFSET]): selector.DurationSelector(
            selector.DurationSelectorConfig(
                enable_day=True,
            ),
        ),
    }

def create_base_cron_option_schema(data):
    """Create the base options schema for cron cycles."""

    return {
        vol.Required(CONF_CONFIG_CRON, default=data[CONF_CONFIG_CRON]): selector.TextSelector(),
    }

def create_common_option_schema(data):
    """Create the common options schema for all configurations."""

    return {
        vol.Optional(
            CONF_CONFIG_CALIBRATE_VALUE,
            default=data[CONF_CONFIG_CALIBRATE_VALUE]): selector.NumberSelector(
            selector.NumberSelectorConfig(
                mode=selector.NumberSelectorMode.BOX,
                step="any",
                    ),
        ),
        vol.Optional(
            CONF_CONFIG_CALIBRATE_CALC_VALUE,
            default=data[CONF_CONFIG_CALIBRATE_CALC_VALUE]): selector.NumberSelector(
            selector.NumberSelectorConfig(
                mode=selector.NumberSelectorMode.BOX,
                step="any",
                    ),
        ),
        vol.Required(CONF_TARIFFS, default=data[CONF_TARIFFS]): selector.SelectSelector(
            selector.SelectSelectorConfig(options=[], custom_value=True, multiple=True),
        ),
        vol.Required(
            CONF_METER_NET_CONSUMPTION, default=data[CONF_METER_NET_CONSUMPTION]
        ): selector.BooleanSelector(),
        vol.Required(
            CONF_METER_DELTA_VALUES, default=data[CONF_METER_DELTA_VALUES]
        ): selector.BooleanSelector(),
        vol.Required(
            CONF_METER_PERIODICALLY_RESETTING,
            default=data[CONF_METER_PERIODICALLY_RESETTING],  # Assuming this is the correct key
        ): selector.BooleanSelector(),
        vol.Optional(
            CONF_SENSOR_ALWAYS_AVAILABLE,
            default=data[CONF_SENSOR_ALWAYS_AVAILABLE],
        ): selector.BooleanSelector(),
    }


def create_predefined_option_schema(data):
    """Create the options schema for predefined cycles."""

    if data[CONF_SOURCE_CALC_SENSOR] is None:
        predefined_begin = vol.Schema(
            {
                vol.Required(CONF_SOURCE_SENSOR,
                    default=data[CONF_SOURCE_SENSOR]): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain=SENSOR_DOMAIN, filter={"device_class": DEVICE_CLASSES_METER}),
                ),
                vol.Optional(CONF_SOURCE_CALC_SENSOR ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=SENSOR_DOMAIN),
                ),
                vol.Required(
                    CONF_SOURCE_CALC_MULTIPLIER, default=1
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        mode=selector.NumberSelectorMode.BOX,
                        step="any",
                        ),
                ),
            }
        )
    else:
        predefined_begin = vol.Schema(
            {
                vol.Required(CONF_SOURCE_SENSOR,
                    default=data[CONF_SOURCE_SENSOR]): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain=SENSOR_DOMAIN, filter={"device_class": DEVICE_CLASSES_METER}),
                ),
                vol.Optional(
                    CONF_REMOVE_CALC_SENSOR,
                    default=False,
                ): selector.BooleanSelector(),
                vol.Optional(CONF_SOURCE_CALC_SENSOR,
                    default=data[CONF_SOURCE_CALC_SENSOR] ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=SENSOR_DOMAIN),
                ),
                vol.Required(
                    CONF_SOURCE_CALC_MULTIPLIER, default=data[CONF_SOURCE_CALC_MULTIPLIER]
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        mode=selector.NumberSelectorMode.BOX,
                        step="any",
                        ),
                ),

            }
        )
    return vol.Schema(
        {**predefined_begin.schema,
            **create_base_predefined_option_schema(data),
            #**(create_calc_extras_schema(data) or {}),
            **create_common_option_schema(data)
        }
    )

def create_cron_option_schema(data):
    """Create the options schema for cron cycles."""

    if data[CONF_SOURCE_CALC_SENSOR] is None:
        cron_begin = vol.Schema(
            {
                vol.Required(CONF_SOURCE_SENSOR,
                    default=data[CONF_SOURCE_SENSOR]): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain=SENSOR_DOMAIN, filter={"device_class": DEVICE_CLASSES_METER}),
                ),
                vol.Optional(CONF_SOURCE_CALC_SENSOR ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=SENSOR_DOMAIN),
                ),
                vol.Required(
                    CONF_SOURCE_CALC_MULTIPLIER, default=1
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        mode=selector.NumberSelectorMode.BOX,
                        step="any",
                        ),
                ),

            }
        )
    else:
        cron_begin = vol.Schema(
            {
                vol.Required(CONF_SOURCE_SENSOR,
                    default=data[CONF_SOURCE_SENSOR]): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain=SENSOR_DOMAIN, filter={"device_class": DEVICE_CLASSES_METER}),
                ),
                vol.Optional(
                    CONF_REMOVE_CALC_SENSOR,
                    default=False,
                ): selector.BooleanSelector(),
                vol.Optional(CONF_SOURCE_CALC_SENSOR,
                    default=data[CONF_SOURCE_CALC_SENSOR] ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=SENSOR_DOMAIN),
                ),
                vol.Required(
                    CONF_SOURCE_CALC_MULTIPLIER, default=data[CONF_SOURCE_CALC_MULTIPLIER]
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        mode=selector.NumberSelectorMode.BOX,
                        step="any",
                        ),
                ),
            }
        )
    return vol.Schema(
        {**cron_begin.schema,
            **create_base_cron_option_schema(data),
            #**(create_calc_extras_schema(data) or {}),
            **create_common_option_schema(data)
        }
    )
