"""Tests for Utility Meter Next Gen device management."""

from collections.abc import Iterable
from typing import Any
from unittest.mock import patch

import pytest

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from custom_components import utility_meter_next_gen as integration
from custom_components.utility_meter_next_gen import async_migrate_entry
from custom_components.utility_meter_next_gen.config_flow import (
    UtilityMeterEvolvedCustomConfigFlow,
)
from custom_components.utility_meter_next_gen.const import (
    CONF_CONFIG_CALIBRATE_APPLY,
    CONF_CONFIG_CALIBRATE_CALC_APPLY,
    CONF_CONFIG_CALIBRATE_CALC_VALUE,
    CONF_CONFIG_CALIBRATE_VALUE,
    CONF_CONFIG_PREDEFINED,
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
    DOMAIN,
    MONTHLY,
)

from pytest_homeassistant_custom_component.common import MockConfigEntry


def _options(source_entity_id: str, tariffs: Iterable[str] = ()) -> dict[str, Any]:
    """Return a complete set of config entry options."""
    return {
        CONF_CONFIG_CALIBRATE_APPLY: None,
        CONF_CONFIG_CALIBRATE_CALC_APPLY: None,
        CONF_CONFIG_CALIBRATE_CALC_VALUE: 0,
        CONF_CONFIG_CALIBRATE_VALUE: 0,
        CONF_CONFIG_TYPE: CONF_CONFIG_PREDEFINED,
        CONF_CREATE_CALCULATION_SENSOR: False,
        CONF_CRON_PATTERN: None,
        CONF_METER_DELTA_VALUES: False,
        CONF_METER_NET_CONSUMPTION: False,
        CONF_METER_OFFSET: {"days": 0, "hours": 0, "minutes": 0, "seconds": 0},
        CONF_METER_PERIODICALLY_RESETTING: True,
        CONF_METER_TYPE: MONTHLY,
        CONF_SENSOR_ALWAYS_AVAILABLE: False,
        CONF_SOURCE_CALC_MULTIPLIER: 1,
        CONF_SOURCE_CALC_SENSOR: None,
        CONF_SOURCE_SENSOR: source_entity_id,
        CONF_TARIFFS: list(tariffs),
    }


def _add_source(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    unique_id: str,
) -> tuple[MockConfigEntry, dr.DeviceEntry, er.RegistryEntry]:
    """Add a source config entry, device, and sensor entity."""
    source_entry = MockConfigEntry(domain="test")
    source_entry.add_to_hass(hass)
    source_device = device_registry.async_get_or_create(
        config_entry_id=source_entry.entry_id,
        identifiers={("test", unique_id)},
    )
    source_entity = entity_registry.async_get_or_create(
        "sensor",
        "test",
        unique_id,
        config_entry=source_entry,
        device_id=source_device.id,
    )
    return source_entry, source_device, source_entity


def _helper_entities(
    entity_registry: er.EntityRegistry, entry: ConfigEntry
) -> list[er.RegistryEntry]:
    """Return all entities belonging to a helper config entry."""
    return list(
        entity_registry.entities.get_entries_for_config_entry_id(entry.entry_id)
    )


@pytest.mark.parametrize(
    ("tariffs", "expected_entity_count"),
    [([], 1), (["peak", "offpeak"], 3)],
)
async def test_entities_link_without_owning_source_device(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    tariffs: list[str],
    expected_entity_count: int,
) -> None:
    """Entities link to the source device without adding helper ownership."""
    source_entry, source_device, source_entity = _add_source(
        hass, device_registry, entity_registry, "source"
    )
    helper_entry = MockConfigEntry(
        domain=DOMAIN,
        options=_options(source_entity.entity_id, tariffs),
        title="Energy meter",
        version=UtilityMeterEvolvedCustomConfigFlow.VERSION,
        minor_version=UtilityMeterEvolvedCustomConfigFlow.MINOR_VERSION,
    )
    helper_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(helper_entry.entry_id)
    await hass.async_block_till_done()

    helper_entities = _helper_entities(entity_registry, helper_entry)
    assert len(helper_entities) == expected_entity_count
    assert {entity.device_id for entity in helper_entities} == {source_device.id}

    source_device = device_registry.async_get(source_device.id)
    assert source_device is not None
    assert source_device.config_entries == {source_entry.entry_id}
    assert (
        dr.async_entries_for_config_entry(device_registry, helper_entry.entry_id) == []
    )


