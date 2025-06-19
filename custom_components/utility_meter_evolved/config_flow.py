"""Config flow for Utility Meter integration."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Dict, Optional, cast

import voluptuous as vol
from cronsim import CronSim, CronSimError
from datetime import datetime
from decimal import Decimal, DecimalException, InvalidOperation

from homeassistant import config_entries
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.const import (
    CONF_NAME,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN
)
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.entity_registry import (
    async_entries_for_config_entry,
)
from homeassistant.helpers.schema_config_entry_flow import (
    SchemaCommonFlowHandler,
    SchemaConfigFlowHandler,
    SchemaFlowError,
    SchemaFlowFormStep,
)

from .const import (
    BIMONTHLY,
    CONFIG_TYPES,
    CONF_CONFIG_CRON,
    CONF_CONFIG_PREDEFINED,
    CONF_CONFIG_TYPE,
    CONF_METER_DELTA_VALUES,
    CONF_METER_NET_CONSUMPTION,
    CONF_METER_OFFSET,
    CONF_METER_PERIODICALLY_RESETTING,
    CONF_METER_TYPE,
    CONF_REMOVE_CALC_SENSOR,
    CONF_SENSOR_ALWAYS_AVAILABLE,
    CONF_SOURCE_CALC_SENSOR,
    CONF_SOURCE_SENSOR,
    CONF_TARIFFS,
    DAILY,
    DOMAIN,
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


async def _validate_config(
    handler: SchemaCommonFlowHandler, user_input: dict[str, Any]
) -> dict[str, Any]:
    """Validate config."""
    try:
        vol.Unique()(user_input[CONF_TARIFFS])
    except CronSimError as exc:
        raise SchemaFlowError("tariffs_not_unique") from exc

    return user_input



OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_SOURCE_SENSOR): selector.EntitySelector(
            selector.EntitySelectorConfig(domain=SENSOR_DOMAIN),
        ),
        vol.Optional(CONF_SOURCE_CALC_SENSOR): selector.EntitySelector(
            selector.EntitySelectorConfig(domain=SENSOR_DOMAIN),
        ),
        vol.Required(
            CONF_METER_PERIODICALLY_RESETTING,
        ): selector.BooleanSelector(),
        vol.Optional(
            CONF_SENSOR_ALWAYS_AVAILABLE,
            default=False,
        ): selector.BooleanSelector(),
    }
)

OPTIONS_SCHEMA_CRON = vol.Schema(
    {
        vol.Required(CONF_SOURCE_SENSOR): selector.EntitySelector(
            selector.EntitySelectorConfig(domain=SENSOR_DOMAIN),
        ),
        vol.Optional(CONF_SOURCE_CALC_SENSOR): selector.EntitySelector(
            selector.EntitySelectorConfig(domain=SENSOR_DOMAIN),
        ),
        vol.Required(CONF_CONFIG_CRON): selector.TextSelector(),
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
)

def create_option_schema_cron(data):
    """Create the options schema for cron cycles."""

    if data[CONF_SOURCE_CALC_SENSOR] is None:
        cron_option_schema_1 = vol.Schema(
            {
                vol.Required(CONF_SOURCE_SENSOR,
                    default=data[CONF_SOURCE_SENSOR]): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=SENSOR_DOMAIN),
                ),
                vol.Optional(CONF_SOURCE_CALC_SENSOR ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=SENSOR_DOMAIN),
                ),
            }
        )
    else:
        cron_option_schema_1 = vol.Schema(
            {
                vol.Required(CONF_SOURCE_SENSOR,
                    default=data[CONF_SOURCE_SENSOR]): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=SENSOR_DOMAIN),
                ),
                vol.Optional(
                    CONF_REMOVE_CALC_SENSOR,
                    default=False,
                ): selector.BooleanSelector(),
                vol.Optional(CONF_SOURCE_CALC_SENSOR,
                    default=data[CONF_SOURCE_CALC_SENSOR] ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=SENSOR_DOMAIN),
                ),
            }
        )
    cron_option_schema_2 = {
        vol.Required(CONF_CONFIG_CRON, default=data[CONF_CONFIG_CRON]): selector.TextSelector(),
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

    return vol.Schema({**cron_option_schema_1.schema, **cron_option_schema_2})


def create_option_schema_predefined(data):
    """Create the options schema for predefined cycles."""

    if data[CONF_SOURCE_CALC_SENSOR] is None:
        predefined_option_schema_1 = vol.Schema(
            {
                vol.Required(CONF_SOURCE_SENSOR,
                    default=data[CONF_SOURCE_SENSOR]): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=SENSOR_DOMAIN),
                ),
                vol.Optional(CONF_SOURCE_CALC_SENSOR ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=SENSOR_DOMAIN),
                ),
            }
        )
    else:
        predefined_option_schema_1 = vol.Schema(
            {
                vol.Required(CONF_SOURCE_SENSOR,
                    default=data[CONF_SOURCE_SENSOR]): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=SENSOR_DOMAIN),
                ),
                vol.Optional(
                    CONF_REMOVE_CALC_SENSOR,
                    default=False,
                ): selector.BooleanSelector(),
                vol.Optional(CONF_SOURCE_CALC_SENSOR,
                    default=data[CONF_SOURCE_CALC_SENSOR] ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=SENSOR_DOMAIN),
                ),
            }
        )
    predefined_option_schema_2 = {
        vol.Required(CONF_METER_TYPE, default=data[CONF_METER_TYPE]): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=METER_TYPES, translation_key=CONF_METER_TYPE
            ),
        ),
        vol.Required(CONF_METER_OFFSET, default=data[CONF_METER_OFFSET]): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0,
                max=28,
                mode=selector.NumberSelectorMode.BOX,
                unit_of_measurement="days",
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
    return vol.Schema({**predefined_option_schema_1.schema, **predefined_option_schema_2})

BASE_CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): selector.TextSelector(),
        vol.Required(CONF_SOURCE_SENSOR): selector.EntitySelector(
            selector.EntitySelectorConfig(domain=SENSOR_DOMAIN),
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

PREDEFINED_CYCLES_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_METER_TYPE): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=METER_TYPES, translation_key=CONF_METER_TYPE
            ),
        ),
        vol.Required(CONF_METER_OFFSET, default=0): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0,
                max=28,
                mode=selector.NumberSelectorMode.BOX,
                unit_of_measurement="days",
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
)

CRON_CYCLES_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CONFIG_CRON): selector.TextSelector(),
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
)

async def validate():
    """Validate the configuration."""
    # This function can be extended to include any validation logic needed.
    return True

class UtilityMeterEvolvedCustomConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Github Custom config flow."""

    data: Optional[Dict[str, Any]]

    @staticmethod
    def _validate_state(state: State | None) -> Decimal | None:
        """Parse the state as a Decimal if available. Throws DecimalException if the state is not a number."""
        try:
            return (
                None
                if state is None or state.state in [STATE_UNAVAILABLE, STATE_UNKNOWN]
                else Decimal(state.state)
            )
        except DecimalException:
            return None
    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None):
        """Invoked when a user initiates a flow via the user interface."""

        errors: Dict[str, str] = {}
        if user_input is not None:
            try:
                source_state = self.hass.states.get(user_input[CONF_SOURCE_SENSOR])
                if source_state is None:
                    errors["base"] = "source_sensor_not_found"
                elif source_state.state in [STATE_UNAVAILABLE, STATE_UNKNOWN]:
                    errors["base"] = "source_sensor_unavailable"
                else:
                    # Validate the state as a Decimal.
                    _ = self._validate_state(source_state)
            except DecimalException:
                errors["base"] = "source_sensor_not_a_number"
            try:
                if CONF_SOURCE_CALC_SENSOR in user_input:
                    source_state = self.hass.states.get(user_input[CONF_SOURCE_CALC_SENSOR])
                    if source_state is None:
                        errors["base"] = "source_calc_sensor_not_found"
                    elif source_state.state in [STATE_UNAVAILABLE, STATE_UNKNOWN]:
                        errors["base"] = "source_calc_sensor_unavailable"
                    else:
                        # Validate the state as a Decimal.
                        _ = self._validate_state(source_state)
                else:
                    user_input[CONF_SOURCE_CALC_SENSOR] = None
            except DecimalException:
                errors["base"] = "source_calc_sensor_not_a_number"

            if not errors:
                # Input is valid, set data.
                self.data = user_input
                self.data["meters"] = []
                # Return the form of the next step.
                if user_input.get(CONF_CONFIG_TYPE) == CONF_CONFIG_CRON:
                    return await self.async_step_cron()
                elif user_input.get(CONF_CONFIG_TYPE) == CONF_CONFIG_PREDEFINED:
                    return await self.async_step_predefined()
                #return await self.async_step_repo()

        return self.async_show_form(
            step_id="user", data_schema=BASE_CONFIG_SCHEMA, errors=errors
        )

    async def async_step_cron(self, user_input: Optional[Dict[str, Any]] = None):
        """Second step in config flow to add a repo to watch."""
        errors: Dict[str, str] = {}
        if user_input is not None:
            # Validate the path.
            try:
                CronSim(user_input[CONF_CONFIG_CRON], datetime(2020, 1, 1))
            except CronSimError:
                errors["base"] = "invalid_cron"

            if not errors:
                # Input is valid, set data.
                self.data.update(user_input)
                self.data[CONF_METER_OFFSET] =0
                self.data[CONF_METER_TYPE] = None
                #if self.data[CONF_TARIFFS] != []:
                #    self.data[CONF_TARIFFS].append("total")
                # If user ticked the box show this form again so they can add an
                # additional repo.
                return self.async_create_entry(title=self.data["name"], data={}, options=self.data)

        return self.async_show_form(
            step_id="cron", data_schema=CRON_CYCLES_SCHEMA, errors=errors
        )

    async def async_step_predefined(self, user_input: Optional[Dict[str, Any]] = None):
        """Second step in config flow to add a repo to watch."""
        errors: Dict[str, str] = {}
        if user_input is not None:
            # Validate the path.
            try:
                await validate()

            except ValueError:
                errors["base"] = "invalid_path"

            if not errors:
                # Input is valid, set data.
                self.data.update(user_input)
                self.data[CONF_CONFIG_CRON] = None
                #if self.data[CONF_TARIFFS] != []:
                #    self.data[CONF_TARIFFS].append("total")
                # If user ticked the box show this form again so they can add an
                # additional repo.
                return self.async_create_entry(title=self.data["name"], data={}, options=self.data)

        return self.async_show_form(
            step_id="predefined", data_schema=PREDEFINED_CYCLES_SCHEMA, errors=errors
        )
    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handles options flow for the component."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry
        self.options_schema =OPTIONS_SCHEMA

        if config_entry.options["config_type"] == CONF_CONFIG_CRON:
            self.options_schema = create_option_schema_cron(config_entry.options)
        else:
            self.options_schema = create_option_schema_predefined(config_entry.options)

    @staticmethod
    def _validate_state(state: State | None) -> Decimal | None:
        """Parse the state as a Decimal if available. Throws DecimalException if the state is not a number."""
        try:
            return (
                None
                if state is None or state.state in [STATE_UNAVAILABLE, STATE_UNKNOWN]
                else Decimal(state.state)
            )
        except DecimalException:
            return None

    async def async_step_init(
        self, user_input = None
    ):
        """Manage the options for the custom component."""
        errors: Dict[str, str] = {}
        if user_input is not None:
            # Get the current repos from the config entry.
            if CONF_REMOVE_CALC_SENSOR in user_input:
                if user_input[CONF_REMOVE_CALC_SENSOR]:
                    # Remove the calc sensor from the options.
                    user_input[CONF_SOURCE_CALC_SENSOR] = None

            try:
                if CONF_SOURCE_CALC_SENSOR in user_input:
                    if user_input[CONF_SOURCE_CALC_SENSOR] is not None:
                        source_state = self.hass.states.get(user_input[CONF_SOURCE_CALC_SENSOR])
                        if source_state is None:
                            errors["base"] = "source_calc_sensor_not_found"
                        elif source_state.state in [STATE_UNAVAILABLE, STATE_UNKNOWN]:
                            errors["base"] = "source_calc_sensor_unavailable"
                        else:
                            # Validate the state as a Decimal.
                            _ = self._validate_state(source_state)
                else:
                   user_input[CONF_SOURCE_CALC_SENSOR] = None
            except DecimalException:
                errors["base"] = "source_calc_sensor_not_a_number"
            if self.config_entry.options["config_type"] == CONF_CONFIG_CRON:
                user_input[CONF_METER_OFFSET] =0
                user_input[CONF_METER_TYPE] = None
                user_input[CONF_CONFIG_TYPE] = CONF_CONFIG_CRON
            else:
                user_input[CONF_CONFIG_CRON] = None
                user_input[CONF_CONFIG_TYPE] = CONF_CONFIG_PREDEFINED

            return self.async_create_entry(title=self.config_entry.title, data=user_input)
        #options_schema = OPTIONS_SCHEMA
        return self.async_show_form(
            step_id="init", data_schema=self.options_schema, errors=errors
        )
