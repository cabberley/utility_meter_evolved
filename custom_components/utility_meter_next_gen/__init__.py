"""Support for tracking consumption over given periods of time."""

from datetime import datetime
import logging

from cronsim import CronSim, CronSimError
import voluptuous as vol

from homeassistant.components.select import DOMAIN as SELECT_DOMAIN
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID, CONF_NAME, CONF_UNIQUE_ID, Platform
from homeassistant.core import HomeAssistant, split_entity_id
from homeassistant.helpers import (
    config_validation as cv,
    discovery,
    entity_registry as er,
)
from homeassistant.helpers.device import (
    async_entity_id_to_device_id,
    async_remove_stale_devices_links_keep_entity_device,
)
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.helper_integration import (
    async_handle_source_entity_changes,  # noqa: PGH003 # type: ignore
)
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_CONFIG_CALIBRATE_APPLY,
    CONF_CONFIG_CALIBRATE_CALC_APPLY,
    CONF_CONFIG_CALIBRATE_CALC_VALUE,
    CONF_CONFIG_CALIBRATE_VALUE,
    CONF_CREATE_CALCULATION_SENSOR,
    CONF_CREATE_CALCULATION_SENSOR_DEFAULT,
    CONF_CRON_PATTERN,
    CONF_METER,
    CONF_METER_DELTA_VALUES,
    CONF_METER_NET_CONSUMPTION,
    CONF_METER_OFFSET,
    CONF_METER_OFFSET_DURATION_DEFAULT,
    CONF_METER_PERIODICALLY_RESETTING,
    CONF_METER_TYPE,
    CONF_METER_TYPES,
    CONF_SENSOR_ALWAYS_AVAILABLE,
    CONF_SOURCE_CALC_MULTIPLIER,
    CONF_SOURCE_SENSOR,
    CONF_TARIFF,
    CONF_TARIFF_ENTITY,
    CONF_TARIFFS,
    DATA_TARIFF_SENSORS,
    DATA_UTILITY,
    DOMAIN,
    SERVICE_RESET,
    SIGNAL_RESET_METER,
)

_LOGGER = logging.getLogger(__name__)

def validate_cron_pattern(pattern):
    """Check that the pattern is well-formed."""
    try:
        _LOGGER.debug("Testing cron pattern: %s", pattern)
        CronSim(pattern, datetime(2020, 1, 1))  # any date will do
    except CronSimError as err:
        _LOGGER.error("Invalid cron pattern %s: %s", pattern, err)
        raise vol.Invalid("Invalid pattern") from err
    return pattern

def period_or_cron(config):
    """Check that if cron pattern is used, then meter type and offsite must be removed."""
    if CONF_CRON_PATTERN in config and CONF_METER_TYPE in config:
        raise vol.Invalid(f"Use <{CONF_CRON_PATTERN}> or <{CONF_METER_TYPE}>")
    if (
        CONF_CRON_PATTERN in config
        and CONF_METER_OFFSET in config
        and config[CONF_METER_OFFSET] != CONF_METER_OFFSET_DURATION_DEFAULT
    ):
        raise vol.Invalid(
            f"When <{CONF_CRON_PATTERN}> is used <{CONF_METER_OFFSET}> has no meaning"
        )
    return config

