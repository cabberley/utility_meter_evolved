"""Tests for sensor-backed calibration and daily standing charges."""

from decimal import Decimal
from unittest.mock import Mock

import pytest
import voluptuous as vol

from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er

from custom_components.utility_meter_next_gen.const import (
    ATTR_CALC_CURRENT_VALUE,
    ATTR_CALC_LAST_VALUE,
    ATTR_PREDEFINED_CYCLE,
    CONF_CONFIG_CALIBRATE_APPLY,
    CONF_CONFIG_CALIBRATE_CALC_APPLY,
    CONF_CONFIG_CALIBRATE_CALC_SENSOR,
    CONF_CONFIG_CALIBRATE_CALC_VALUE,
    CONF_CONFIG_CALIBRATE_SENSOR,
    CONF_CONFIG_CALIBRATE_VALUE,
    CONF_CONFIG_CRON,
    CONF_CONFIG_TYPE,
    CONF_CREATE_CALCULATION_SENSOR,
    CONF_CRON_PATTERN,
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
    DAILY,
    DATA_TARIFF_SENSORS,
    DATA_UTILITY,
    DOMAIN,
    MONTHLY,
)
from custom_components.utility_meter_next_gen.schemas import (
    create_cron_config_schema,
    create_cron_option_schema,
    create_multi_config_schema_step_2,
    create_multi_option_schema_step_2,
    create_predefined_config_schema,
    create_predefined_option_schema,
)
from custom_components.utility_meter_next_gen.sensor import UtilityMeterSensor

from pytest_homeassistant_custom_component.common import MockConfigEntry


@pytest.fixture
def options():
    """Return options shared by setup, options, and runtime tests."""
    return {
        CONF_SOURCE_SENSOR: "sensor.energy",
        CONF_SOURCE_CALC_SENSOR: "sensor.rate",
        CONF_SOURCE_CALC_MULTIPLIER: 1,
        CONF_CREATE_CALCULATION_SENSOR: True,
        CONF_CONFIG_TYPE: "predefined",
        CONF_CONFIG_CALIBRATE_APPLY: DAILY,
        CONF_CONFIG_CALIBRATE_CALC_APPLY: DAILY,
        CONF_CONFIG_CALIBRATE_VALUE: 2,
        CONF_CONFIG_CALIBRATE_CALC_VALUE: 0.5,
        CONF_METER_TYPE: DAILY,
        CONF_METER_OFFSET: {"days": 0, "hours": 0, "minutes": 0, "seconds": 0},
        CONF_CONFIG_CRON: "0 0 * * *",
        CONF_CRON_PATTERN: None,
        CONF_TARIFFS: [],
        CONF_METER_NET_CONSUMPTION: False,
        CONF_METER_DELTA_VALUES: False,
        CONF_METER_PERIODICALLY_RESETTING: True,
        CONF_SENSOR_ALWAYS_AVAILABLE: False,
    }


@pytest.mark.parametrize(
    "schema_factory",
    [
        create_predefined_config_schema,
        create_cron_config_schema,
        create_multi_config_schema_step_2,
        create_predefined_option_schema,
        create_cron_option_schema,
        create_multi_option_schema_step_2,
    ],
)
@pytest.mark.parametrize("existing_entity", [None, "sensor.charge"])
def test_calibration_selectors(schema_factory, options, existing_entity):
    """All forms accept entities and retain legacy numeric calibration."""
    options[CONF_METER_TYPE] = [DAILY, MONTHLY]
    for key in (CONF_CONFIG_CALIBRATE_SENSOR, CONF_CONFIG_CALIBRATE_CALC_SENSOR):
        if existing_entity:
            options[key] = existing_entity
    schema = schema_factory(options)
    for key in (CONF_CONFIG_CALIBRATE_SENSOR, CONF_CONFIG_CALIBRATE_CALC_SENSOR):
        entity_selector = schema.schema[key]
        assert entity_selector("sensor.charge") == "sensor.charge"
        assert entity_selector("input_number.charge") == "input_number.charge"
        with pytest.raises(vol.Invalid):
            entity_selector("input_text.charge")
        marker = next(field for field in schema.schema if field == key)
        assert marker.default is vol.UNDEFINED
        assert marker.description["suggested_value"] == existing_entity
    assert schema.schema[CONF_CONFIG_CALIBRATE_VALUE](2) == 2
    assert schema.schema[CONF_CONFIG_CALIBRATE_CALC_VALUE](0.5) == 0.5


async def test_options_can_clear_calibration_entities(hass: HomeAssistant, options):
    """Clearing optional entity inputs restores fixed calibration values."""
    options[CONF_CONFIG_CALIBRATE_SENSOR] = "sensor.consumption_offset"
    options[CONF_CONFIG_CALIBRATE_CALC_SENSOR] = "sensor.charge"
    entry = MockConfigEntry(
        domain=DOMAIN, options=options, title="Electricity", version=8
    )
    entry.add_to_hass(hass)
    hass.states.async_set("sensor.rate", "0.25")
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    user_input = {
        key: value
        for key, value in options.items()
        if key in result["data_schema"].schema
        and key
        not in (
            CONF_CONFIG_CALIBRATE_SENSOR,
            CONF_CONFIG_CALIBRATE_CALC_SENSOR,
            CONF_TARIFFS,
        )
    }
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert CONF_CONFIG_CALIBRATE_SENSOR not in entry.options
    assert CONF_CONFIG_CALIBRATE_CALC_SENSOR not in entry.options
    assert entry.options[CONF_CONFIG_CALIBRATE_VALUE] == 2
    assert entry.options[CONF_CONFIG_CALIBRATE_CALC_VALUE] == 0.5


