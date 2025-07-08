"""Schemas for configuring the Utility Meter Next Gen component."""
import logging

import voluptuous as vol

from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.const import CONF_NAME
from homeassistant.helpers import selector

from .const import (
    CONF_CONFIG_CALIBRATE_APPLY,
    CONF_CONFIG_CALIBRATE_CALC_APPLY,
    CONF_CONFIG_CALIBRATE_CALC_VALUE,
    CONF_CONFIG_CALIBRATE_VALUE,
    CONF_CONFIG_CRON,
    CONF_CONFIG_PREDEFINED,
    CONF_CONFIG_TYPE,
    CONF_CREATE_CALCULATION_SENSOR,
    CONF_CREATE_CALCULATION_SENSOR_DEFAULT,
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
    DEVICE_CLASSES_METER,
    METER_TYPES,
    MULTI_METER_TYPES,
)

_LOGGER = logging.getLogger(__name__)

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
                options=METER_TYPES,
                translation_key=CONF_METER_TYPE
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

BASE_MULTI_CONFIG_SCHEMA_STEP_1 = vol.Schema(
    {
        vol.Required(CONF_METER_TYPE,default=[]): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=MULTI_METER_TYPES,
                translation_key=CONF_METER_TYPE,
                mode=selector.SelectSelectorMode.DROPDOWN,
                custom_value =False,
                multiple=True
            ),
        ),
    }
)

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
            default=True,
        ): selector.BooleanSelector(),
}
def create_calc_extras_schema(data):
    """Create the calibration schema for predefined and cron cycles."""
    calibrate_default = data.get(CONF_CONFIG_CALIBRATE_CALC_VALUE,0)
    multiplier_default = data.get(CONF_SOURCE_CALC_MULTIPLIER, 1)
    create_calc_sensor_default = data.get(CONF_CREATE_CALCULATION_SENSOR,
            CONF_CREATE_CALCULATION_SENSOR_DEFAULT)
    if data[CONF_SOURCE_CALC_SENSOR] is not None:
        return {
            vol.Required(
                CONF_CREATE_CALCULATION_SENSOR,
                default=create_calc_sensor_default):
                    selector.BooleanSelector(
                        selector.BooleanSelectorConfig()
                ),
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

def create_common_multi_config_schema_step_2a(data):
    """Create the common configuration schema for multi configurations."""
    return vol.Schema(
        {
        vol.Optional(
            CONF_CONFIG_CALIBRATE_VALUE,
            default=0
            ): selector.NumberSelector(
            selector.NumberSelectorConfig(
                mode=selector.NumberSelectorMode.BOX,
                step="any",
                    ),
        ),
        vol.Optional(
                CONF_CONFIG_CALIBRATE_APPLY):
                    selector.SelectSelector(
                    selector.SelectSelectorConfig(
                    options=data.get(CONF_METER_TYPE, []),
                    translation_key=CONF_METER_TYPE,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    custom_value =False,
                    multiple=False
                ),
            ),
        }
    )

def create_common_multi_config_schema_step_2b(data):
    """Create the calibration schema for multi cycles."""
    calibrate_default = data.get(CONF_CONFIG_CALIBRATE_CALC_VALUE,0)
    multiplier_default = data.get(CONF_SOURCE_CALC_MULTIPLIER, 1)
    selected_meter_types = data.get(CONF_METER_TYPE, [])
    create_calc_sensor_default = data.get(CONF_CREATE_CALCULATION_SENSOR,
        CONF_CREATE_CALCULATION_SENSOR_DEFAULT)
    if data[CONF_SOURCE_CALC_SENSOR] is not None:
        return {
            vol.Required(
                CONF_CREATE_CALCULATION_SENSOR,
                default=create_calc_sensor_default):
                    selector.BooleanSelector(
                        selector.BooleanSelectorConfig()
                ),
            vol.Required(
                CONF_SOURCE_CALC_MULTIPLIER, default=multiplier_default
                ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    mode=selector.NumberSelectorMode.BOX,
                    step="any",
                    ),
                ),
            vol.Required(
                CONF_CONFIG_CALIBRATE_CALC_VALUE,
                default=calibrate_default): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    mode=selector.NumberSelectorMode.BOX,
                    step="any",
                        ),
                ),
            vol.Optional(
                CONF_CONFIG_CALIBRATE_CALC_APPLY):
                    selector.SelectSelector(
                    selector.SelectSelectorConfig(
                    options=selected_meter_types,
                    translation_key=CONF_METER_TYPE,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    custom_value =False,
                    multiple=False
                    ),
                ),
            }
    return {}