METER_CONFIG_SCHEMA = vol.Schema(
    vol.All(
        {
            vol.Required(CONF_SOURCE_SENSOR): cv.entity_id,
            vol.Optional(CONF_NAME): cv.string,
            vol.Optional(CONF_UNIQUE_ID): cv.string,
            vol.Optional(CONF_METER_TYPE): vol.In(CONF_METER_TYPES),
            vol.Optional(CONF_METER_OFFSET,
                default=CONF_METER_OFFSET_DURATION_DEFAULT): cv.ensure_list,
            vol.Optional(CONF_METER_DELTA_VALUES, default=False): cv.boolean,
            vol.Optional(CONF_METER_NET_CONSUMPTION, default=False): cv.boolean,
            vol.Optional(CONF_METER_PERIODICALLY_RESETTING, default=True): cv.boolean,
            vol.Optional(CONF_TARIFFS, default=[]): vol.All(
                cv.ensure_list, vol.Unique(), [cv.string]
            ),
            vol.Optional(CONF_CRON_PATTERN): validate_cron_pattern,
            vol.Optional(CONF_SENSOR_ALWAYS_AVAILABLE, default=False): cv.boolean,
        },
        period_or_cron,
    )
)

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Schema({cv.slug: METER_CONFIG_SCHEMA})}, extra=vol.ALLOW_EXTRA
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up an Utility Meter."""
    hass.data[DATA_UTILITY] = {}

    async def async_reset_meters(service_call):
        """Reset all sensors of a meter."""
        meters = service_call.data["entity_id"]

        for meter in meters:
            _LOGGER.debug("resetting meter %s", meter)
            domain, entity = split_entity_id(meter)
            # backward compatibility up to 2022.07:
            if domain == DOMAIN:
                async_dispatcher_send(
                    hass, SIGNAL_RESET_METER, f"{SELECT_DOMAIN}.{entity}"
                )
            else:
                async_dispatcher_send(hass, SIGNAL_RESET_METER, meter)

    hass.services.async_register(
        DOMAIN,
        SERVICE_RESET,
        async_reset_meters,
        vol.Schema({ATTR_ENTITY_ID: vol.All(cv.ensure_list, [cv.entity_id])}),
    )

    if DOMAIN not in config:
        return True

    for meter, conf in config[DOMAIN].items():
        _LOGGER.debug("Setup %s.%s", DOMAIN, meter)

        hass.data[DATA_UTILITY][meter] = conf
        hass.data[DATA_UTILITY][meter][DATA_TARIFF_SENSORS] = []

        if not conf[CONF_TARIFFS]:
            # only one entity is required
            hass.async_create_task(
                discovery.async_load_platform(
                    hass,
                    SENSOR_DOMAIN,
                    DOMAIN,
                    {meter: {CONF_METER: meter}},
                    config,
                ),
                eager_start=True,
            )
        else:
            # create tariff selection
            hass.async_create_task(
                discovery.async_load_platform(
                    hass,
                    SELECT_DOMAIN,
                    DOMAIN,
                    {CONF_METER: meter, CONF_TARIFFS: conf[CONF_TARIFFS]},
                    config,
                ),
                eager_start=True,
            )

            hass.data[DATA_UTILITY][meter][CONF_TARIFF_ENTITY] = (
                f"{SELECT_DOMAIN}.{meter}"
            )

            # add one meter for each tariff
            tariff_confs = {}
            for tariff in conf[CONF_TARIFFS]:
                name = f"{meter} {tariff}"
                tariff_confs[name] = {
                    CONF_METER: meter,
                    CONF_TARIFF: tariff,
                }

            hass.async_create_task(
                discovery.async_load_platform(
                    hass, SENSOR_DOMAIN, DOMAIN, tariff_confs, config
                ),
                eager_start=True,
            )

    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Utility Meter from a config entry."""

    async_remove_stale_devices_links_keep_entity_device(
        hass, entry.entry_id, entry.options[CONF_SOURCE_SENSOR]
    )

    entity_registry = er.async_get(hass)
    hass.data[DATA_UTILITY][entry.entry_id] = {
        "source": entry.options[CONF_SOURCE_SENSOR],
    }
    hass.data[DATA_UTILITY][entry.entry_id][DATA_TARIFF_SENSORS] = []

    try:
        er.async_validate_entity_id(entity_registry, entry.options[CONF_SOURCE_SENSOR])
    except vol.Invalid:
        # The entity is identified by an unknown entity registry ID
        _LOGGER.error(
            "Failed to setup utility_meter for unknown entity %s",
            entry.options[CONF_SOURCE_SENSOR],
        )
        return False

    def set_source_entity_id_or_uuid(source_entity_id: str) -> None:
        hass.config_entries.async_update_entry(
            entry,
            options={**entry.options, CONF_SOURCE_SENSOR: source_entity_id},
        )

    async def source_entity_removed() -> None:
        # The source entity has been removed, we need to clean the device links.
        async_remove_stale_devices_links_keep_entity_device(hass, entry.entry_id, None)

    entry.async_on_unload(
        async_handle_source_entity_changes(
            hass,
            helper_config_entry_id=entry.entry_id,
            set_source_entity_id_or_uuid=set_source_entity_id_or_uuid,
            source_device_id=async_entity_id_to_device_id(
                hass, entry.options[CONF_SOURCE_SENSOR]
            ),
            source_entity_id_or_uuid=entry.options[CONF_SOURCE_SENSOR],
            source_entity_removed=source_entity_removed,
        )
    )

    if not entry.options.get(CONF_TARIFFS):
        # Only a single meter sensor is required
        hass.data[DATA_UTILITY][entry.entry_id][CONF_TARIFF_ENTITY] = None
        await hass.config_entries.async_forward_entry_setups(entry, (Platform.SENSOR,))
    else:
        # Create tariff selection + one meter sensor for each tariff
        entity_entry = entity_registry.async_get_or_create(
            Platform.SELECT, DOMAIN, entry.entry_id, suggested_object_id=entry.title
        )
        #entry.options[CONF_TARIFFS].append("total")
        hass.data[DATA_UTILITY][entry.entry_id][CONF_TARIFF_ENTITY] = (
            entity_entry.entity_id
        )
        await hass.config_entries.async_forward_entry_setups(
            entry, (Platform.SELECT, Platform.SENSOR)
        )

    entry.async_on_unload(entry.add_update_listener(config_entry_update_listener))

    return True