async def test_source_option_change_relinks_entities(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Changing the source relinks helper entities and preserves device ownership."""
    source_entry_1, source_device_1, source_entity_1 = _add_source(
        hass, device_registry, entity_registry, "source_1"
    )
    source_entry_2, source_device_2, source_entity_2 = _add_source(
        hass, device_registry, entity_registry, "source_2"
    )
    helper_entry = MockConfigEntry(
        domain=DOMAIN,
        options=_options(source_entity_1.entity_id, ["peak", "offpeak"]),
        title="Energy meter",
        version=UtilityMeterEvolvedCustomConfigFlow.VERSION,
        minor_version=UtilityMeterEvolvedCustomConfigFlow.MINOR_VERSION,
    )
    helper_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(helper_entry.entry_id)
    await hass.async_block_till_done()

    hass.config_entries.async_update_entry(
        helper_entry,
        options=_options(source_entity_2.entity_id, ["peak", "offpeak"]),
    )
    await hass.async_block_till_done()

    assert {
        entity.device_id for entity in _helper_entities(entity_registry, helper_entry)
    } == {source_device_2.id}
    assert device_registry.async_get(source_device_1.id).config_entries == {
        source_entry_1.entry_id
    }
    assert device_registry.async_get(source_device_2.id).config_entries == {
        source_entry_2.entry_id
    }
    assert (
        dr.async_entries_for_config_entry(device_registry, helper_entry.entry_id) == []
    )


async def test_source_entity_removal_detaches_helper_entities(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Removing the source entity detaches, but does not remove, helper entities."""
    _, _, source_entity = _add_source(hass, device_registry, entity_registry, "source")
    helper_entry = MockConfigEntry(
        domain=DOMAIN,
        options=_options(source_entity.entity_id, ["peak", "offpeak"]),
        title="Energy meter",
        version=UtilityMeterEvolvedCustomConfigFlow.VERSION,
        minor_version=UtilityMeterEvolvedCustomConfigFlow.MINOR_VERSION,
    )
    helper_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(helper_entry.entry_id)
    await hass.async_block_till_done()

    entity_registry.async_remove(source_entity.entity_id)
    await hass.async_block_till_done()

    helper_entities = _helper_entities(entity_registry, helper_entry)
    assert len(helper_entities) == 3
    assert {entity.device_id for entity in helper_entities} == {None}
    assert helper_entry.entry_id in hass.config_entries.async_entry_ids()


async def test_source_entity_rename_updates_entry_once(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Renaming the source updates the option without scheduling duplicate reloads."""
    _, source_device, source_entity = _add_source(
        hass, device_registry, entity_registry, "source"
    )
    helper_entry = MockConfigEntry(
        domain=DOMAIN,
        options=_options(source_entity.entity_id),
        title="Energy meter",
        version=UtilityMeterEvolvedCustomConfigFlow.VERSION,
        minor_version=UtilityMeterEvolvedCustomConfigFlow.MINOR_VERSION,
    )
    helper_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(helper_entry.entry_id)
    await hass.async_block_till_done()

    with patch(
        "custom_components.utility_meter_next_gen.async_unload_entry",
        wraps=integration.async_unload_entry,
    ) as mock_unload_entry:
        entity_registry.async_update_entity(
            source_entity.entity_id,
            new_entity_id="sensor.renamed_source",
        )
        await hass.async_block_till_done()

    assert mock_unload_entry.call_count == 1
    assert helper_entry.options[CONF_SOURCE_SENSOR] == "sensor.renamed_source"
    assert {
        entity.device_id for entity in _helper_entities(entity_registry, helper_entry)
    } == {source_device.id}


async def test_device_model_migration_removes_all_legacy_devices(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Migration removes stale helper-owned devices and relinks their entities."""
    source_entry, source_device, source_entity = _add_source(
        hass, device_registry, entity_registry, "current_source"
    )
    helper_entry = MockConfigEntry(
        domain=DOMAIN,
        options=_options(source_entity.entity_id),
        title="Energy meter",
        version=UtilityMeterEvolvedCustomConfigFlow.VERSION,
        minor_version=1,
    )
    helper_entry.add_to_hass(hass)

    legacy_devices = [
        device_registry.async_get_or_create(
            config_entry_id=helper_entry.entry_id,
            identifiers={("legacy", legacy_id)},
        )
        for legacy_id in ("old_source", "current_source")
    ]
    for index, legacy_device in enumerate(legacy_devices):
        entity_registry.async_get_or_create(
            "sensor",
            DOMAIN,
            f"legacy_{index}",
            config_entry=helper_entry,
            device_id=legacy_device.id,
        )

    assert await async_migrate_entry(hass, helper_entry)

    assert helper_entry.version == UtilityMeterEvolvedCustomConfigFlow.VERSION
    assert (
        helper_entry.minor_version == UtilityMeterEvolvedCustomConfigFlow.MINOR_VERSION
    )
    assert {
        entity.device_id for entity in _helper_entities(entity_registry, helper_entry)
    } == {source_device.id}
    assert all(
        device_registry.async_get(legacy_device.id) is None
        for legacy_device in legacy_devices
    )
    source_device = device_registry.async_get(source_device.id)
    assert source_device is not None
    assert source_device.config_entries == {source_entry.entry_id}


async def test_legacy_data_migration_preserves_both_calibration_values(
    hass: HomeAssistant,
) -> None:
    """Version 3 migration retains both calibration defaults."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        options={
            CONF_SOURCE_SENSOR: "sensor.source",
            CONF_SOURCE_CALC_MULTIPLIER: 1,
        },
        version=3,
        minor_version=1,
    )
    entry.add_to_hass(hass)

    assert await async_migrate_entry(hass, entry)

    assert entry.options[CONF_CONFIG_CALIBRATE_VALUE] == 0
    assert entry.options[CONF_CONFIG_CALIBRATE_CALC_VALUE] == 0
