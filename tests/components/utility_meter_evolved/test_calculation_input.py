"""Tests for selecting calculation input entities."""

import pytest
import voluptuous as vol

from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.utility_meter_next_gen.config_flow import (
    UtilityMeterEvolvedCustomConfigFlow,
)
from custom_components.utility_meter_next_gen.const import (
    CONF_CONFIG_CALIBRATE_APPLY,
    CONF_CONFIG_CALIBRATE_CALC_APPLY,
    CONF_CONFIG_CALIBRATE_CALC_VALUE,
    CONF_CONFIG_CALIBRATE_VALUE,
    CONF_CONFIG_CRON,
    CONF_CONFIG_PREDEFINED,
    CONF_CREATE_CALCULATION_SENSOR,
    CONF_METER_DELTA_VALUES,
    CONF_METER_NET_CONSUMPTION,
    CONF_METER_OFFSET,
    CONF_METER_PERIODICALLY_RESETTING,
    CONF_METER_TYPE,
    CONF_SENSOR_ALWAYS_AVAILABLE,
    CONF_SOURCE_CALC_MULTIPLIER,
    CONF_SOURCE_CALC_SENSOR,
    CONF_SOURCE_SENSOR,
    CONF_TARIFFS,
    DEVICE_CLASSES_METER,
)
from custom_components.utility_meter_next_gen.schemas import (
    BASE_CONFIG_SCHEMA,
    create_cron_option_schema,
    create_multi_option_schema_step_2,
    create_predefined_option_schema,
)


def _assert_input_selectors(schema: vol.Schema) -> None:
    """Verify calculation helper support without broadening meter sources."""
    calc_selector = schema.schema[CONF_SOURCE_CALC_SENSOR]
    assert calc_selector.config["domain"] == ["sensor", "input_number"]
    assert calc_selector("input_number.electric_rate") == "input_number.electric_rate"
    assert calc_selector("sensor.electric_rate") == "sensor.electric_rate"
    with pytest.raises(vol.Invalid):
        calc_selector("input_text.electric_rate")

    source_selector = schema.schema[CONF_SOURCE_SENSOR]
    assert source_selector.config["domain"] == ["sensor"]
    assert source_selector.config["filter"] == [{"device_class": DEVICE_CLASSES_METER}]


def test_setup_calculation_input_selector() -> None:
    """Initial setup allows input_number helpers as calculation inputs."""
    _assert_input_selectors(BASE_CONFIG_SCHEMA)


@pytest.mark.parametrize(
    "schema_factory",
    [
        create_predefined_option_schema,
        create_cron_option_schema,
        create_multi_option_schema_step_2,
    ],
)
@pytest.mark.parametrize(
    "existing_calc_source", [None, "sensor.electric_rate", "input_number.electric_rate"]
)
def test_options_calculation_input_selector(
    schema_factory, existing_calc_source: str | None
) -> None:
    """All options forms support adding or replacing a calculation input."""
    data = {
        CONF_SOURCE_SENSOR: "sensor.energy",
        CONF_SOURCE_CALC_SENSOR: existing_calc_source,
        CONF_SOURCE_CALC_MULTIPLIER: 1,
        CONF_CREATE_CALCULATION_SENSOR: True,
        CONF_CONFIG_CALIBRATE_APPLY: None,
        CONF_CONFIG_CALIBRATE_CALC_APPLY: None,
        CONF_CONFIG_CALIBRATE_VALUE: 0,
        CONF_CONFIG_CALIBRATE_CALC_VALUE: 0,
        CONF_METER_TYPE: ["daily"],
        CONF_METER_OFFSET: {"days": 0},
        CONF_CONFIG_CRON: "0 0 * * *",
        CONF_TARIFFS: [],
        CONF_METER_NET_CONSUMPTION: False,
        CONF_METER_DELTA_VALUES: False,
        CONF_METER_PERIODICALLY_RESETTING: True,
        CONF_SENSOR_ALWAYS_AVAILABLE: False,
    }
    _assert_input_selectors(schema_factory(data))


@pytest.mark.parametrize("calc_domain", ["sensor", "input_number"])
async def test_setup_accepts_numeric_calculation_input(
    hass: HomeAssistant, calc_domain: str
) -> None:
    """The setup flow accepts an electricity rate with a compound unit."""
    calc_entity = f"{calc_domain}.electric_rate"
    hass.states.async_set("sensor.energy", "100", {"device_class": "energy"})
    hass.states.async_set(calc_entity, "0.35", {"unit_of_measurement": "USD/kWh"})
    flow = UtilityMeterEvolvedCustomConfigFlow()
    flow.hass = hass

    user_input = BASE_CONFIG_SCHEMA(
        {
            "name": "Electricity cost",
            CONF_SOURCE_SENSOR: "sensor.energy",
            CONF_SOURCE_CALC_SENSOR: calc_entity,
            "config_type": CONF_CONFIG_PREDEFINED,
        }
    )
    result = await flow.async_step_user(user_input)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "predefined"
    assert result["errors"] == {}
    assert flow.data[CONF_SOURCE_CALC_SENSOR] == calc_entity