def create_common_multi_config_schema_step_2c():
    """Create the common configuration schema for multi configurations."""
    return {
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
            default=True,
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

def create_multi_config_schema_step_1(data):
    """Create the configuration schema for predefined cycles."""

    return vol.Schema(
        {
            **BASE_MULTI_CONFIG_SCHEMA_STEP_1.schema,
        }
    )

def create_multi_config_schema_step_2(data):
    """Create the configuration schema for predefined cycles."""

    return vol.Schema(
        {
            **(create_common_multi_config_schema_step_2a(data)).schema,
            **create_common_multi_config_schema_step_2b(data),
            **create_common_multi_config_schema_step_2c()
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
    option_schema = {
        vol.Required(
            CONF_CREATE_CALCULATION_SENSOR,
            default=data[CONF_CREATE_CALCULATION_SENSOR],):
                selector.BooleanSelector(
                    selector.BooleanSelectorConfig()
            ),
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
            default=data.get(CONF_CONFIG_CALIBRATE_CALC_VALUE,0)): selector.NumberSelector(
            selector.NumberSelectorConfig(
                mode=selector.NumberSelectorMode.BOX,
                step="any",
                    ),
        ),
    }
    if data[CONF_TARIFFS] != [] and data[CONF_TARIFFS] is not None:
        _LOGGER.debug("Schema Current Tariffs: %s", data[CONF_TARIFFS] )
        option_schema[
            vol.Required(CONF_TARIFFS, default=data[CONF_TARIFFS])
        ] = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[], custom_value=True, multiple=True
            ),
        )
    else:
        _LOGGER.debug("Schema Current Tariffs: %s", data[CONF_TARIFFS] )
        option_schema[
            vol.Optional(CONF_TARIFFS)
        ] = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[], custom_value=False, multiple=False
            ),
        )
    option_schema |= {
        vol.Required(
            CONF_METER_NET_CONSUMPTION,
            default=data[CONF_METER_NET_CONSUMPTION],
        ): selector.BooleanSelector(),
        vol.Required(
            CONF_METER_DELTA_VALUES, default=data[CONF_METER_DELTA_VALUES]
        ): selector.BooleanSelector(),
        vol.Required(
            CONF_METER_PERIODICALLY_RESETTING,
            default=data[
                CONF_METER_PERIODICALLY_RESETTING
            ],  # Assuming this is the correct key
        ): selector.BooleanSelector(),
        vol.Optional(
            CONF_SENSOR_ALWAYS_AVAILABLE,
            default=data[CONF_SENSOR_ALWAYS_AVAILABLE],
        ): selector.BooleanSelector(),
    }
    return option_schema

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
            **create_common_option_schema(data)
        }
    )