async def config_entry_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update listener, called when the config entry options are changed."""

    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    platforms_to_unload = [Platform.SENSOR]
    if entry.options.get(CONF_TARIFFS):
        platforms_to_unload.append(Platform.SELECT)

    if unload_ok := await hass.config_entries.async_unload_platforms(
        entry,
        platforms_to_unload,
    ):
        hass.data[DATA_UTILITY].pop(entry.entry_id)

    return unload_ok


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", config_entry.version)

    if config_entry.version == 1:
        new = {**config_entry.options,CONF_METER_PERIODICALLY_RESETTING: True}
        hass.config_entries.async_update_entry(config_entry, options=new, version=2)

    _LOGGER.info("Migration to version %s successful", config_entry.version)

    if config_entry.version == 2 or config_entry.version is None:
        new = {**config_entry.options, CONF_SOURCE_CALC_MULTIPLIER: 1}
        hass.config_entries.async_update_entry(config_entry, options=new, version=3)

    _LOGGER.info("Migration to version %s successful", config_entry.version)

    if config_entry.version == 3:
        new = {**config_entry.options, CONF_CONFIG_CALIBRATE_CALC_VALUE: 0}
        new = {**config_entry.options, CONF_CONFIG_CALIBRATE_VALUE: 0}
        hass.config_entries.async_update_entry(config_entry, options=new, version=4)

    _LOGGER.info("Migration to version %s successful", config_entry.version)

    if config_entry.version == 4:
        new = {**config_entry.options, CONF_CONFIG_CALIBRATE_CALC_VALUE: 0}
        hass.config_entries.async_update_entry(config_entry, options=new, version=5)

    _LOGGER.info("Migration to version %s successful", config_entry.version)

    if config_entry.version == 5:
        new = {**config_entry.options,
               CONF_CREATE_CALCULATION_SENSOR: CONF_CREATE_CALCULATION_SENSOR_DEFAULT}
        hass.config_entries.async_update_entry(config_entry, options=new, version=6)

    _LOGGER.info("Migration to version %s successful", config_entry.version)

    if config_entry.version == 6:
        new = {**config_entry.options,
               CONF_CONFIG_CALIBRATE_CALC_APPLY: None}
        hass.config_entries.async_update_entry(config_entry, options=new, version=7)

    _LOGGER.info("Migration to version %s successful", config_entry.version)

    if config_entry.version == 7:
        new = {**config_entry.options,
               CONF_CONFIG_CALIBRATE_APPLY: None}
        hass.config_entries.async_update_entry(config_entry, options=new, version=8)

    _LOGGER.info("Migration to version %s successful", config_entry.version)

    return True