@pytest.mark.parametrize("cycle", [DAILY, [DAILY, MONTHLY], None])
@pytest.mark.parametrize("charge_domain", ["sensor", "input_number", None])
async def test_standing_charge_cost_and_reset(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    options,
    cycle,
    charge_domain,
):
    """Daily costs include one offset plus incrementally priced consumption."""
    options[CONF_METER_TYPE] = cycle
    if cycle is None:
        options[CONF_CONFIG_TYPE] = "cron"
        options[CONF_CRON_PATTERN] = "0 0 * * *"
    elif isinstance(cycle, list):
        options[CONF_CONFIG_TYPE] = "multi"
    if charge_domain:
        options[CONF_CONFIG_CALIBRATE_SENSOR] = "sensor.consumption_offset"
        options[CONF_CONFIG_CALIBRATE_CALC_SENSOR] = f"{charge_domain}.charge"
        hass.states.async_set("sensor.consumption_offset", "3")
        hass.states.async_set(f"{charge_domain}.charge", "0.60")
    hass.states.async_set("sensor.energy", "100", {"unit_of_measurement": "kWh"})
    hass.states.async_set("sensor.rate", "0.25", {"unit_of_measurement": "GBP/kWh"})
    await hass.async_start()
    entry = MockConfigEntry(
        domain=DOMAIN, options=options, title="Electricity", version=8
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    hass.states.async_set("sensor.energy", "102", {"unit_of_measurement": "kWh"})
    await hass.async_block_till_done()
    meters = [
        entity
        for entity in hass.data[DATA_UTILITY][entry.entry_id][DATA_TARIFF_SENSORS]
        if isinstance(entity, UtilityMeterSensor)
    ]
    for meter in meters:
        applied = meter.extra_state_attributes.get(ATTR_PREDEFINED_CYCLE) != "Monthly"
        charge = Decimal("0.60" if charge_domain else "0.5") if applied else Decimal(0)
        offset = Decimal(3 if charge_domain else 2) if applied else Decimal(0)
        assert meter.native_value == offset + 2
        assert Decimal(
            meter.extra_state_attributes[ATTR_CALC_CURRENT_VALUE]
        ) == charge + Decimal("0.5")
        calculated_id = entity_registry.async_get_entity_id(
            "sensor", DOMAIN, f"{meter.name} Calculated"
        )
        state = hass.states.get(calculated_id)
        assert state.attributes["unit_of_measurement"] == "GBP"
        assert Decimal(state.state) == charge + Decimal("0.5")

    if charge_domain:
        hass.states.async_set(f"{charge_domain}.charge", "0.75")
        await hass.async_block_till_done()
    hass.states.async_set("sensor.rate", "0.30")
    hass.states.async_set("sensor.energy", "103", {"unit_of_measurement": "kWh"})
    await hass.async_block_till_done()
    for meter in meters:
        applied = meter.extra_state_attributes.get(ATTR_PREDEFINED_CYCLE) != "Monthly"
        old_charge = (
            Decimal("0.60" if charge_domain else "0.5") if applied else Decimal(0)
        )
        assert Decimal(
            meter.extra_state_attributes[ATTR_CALC_CURRENT_VALUE]
        ) == old_charge + Decimal("0.8")
        await meter.async_reset_meter(None)
        charge = Decimal("0.75" if charge_domain else "0.5") if applied else Decimal(0)
        assert Decimal(
            meter.extra_state_attributes[ATTR_CALC_LAST_VALUE]
        ) == old_charge + Decimal("0.8")
        assert Decimal(meter.extra_state_attributes[ATTR_CALC_CURRENT_VALUE]) == charge
        await meter.async_reset_meter(None)
        assert Decimal(meter.extra_state_attributes[ATTR_CALC_CURRENT_VALUE]) == charge


@pytest.mark.parametrize(
    "reading",
    [None, "unknown", "unavailable", "invalid", "NaN", "Infinity", "-Infinity"],
)
async def test_invalid_calibration_reading(hass: HomeAssistant, reading):
    """Invalid calibration sources cannot corrupt consumption or cost totals."""
    meter = UtilityMeterSensor(
        cron_pattern=None,
        delta_values=False,
        meter_offset={},
        meter_type=None,
        name="Electricity",
        net_consumption=False,
        parent_meter="test",
        periodically_resetting=True,
        source_entity="sensor.energy",
        source_calc_entity="sensor.rate",
        source_calc_multiplier=1,
        calibrate_value="sensor.charge",
        calibrate_calc_value="sensor.charge",
        tariff_entity=None,
        tariff=None,
        unique_id="test",
        sensor_always_available=True,
    )
    meter.hass = hass
    meter.async_write_ha_state = Mock()
    if reading is not None:
        hass.states.async_set("sensor.charge", reading)
    meter.start({})
    assert meter.native_value == 0
    assert Decimal(meter.extra_state_attributes[ATTR_CALC_CURRENT_VALUE]) == 0
    await meter.async_reset_meter(None)
    assert meter.native_value == 0
    assert Decimal(meter.extra_state_attributes[ATTR_CALC_CURRENT_VALUE]) == 0
    hass.states.async_set("sensor.charge", "0.65")
    await meter.async_reset_meter(None)
    assert meter.native_value == Decimal("0.65")
    assert Decimal(meter.extra_state_attributes[ATTR_CALC_CURRENT_VALUE]) == Decimal(
        "0.65"
    )
