"""Config flow for Utility Meter Next Gen integration."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, DecimalException
from typing import Any, Optional

from cronsim import CronSim, CronSimError

from homeassistant import config_entries
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import callback

#from homeassistant.helpers.schema_config_entry_flow import (
#    SchemaCommonFlowHandler,
#    SchemaFlowError,
#)
from .const import (
    BIMONTHLY,
    CONF_CONFIG_CALIBRATE_CALC_VALUE,
    CONF_CONFIG_CALIBRATE_VALUE,
    CONF_CONFIG_CRON,
    CONF_CONFIG_PREDEFINED,
    CONF_CONFIG_TYPE,
    CONF_METER_OFFSET,
    CONF_METER_OFFSET_DURATION_DEFAULT,
    CONF_METER_TYPE,
    CONF_REMOVE_CALC_SENSOR,
    CONF_SOURCE_CALC_MULTIPLIER,
    CONF_SOURCE_CALC_SENSOR,
    CONF_SOURCE_SENSOR,
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
from .schemas import (
    BASE_CONFIG_SCHEMA,
    #CRON_CONFIG_SCHEMA,
    #PREDEFINED_CONFIG_SCHEMA,
    create_cron_config_schema,
    create_cron_option_schema,
    create_predefined_config_schema,
    create_predefined_option_schema,
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

async def validate():
    """Validate the configuration."""
    # This function can be extended to include any validation logic needed.
    return True

class UtilityMeterEvolvedCustomConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Github Custom config flow."""

    VERSION = 5

    data: Optional[dict[str, Any]]  # noqa: UP045

    @staticmethod
    def _validate_state(state: State | None) -> Decimal | None: # noqa: F821
        """Parse the state as a Decimal if available."""

        #Throws DecimalException if the state is not a number.

        try:
            return (
                None
                if state is None or state.state in [STATE_UNAVAILABLE, STATE_UNKNOWN]
                else Decimal(state.state)
            )
        except DecimalException:
            return None
    async def async_step_user(self, user_input: Optional[dict[str, Any]] = None):  # noqa: UP045
        """Initiate a flow when a user starts via the user interface."""

        errors: dict[str, str] = {}
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
                elif user_input.get(CONF_CONFIG_TYPE) == CONF_CONFIG_PREDEFINED:  # noqa: RET505
                    return await self.async_step_predefined()
                #return await self.async_step_repo()

        return self.async_show_form(
            step_id="user", data_schema=BASE_CONFIG_SCHEMA, errors=errors
        )

    async def async_step_cron(self, user_input: Optional[dict[str, Any]] = None):  # noqa: UP045
        """Second step in config flow to add a repo to watch."""
        errors: dict[str, str] = {}
        self.data = self.data or {}
        if user_input is not None:
            # Validate the path.
            try:
                CronSim(user_input[CONF_CONFIG_CRON], datetime(2020, 1, 1))
            except CronSimError:
                errors["base"] = "invalid_cron"

            if not errors:
                # Input is valid, set data.
                self.data[CONF_CONFIG_CALIBRATE_CALC_VALUE] = 0
                self.data[CONF_CONFIG_CALIBRATE_VALUE] = 0
                self.data[CONF_SOURCE_CALC_MULTIPLIER] = 1
                self.data.update(user_input) # noqa: PGH003 # type: ignore
                self.data[CONF_METER_OFFSET] =(       # noqa: PGH003  # type: ignore
                    CONF_METER_OFFSET_DURATION_DEFAULT)
                self.data[CONF_METER_TYPE] = None   # noqa: PGH003# type: ignore
                return self.async_create_entry(
                    title=self.data["name"],  # noqa: PGH003 # type: ignore
                    data={},
                    options=self.data)   # noqa: PGH003 # type: ignore

        return self.async_show_form(
            step_id="cron", data_schema=create_cron_config_schema(self.data), errors=errors
        )

    async def async_step_predefined(self, user_input:
            Optional[dict[str, Any]] = None):  # noqa: UP045
        """Second step in config flow to add a repo to watch."""
        errors: dict[str, str] = {}
        self.data = self.data or {}  # Initialize data if not set
        if user_input is not None:
            # Validate the path.
            try:
                await validate()

            except ValueError:
                errors["base"] = "invalid_path"

            if not errors:
                # Input is valid, set data.
                self.data[CONF_CONFIG_CALIBRATE_CALC_VALUE] = 0
                self.data[CONF_CONFIG_CALIBRATE_VALUE] = 0
                self.data[CONF_SOURCE_CALC_MULTIPLIER] = 1
                self.data.update(user_input)  # noqa: PGH003 # type: ignore
                self.data[CONF_CONFIG_CRON] = None  # noqa: PGH003 # type: ignore
                return self.async_create_entry(title=self.data["name"],    # noqa: PGH003 # type: ignore
                            data={}, options=self.data)

        return self.async_show_form(
            #step_id="predefined", data_schema=PREDEFINED_CONFIG_SCHEMA, errors=errors
            step_id="predefined", data_schema=create_predefined_config_schema(self.data), errors=errors
        )
    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handles options flow for the component."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize the options flow handler."""
        self.config_entry = config_entry
        self.options_schema =None

        if config_entry.options["config_type"] == CONF_CONFIG_CRON:
            self.options_schema = create_cron_option_schema(config_entry.options)
        else:
            self.options_schema = create_predefined_option_schema(config_entry.options)

    @staticmethod
    def _validate_state(state: State | None) -> Decimal | None: # noqa: F821
        """Parse the state as a Decimal if available. Throws DecimalException if not a number."""
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
        errors: dict[str, str] = {}
        if user_input is not None:
            # Get the current repos from the config entry.
            if CONF_REMOVE_CALC_SENSOR in user_input: # sourcery skip: merge-nested-ifs
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
                user_input[CONF_METER_OFFSET] =CONF_METER_OFFSET_DURATION_DEFAULT
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