def create_multi_option_schema_step_1(data):
    """Create the options step 1 schema for multi configurations."""
    if data[CONF_SOURCE_CALC_SENSOR] is None:
        multi_option_step_1 = vol.Schema(
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
                    CONF_CREATE_CALCULATION_SENSOR,
                    default=data[CONF_CREATE_CALCULATION_SENSOR]):
                        selector.BooleanSelector(
                            selector.BooleanSelectorConfig()
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
        multi_option_step_1 = vol.Schema(
            {
                vol.Required(CONF_SOURCE_SENSOR,
                    default=data[CONF_SOURCE_SENSOR]): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain=SENSOR_DOMAIN, filter={"device_class": DEVICE_CLASSES_METER}),
                ),
                vol.Optional(CONF_SOURCE_CALC_SENSOR,
                    default=data[CONF_SOURCE_CALC_SENSOR] ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=SENSOR_DOMAIN),
                ),
                vol.Required(
                    CONF_CREATE_CALCULATION_SENSOR,
                    default=data[CONF_CREATE_CALCULATION_SENSOR]):
                        selector.BooleanSelector(
                            selector.BooleanSelectorConfig()
                ),
                vol.Required(
                    CONF_REMOVE_CALC_SENSOR,
                    default=False,
                ): selector.BooleanSelector(),
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
    meter_types ={
        vol.Required(CONF_METER_TYPE,default=data[CONF_METER_TYPE]): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=METER_TYPES,
                translation_key=CONF_METER_TYPE,
                mode=selector.SelectSelectorMode.DROPDOWN,
                custom_value =False,
                multiple=True
            ),
        ),
    }
    if data[CONF_TARIFFS] != [] and data[CONF_TARIFFS] is not None:
        _LOGGER.debug("Schema Current Tariffs: %s", data[CONF_TARIFFS] )
        multi_option_step_tariffs = {
            vol.Optional(CONF_TARIFFS, default=data[CONF_TARIFFS]):
            selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[], custom_value=True, multiple=True
            ),
            )
        }
    else:
        _LOGGER.debug("Schema Current Tariffs: %s", data[CONF_TARIFFS] )
        multi_option_step_tariffs = {}

    return vol.Schema(
        {**multi_option_step_1.schema,
            **meter_types,
            **multi_option_step_tariffs,
        }
    )

def create_multi_option_schema_step_2(data):
    """Create the options step 2 schema for multi configurations."""
    multi_option_step_2 = vol.Schema(
        {
        vol.Optional(
            CONF_CONFIG_CALIBRATE_VALUE,
            default=data[CONF_CONFIG_CALIBRATE_VALUE]): selector.NumberSelector(
            selector.NumberSelectorConfig(
                mode=selector.NumberSelectorMode.BOX,
                step="any",
                    ),
        ),
        vol.Required(
                CONF_CONFIG_CALIBRATE_APPLY,
                default=data[CONF_CONFIG_CALIBRATE_APPLY]):
                    selector.SelectSelector(
                    selector.SelectSelectorConfig(
                    options=data.get(CONF_METER_TYPE, []),
                    translation_key=CONF_METER_TYPE,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    custom_value =False,
                    multiple=False
                ),
            ),
        }
    )
    if data[CONF_SOURCE_CALC_SENSOR] is not None:
        multi_option_calc = {
            vol.Required(
                CONF_SOURCE_CALC_MULTIPLIER, data[CONF_SOURCE_CALC_MULTIPLIER]
                ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    mode=selector.NumberSelectorMode.BOX,
                    step="any",
                    ),
                ),
            vol.Optional(
                CONF_CONFIG_CALIBRATE_CALC_VALUE,
                default=data.get(CONF_CONFIG_CALIBRATE_CALC_VALUE,0)): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    mode=selector.NumberSelectorMode.BOX,
                    step="any",
                    ),
                ),
            vol.Required(
                CONF_CONFIG_CALIBRATE_CALC_APPLY,
                    default=data.get(CONF_CONFIG_CALIBRATE_CALC_APPLY, [])):
                    selector.SelectSelector(
                    selector.SelectSelectorConfig(
                    options=data.get(CONF_METER_TYPE, []),
                    translation_key=CONF_METER_TYPE,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    custom_value =False,
                    multiple=False
                    ),
                ),
            }
    else:
        multi_option_calc = {}

    multi_option_common = {
        vol.Required(
            CONF_METER_NET_CONSUMPTION,
            default=data[CONF_METER_NET_CONSUMPTION],
        ): selector.BooleanSelector(),
        vol.Required(
            CONF_METER_DELTA_VALUES, default=data[CONF_METER_DELTA_VALUES]
        ): selector.BooleanSelector(),
        vol.Required(
            CONF_METER_PERIODICALLY_RESETTING,
            default=data[
                CONF_METER_PERIODICALLY_RESETTING
            ],  # Assuming this is the correct key
        ): selector.BooleanSelector(),
        vol.Optional(
            CONF_SENSOR_ALWAYS_AVAILABLE,
            default=data[CONF_SENSOR_ALWAYS_AVAILABLE],
        ): selector.BooleanSelector(),
    }
    return vol.Schema(
        {**create_multi_option_schema_step_1(data).schema,
         **multi_option_step_2.schema,
            **multi_option_calc,
            **multi_option_common,
        }
    )
