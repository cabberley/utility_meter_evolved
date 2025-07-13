"""Utility meter from sensors providing raw data."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, DecimalException, InvalidOperation
import logging
import re
from typing import Any, Self

from cronsim import CronSim
import voluptuous as vol

from homeassistant.components.sensor import (
    ATTR_LAST_RESET,
    RestoreSensor,
    SensorDeviceClass,
    SensorExtraStoredData,
    SensorStateClass,
)
from homeassistant.components.sensor.const import DEVICE_CLASS_UNITS
from homeassistant.components.sensor.recorder import _suggest_report_issue
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    ATTR_UNIT_OF_MEASUREMENT,
    CONF_NAME,
    CONF_UNIQUE_ID,
    CURRENCY_DOLLAR,
    EVENT_CORE_CONFIG_UPDATE,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import (
    Event,
    EventStateChangedData,
    HomeAssistant,
    State,
    callback,
)
from homeassistant.helpers import entity_platform, entity_registry as er
from homeassistant.helpers.device import async_device_info_to_link_from_entity
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import (
    async_track_point_in_time,
    async_track_state_change_event,
    async_track_state_report_event,
)
from homeassistant.helpers.start import async_at_started
from homeassistant.helpers.template import is_number
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util import dt as dt_util, slugify
from homeassistant.util.enum import try_parse_enum

from .const import (
    ATTR_CALC_CURRENT_VALUE,
    ATTR_CALC_LAST_VALUE,
    ATTR_LAST_PERIOD,
    ATTR_LAST_VALID_STATE,
    ATTR_LINKED_METER,
    ATTR_NEXT_RESET,
    ATTR_PREDEFINED_CYCLE,
    ATTR_SOURCE_ID,
    ATTR_STATUS,
    ATTR_TARIFF,
    ATTR_VALUE,
    COLLECTING,
    CONF_CONFIG_CALIBRATE_APPLY,
    CONF_CONFIG_CALIBRATE_CALC_APPLY,
    CONF_CONFIG_CALIBRATE_CALC_VALUE,
    CONF_CONFIG_CALIBRATE_VALUE,
    CONF_CREATE_CALCULATION_SENSOR,
    CONF_CRON_PATTERN,
    CONF_METER,
    CONF_METER_DELTA_VALUES,
    CONF_METER_NET_CONSUMPTION,
    CONF_METER_OFFSET,
    CONF_METER_PERIODICALLY_RESETTING,
    CONF_METER_TYPE,
    CONF_SENSOR_ALWAYS_AVAILABLE,
    CONF_SOURCE_CALC_MULTIPLIER,
    CONF_SOURCE_CALC_SENSOR,
    CONF_SOURCE_SENSOR,
    CONF_TARIFF,
    CONF_TARIFF_ENTITY,
    CONF_TARIFFS,
    DATA_TARIFF_SENSORS,
    DATA_UTILITY,
    METER_NAME_TYPES,
    PAUSED,
    PERIOD2CRON,
    PRECISION,
    SERVICE_CALIBRATE_METER,
    SIGNAL_RESET_METER,
    SINGLE_TARIFF,
    TOTAL_TARIFF,
)

_LOGGER = logging.getLogger(__name__)


def validate_is_number(value):
    """Validate value is a number."""
    if is_number(value):
        return value
    raise vol.Invalid("Value is not a number")


def clean_string(input_string):
    """Replace non-alphanumeric characters with underscores."""
    result = re.sub(r"[^a-zA-Z0-9]", "_", input_string)
    # Remove consecutive underscores
    result = re.sub(r"_+", "_", result)
    # Convert to lowercase
    return result.lower()

def clean_string_display(input_string):
    """Replace non-alphanumeric characters with underscores."""
    result = re.sub(r"[^a-zA-Z0-9]", " ", input_string)
    # Remove consecutive underscores
    result = re.sub(r" +", " ", result)
    # Convert to lowercase
    return result.title()

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialize Utility Meter config entry."""
    entry_id = config_entry.entry_id
    registry = er.async_get(hass)
    # Validate + resolve entity registry id to entity_id
    source_entity_id = er.async_validate_entity_id(
        registry, config_entry.options[CONF_SOURCE_SENSOR]
    )
    device_info = async_device_info_to_link_from_entity(
        hass,
        source_entity_id,
    )
    if config_entry.options[CONF_SOURCE_CALC_SENSOR] is not None:
        source_calc_entity_id = er.async_validate_entity_id(
            registry, config_entry.options[CONF_SOURCE_CALC_SENSOR]
        )
    else:
        source_calc_entity_id = None
    calibrate_calc_apply = config_entry.options.get(CONF_CONFIG_CALIBRATE_CALC_APPLY, None)
    calibrate_calc_value = config_entry.options.get(CONF_CONFIG_CALIBRATE_CALC_VALUE, Decimal(0))
    calibrate_apply = config_entry.options.get(CONF_CONFIG_CALIBRATE_APPLY, None)
    calibrate_value = config_entry.options.get(CONF_CONFIG_CALIBRATE_VALUE, Decimal(0))
    create_calc_sensor = config_entry.options[CONF_CREATE_CALCULATION_SENSOR]
    cron_pattern = config_entry.options[CONF_CRON_PATTERN]
    delta_values = config_entry.options[CONF_METER_DELTA_VALUES]
    meter_offset = config_entry.options[CONF_METER_OFFSET]
    meter_type = config_entry.options[CONF_METER_TYPE]
    if meter_type == "none":
        meter_type = None
    name = config_entry.title
    net_consumption = config_entry.options[CONF_METER_NET_CONSUMPTION]
    periodically_resetting = config_entry.options[CONF_METER_PERIODICALLY_RESETTING]
    sensor_always_available = config_entry.options.get(
        CONF_SENSOR_ALWAYS_AVAILABLE, False
    )
    source_calc_multiplier = config_entry.options[CONF_SOURCE_CALC_MULTIPLIER]
    tariff_entity = hass.data[DATA_UTILITY][entry_id][CONF_TARIFF_ENTITY]

    meters = []
    calc_sensors = []
    tariffs = config_entry.options[CONF_TARIFFS]

    if meter_type is not None and not isinstance(meter_type, str) and len(meter_type) > 1:
        for meter in meter_type:
            if not tariffs:
                # Add single sensor, not gated by a tariff selector
                meter_sensor = UtilityMeterSensor(
                    calibrate_calc_value=(
                        calibrate_calc_value
                        if calibrate_calc_apply == meter
                        else Decimal(0)
                    ),
                    calibrate_value=(
                        calibrate_value if calibrate_apply == meter else Decimal(0)
                    ),
                    cron_pattern=cron_pattern,
                    delta_values=delta_values,
                    device_info=device_info,
                    meter_offset=meter_offset,
                    meter_type=meter,
                    name=f"{name} {METER_NAME_TYPES[meter]}",
                    net_consumption=net_consumption,
                    parent_meter=entry_id,
                    periodically_resetting=periodically_resetting,
                    sensor_always_available=sensor_always_available,
                    source_calc_entity=source_calc_entity_id,
                    source_calc_multiplier=source_calc_multiplier,
                    source_entity=source_entity_id,
                    tariff_entity=tariff_entity,
                    tariff=None,
                    unique_id=f"{entry_id}_{METER_NAME_TYPES[meter]}",
                )
                meters.append(meter_sensor)
                hass.data[DATA_UTILITY][entry_id][DATA_TARIFF_SENSORS].append(
                    meter_sensor
                )

                if create_calc_sensor:
                    # Create a calculated sensor for the total consumption
                    calc_sensor = UtilityMeterCalculatedSensor(
                        attribute=ATTR_CALC_CURRENT_VALUE,
                        calibrate_calc_value=(
                            calibrate_calc_value
                            if calibrate_calc_apply == meter
                            else Decimal(0)
                        ),
                        cron_pattern=cron_pattern,
                        device_class=None,
                        device_info=device_info,
                        entity_id=(
                            f"sensor.{clean_string(name)}_{clean_string(METER_NAME_TYPES[meter])}"
                        ),
                        hass=hass,
                        icon=None,
                        meter_type=meter,
                        name=f"{name} {METER_NAME_TYPES[meter]} Calculated",
                        source_calc_entity=source_calc_entity_id,
                        source_entity=source_entity_id,
                        state_class=None,
                        tariff=None,
                        unique_id=f"{name} {METER_NAME_TYPES[meter]} Calculated",
                        uom=None,
                    )
                    calc_sensors.append(calc_sensor)
                    hass.data[DATA_UTILITY][entry_id][DATA_TARIFF_SENSORS].append(
                        calc_sensor
                    )

            else:
                # Add sensors for each tariff
                for tariff in tariffs:
                    meter_sensor = UtilityMeterSensor(
                        calibrate_calc_value=(
                            calibrate_calc_value
                            if calibrate_calc_apply == meter
                            else Decimal(0)
                        ),
                        calibrate_value=(
                            calibrate_value if calibrate_apply == meter else Decimal(0)
                        ),
                        cron_pattern=cron_pattern,
                        delta_values=delta_values,
                        device_info=device_info,
                        meter_offset=meter_offset,
                        meter_type=meter,
                        name=f"{name} {METER_NAME_TYPES[meter]} {tariff}",
                        net_consumption=net_consumption,
                        parent_meter=entry_id,
                        periodically_resetting=periodically_resetting,
                        sensor_always_available=sensor_always_available,
                        source_calc_entity=source_calc_entity_id,
                        source_calc_multiplier=source_calc_multiplier,
                        source_entity=source_entity_id,
                        tariff_entity=tariff_entity,
                        tariff=tariff,
                        unique_id=f"{entry_id}_{METER_NAME_TYPES[meter]}_{tariff}",
                    )
                    meters.append(meter_sensor)
                    hass.data[DATA_UTILITY][entry_id][DATA_TARIFF_SENSORS].append(
                        meter_sensor
                    )
                    if create_calc_sensor:
                        # Create a calculated sensor for the tariff consumption
                        calc_sensor = UtilityMeterCalculatedSensor(
                            attribute=ATTR_CALC_CURRENT_VALUE,
                            calibrate_calc_value=(
                                calibrate_calc_value
                                if calibrate_calc_apply == meter
                                else Decimal(0)
                            ),
                            cron_pattern=cron_pattern,
                            device_class=None,
                            device_info=device_info,
                            entity_id=(
                                f"sensor.{clean_string(name)}_{clean_string(METER_NAME_TYPES[meter])}_{clean_string(tariff)}"
                            ),
                            hass=hass,
                            icon=None,
                            meter_type=meter,
                            name=f"{name} {METER_NAME_TYPES[meter]} {tariff} Calculated",
                            source_calc_entity=source_calc_entity_id,
                            source_entity=source_entity_id,
                            state_class=None,
                            tariff=tariff,
                            unique_id=f"{name} {METER_NAME_TYPES[meter]} {tariff} Calculated",
                            uom=None,
                        )
                        calc_sensors.append(calc_sensor)
                        hass.data[DATA_UTILITY][entry_id][DATA_TARIFF_SENSORS].append(
                            calc_sensor
                        )

    else: # noqa: PLR5501
        if not tariffs:
            # Add single sensor, not gated by a tariff selector
            meter_sensor = UtilityMeterSensor(
                calibrate_calc_value=calibrate_calc_value,
                calibrate_value=calibrate_value,
                cron_pattern=cron_pattern,
                delta_values=delta_values,
                device_info=device_info,
                meter_offset=meter_offset,
                meter_type=meter_type,
                name=name,
                net_consumption=net_consumption,
                parent_meter=entry_id,
                periodically_resetting=periodically_resetting,
                sensor_always_available=sensor_always_available,
                source_calc_entity=source_calc_entity_id,
                source_calc_multiplier=source_calc_multiplier,
                source_entity=source_entity_id,
                tariff_entity=tariff_entity,
                tariff=None,
                unique_id=entry_id,
            )
            meters.append(meter_sensor)
            hass.data[DATA_UTILITY][entry_id][DATA_TARIFF_SENSORS].append(meter_sensor)

            if create_calc_sensor:
                # Create a calculated sensor for the total consumption
                calc_sensor = UtilityMeterCalculatedSensor(
                    attribute=ATTR_CALC_CURRENT_VALUE,
                    calibrate_calc_value=calibrate_calc_value,
                    cron_pattern=cron_pattern,
                    device_class=None,
                    device_info=device_info,
                    entity_id=f"sensor.{clean_string(name)}",
                    hass=hass,
                    icon=None,
                    meter_type=meter_type,
                    name=f"{name} Calculated",
                    source_calc_entity=source_calc_entity_id,
                    source_entity=source_entity_id,
                    state_class=None,
                    tariff=None,
                    unique_id=f"{name} Calculated",
                    uom=None,
                )
                calc_sensors.append(calc_sensor)
                hass.data[DATA_UTILITY][entry_id][DATA_TARIFF_SENSORS].append(
                    calc_sensor
                )

        else:
            # Add sensors for each tariff
            for tariff in tariffs:
                meter_sensor = UtilityMeterSensor(
                    calibrate_calc_value=calibrate_calc_value,
                    calibrate_value=calibrate_value,
                    cron_pattern=cron_pattern,
                    delta_values=delta_values,
                    device_info=device_info,
                    meter_offset=meter_offset,
                    meter_type=meter_type,
                    name=f"{name} {tariff}",
                    net_consumption=net_consumption,
                    parent_meter=entry_id,
                    periodically_resetting=periodically_resetting,
                    sensor_always_available=sensor_always_available,
                    source_calc_entity=source_calc_entity_id,
                    source_calc_multiplier=source_calc_multiplier,
                    source_entity=source_entity_id,
                    tariff_entity=tariff_entity,
                    tariff=tariff,
                    unique_id=f"{entry_id}_{tariff}",
                )
                meters.append(meter_sensor)
                hass.data[DATA_UTILITY][entry_id][DATA_TARIFF_SENSORS].append(
                    meter_sensor
                )
                if create_calc_sensor:
                    # Create a calculated sensor for the tariff consumption
                    calc_sensor = UtilityMeterCalculatedSensor(
                        attribute=ATTR_CALC_CURRENT_VALUE,
                        calibrate_calc_value=calibrate_calc_value,
                        cron_pattern=cron_pattern,
                        device_class=None,  # device_class,
                        device_info=device_info,
                        entity_id=f"sensor.{clean_string(name)}_{clean_string(tariff)}",
                        hass=hass,
                        icon=None,
                        meter_type=meter_type,
                        name=f"{name} {tariff} Calculated",
                        source_calc_entity=source_calc_entity_id,
                        source_entity=source_entity_id,
                        state_class=None,
                        tariff=tariff,
                        unique_id=f"{name} {tariff} Calculated",
                        uom=None,
                    )
                    calc_sensors.append(calc_sensor)
                    hass.data[DATA_UTILITY][entry_id][DATA_TARIFF_SENSORS].append(
                        calc_sensor
                    )

    async_add_entities(meters)
    async_add_entities(calc_sensors)

    platform = entity_platform.async_get_current_platform()

    platform.async_register_entity_service(
        SERVICE_CALIBRATE_METER,
        {vol.Required(ATTR_VALUE): validate_is_number},
        "async_calibrate",
    )


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the utility meter sensor."""
    if discovery_info is None:
        _LOGGER.error(
            "This platform is not available to configure "
            "from 'sensor:' in configuration.yaml"
        )
        return

    meters = []
    for conf in discovery_info.values():
        meter = conf[CONF_METER]
        conf_meter_source = hass.data[DATA_UTILITY][meter][CONF_SOURCE_SENSOR]
        conf_meter_calc_multiplier = conf[CONF_SOURCE_CALC_MULTIPLIER]
        conf_meter_calc_source = hass.data[DATA_UTILITY][meter][CONF_SOURCE_CALC_SENSOR]
        conf_meter_calibration_value = conf[CONF_CONFIG_CALIBRATE_VALUE]
        conf_meter_calibration_calc_value = conf[CONF_CONFIG_CALIBRATE_CALC_VALUE]
        conf_meter_unique_id = hass.data[DATA_UTILITY][meter].get(CONF_UNIQUE_ID)
        conf_sensor_tariff = conf.get(CONF_TARIFF, SINGLE_TARIFF)
        conf_sensor_unique_id = (
            f"{conf_meter_unique_id}_{conf_sensor_tariff}"
            if conf_meter_unique_id
            else None
        )
        conf_meter_name = hass.data[DATA_UTILITY][meter].get(CONF_NAME, meter)
        conf_sensor_tariff = conf.get(CONF_TARIFF)

        suggested_entity_id = None
        if conf_sensor_tariff:
            conf_sensor_name = f"{conf_meter_name} {conf_sensor_tariff}"
            slug = slugify(f"{meter} {conf_sensor_tariff}")
            suggested_entity_id = f"sensor.{slug}"
        else:
            conf_sensor_name = conf_meter_name

        conf_meter_type = hass.data[DATA_UTILITY][meter].get(CONF_METER_TYPE)
        conf_meter_offset = hass.data[DATA_UTILITY][meter][CONF_METER_OFFSET]
        conf_meter_delta_values = hass.data[DATA_UTILITY][meter][
            CONF_METER_DELTA_VALUES
        ]
        conf_meter_net_consumption = hass.data[DATA_UTILITY][meter][
            CONF_METER_NET_CONSUMPTION
        ]
        conf_meter_periodically_resetting = hass.data[DATA_UTILITY][meter][
            CONF_METER_PERIODICALLY_RESETTING
        ]
        conf_meter_tariff_entity = hass.data[DATA_UTILITY][meter].get(
            CONF_TARIFF_ENTITY
        )
        conf_cron_pattern = hass.data[DATA_UTILITY][meter].get(CONF_CRON_PATTERN)
        conf_sensor_always_available = hass.data[DATA_UTILITY][meter][
            CONF_SENSOR_ALWAYS_AVAILABLE
        ]
        meter_sensor = UtilityMeterSensor(
            cron_pattern=conf_cron_pattern,
            delta_values=conf_meter_delta_values,
            meter_offset=conf_meter_offset,
            meter_type=conf_meter_type,
            name=conf_sensor_name,
            net_consumption=conf_meter_net_consumption,
            parent_meter=meter,
            periodically_resetting=conf_meter_periodically_resetting,
            source_entity=conf_meter_source,
            source_calc_entity=conf_meter_calc_source,
            source_calc_multiplier=conf_meter_calc_multiplier,
            calibrate_value=conf_meter_calibration_value,
            calibrate_calc_value=conf_meter_calibration_calc_value,
            tariff_entity=conf_meter_tariff_entity,
            tariff=conf_sensor_tariff,
            unique_id=conf_sensor_unique_id,
            suggested_entity_id=suggested_entity_id,
            sensor_always_available=conf_sensor_always_available,
        )
        meters.append(meter_sensor)

        hass.data[DATA_UTILITY][meter][DATA_TARIFF_SENSORS].append(meter_sensor)

    async_add_entities(meters)

    platform = entity_platform.async_get_current_platform()

    platform.async_register_entity_service(
        SERVICE_CALIBRATE_METER,
        {vol.Required(ATTR_VALUE): validate_is_number},
        "async_calibrate",
    )


@dataclass
class UtilitySensorExtraStoredData(SensorExtraStoredData):
    """Object to hold extra stored data."""

    last_period: Decimal
    last_reset: datetime | None
    last_valid_state: Decimal | None
    status: str
    input_device_class: SensorDeviceClass | None
    calculated_current_value: Decimal | None
    calculated_last_value: Decimal | None


    def as_dict(self) -> dict[str, Any]:
        """Return a dict representation of the utility sensor data."""
        data = super().as_dict()
        data["last_period"] = str(self.last_period)
        if isinstance(self.last_reset, (datetime)):
            data["last_reset"] = self.last_reset.isoformat()
        data["last_valid_state"] = (
            str(self.last_valid_state) if self.last_valid_state else None
        )
        data["status"] = self.status
        data["input_device_class"] = str(self.input_device_class)
        data["calculated_current_value"] = str(self.calculated_current_value)
        data["calculated_last_value"] = str(self.calculated_last_value)

        return data

    @classmethod
    def from_dict(cls, restored: dict[str, Any]) -> Self | None:
        """Initialize a stored sensor state from a dict."""
        extra = SensorExtraStoredData.from_dict(restored)
        if extra is None:
            return None

        try:
            last_period: Decimal = Decimal(restored["last_period"])
            last_reset: datetime | None = dt_util.parse_datetime(restored["last_reset"])
            last_valid_state: Decimal | None = (
                Decimal(restored["last_valid_state"])
                if restored.get("last_valid_state")
                else None
            )
            status: str = restored["status"]
            input_device_class = try_parse_enum(
                SensorDeviceClass, restored.get("input_device_class")
            )
            calculated_current_value: Decimal | None = (
                Decimal(restored["calculated_current_value"])
                if restored.get("calculated_current_value")
                else None
            )
            calculated_last_value: Decimal | None = (
                Decimal(restored["calculated_last_value"])
                if restored.get("calculated_last_value")
                else None
            )

        except (KeyError, InvalidOperation):
            # last_period is corrupted
            return None

        return cls(
            extra.native_value,
            extra.native_unit_of_measurement,
            last_period,
            last_reset,
            last_valid_state,
            status,
            input_device_class,
            calculated_current_value,
            calculated_last_value,
        )


class UtilityMeterSensor(RestoreSensor):
    """Representation of an utility meter sensor."""

    _attr_translation_key = "utility_meter"
    _attr_should_poll = False
    _unrecorded_attributes = frozenset(
        {
            ATTR_NEXT_RESET,
            CONF_CRON_PATTERN,
            CONF_METER_TYPE,
            ATTR_SOURCE_ID,
            CONF_SOURCE_CALC_SENSOR,
            CONF_SOURCE_CALC_MULTIPLIER,
            CONF_CONFIG_CALIBRATE_CALC_VALUE,
            CONF_CONFIG_CALIBRATE_VALUE,
        }
    )

    def __init__(
        self,
        *,
        cron_pattern,
        delta_values,
        meter_offset,
        meter_type,
        name,
        net_consumption,
        parent_meter,
        periodically_resetting,
        source_entity,
        source_calc_entity,
        source_calc_multiplier,
        calibrate_value,
        calibrate_calc_value,
        tariff_entity,
        tariff,
        unique_id,
        sensor_always_available,
        suggested_entity_id=None,
        device_info=None,
    ):
        """Initialize the Utility Meter sensor."""
        self._attr_unique_id = unique_id
        self._attr_device_info = device_info
        self.entity_id = suggested_entity_id
        self._parent_meter = parent_meter
        self._sensor_source_id = source_entity
        self._sensor_calc_source_id = source_calc_entity
        self._last_period = Decimal(0)
        self._last_reset = dt_util.utcnow()
        self._last_valid_state = None
        self._collecting = None
        self._attr_name = name
        self._input_device_class = None
        self._attr_native_unit_of_measurement = None
        self._attr_calculated_current_value = Decimal(0)
        self._attr_calculated_last_value = Decimal(0)
        self._attr_multiplier = source_calc_multiplier or Decimal(1)
        self._period = meter_type
        if meter_type is not None:
            # We convert the period and offset into a cron pattern
            self._cron_pattern = PERIOD2CRON[meter_type].format(
                minute=meter_offset["minutes"],
                hour=meter_offset["hours"],
                day=meter_offset["days"],
            )
            _LOGGER.debug("CRON pattern TYPE: %s", self._cron_pattern)
        else:
            self._cron_pattern = cron_pattern
            _LOGGER.debug("CRON pattern CRON: %s", self._cron_pattern)
        self._sensor_always_available = sensor_always_available
        self._sensor_delta_values = delta_values
        self._sensor_net_consumption = net_consumption
        self._sensor_periodically_resetting = periodically_resetting
        self._calibrate_value = Decimal(calibrate_value) or Decimal(0)
        self._calibrate_calc_value = calibrate_calc_value or Decimal(0)
        self._tariff = tariff
        self._tariff_entity = tariff_entity
        self._next_reset = None
        self._current_tz = None
        self._config_scheduler()

    def _config_scheduler(self):
        self.scheduler = (
            CronSim(
                self._cron_pattern,
                dt_util.now(
                    dt_util.get_default_time_zone()
                ),
            )
            if self._cron_pattern
            else None
        )

    def start(self, attributes: Mapping[str, Any]) -> None:
        """Initialize unit and state upon source initial update."""
        self._input_device_class = attributes.get(ATTR_DEVICE_CLASS)
        self._attr_native_unit_of_measurement = attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        self._attr_native_value = Decimal(self._calibrate_value)
        self._attr_calculated_current_value = Decimal(
            self._calibrate_calc_value
        )
        self.async_write_ha_state()

    @staticmethod
    def _validate_state(state: State | None) -> Decimal | None:
        """Parse the state as a Decimal if available. Throws DecimalException if not a number."""
        try:
            return (
                None
                if state is None or state.state in [STATE_UNAVAILABLE, STATE_UNKNOWN]
                else Decimal(state.state)
            )
        except DecimalException:
            return None

    def calculate_adjustment(
        self, old_state: State | None, new_state: State
    ) -> Decimal | None:
        """Calculate the adjustment based on the old and new state."""

        # First check if the new_state is valid (see discussion in PR #88446)
        if (new_state_val := self._validate_state(new_state)) is None:
            _LOGGER.warning("Invalid state %s", new_state.state)
            return None

        if self._sensor_delta_values:
            return new_state_val

        if (
            not self._sensor_periodically_resetting
            and self._last_valid_state is not None
        ):  # Fallback to old_state if sensor is periodically resetting but last_valid_state is None
            return new_state_val - self._last_valid_state

        if (old_state_val := self._validate_state(old_state)) is not None:
            return new_state_val - old_state_val

        _LOGGER.debug(
            "%s received an invalid state change coming from %s (%s > %s)",
            self.name,
            self._sensor_source_id,
            old_state.state if old_state else None,
            new_state_val,
        )
        return None

    @callback
    def async_reading(self, event: Event[EventStateChangedData]) -> None:
        """Handle the sensor state changes."""
        if (
            source_state := self.hass.states.get(self._sensor_source_id)
        ) is None or source_state.state == STATE_UNAVAILABLE:
            if not self._sensor_always_available:
                self._attr_available = False
                self.async_write_ha_state()
            return

        old_state = event.data["old_state"]
        new_state = event.data["new_state"]
        if new_state is None:
            return
        new_state_attributes: Mapping[str, Any] = new_state.attributes or {}

        # First check if the new_state is valid (see discussion in PR #88446)
        if (new_state_val := self._validate_state(new_state)) is None:
            _LOGGER.warning(
                "%s received an invalid new state from %s : %s",
                self.name,
                self._sensor_source_id,
                new_state.state,
            )
            return

        if self.native_value is None:
            _LOGGER.debug("selfHassDATA: %s",self.hass.data[DATA_UTILITY][self._parent_meter][
                DATA_TARIFF_SENSORS
            ])
            # First state update initializes the utility_meter sensors
            for sensor in self.hass.data[DATA_UTILITY][self._parent_meter][
                DATA_TARIFF_SENSORS
            ]:
                sensor.start(new_state_attributes)
                if self.native_unit_of_measurement is None:
                    _LOGGER.warning(
                        "Source sensor %s has no unit of measurement. Please %s",
                        self._sensor_source_id,
                        _suggest_report_issue(self.hass, self._sensor_source_id),
                    )

        if (
            adjustment := self.calculate_adjustment(old_state, new_state)
        ) is not None and (self._sensor_net_consumption or adjustment >= 0):
            # If net_consumption is off, the adjustment must be non-negative
            _LOGGER.debug("%s: Adjustment Check:  %s : %s", self.name, adjustment, self._tariff)
            self._attr_native_value += Decimal(adjustment)  # type: ignore[operator]

            if (
                self._sensor_calc_source_id is not None
                and (
                    source_calc_state := self.hass.states.get(
                        self._sensor_calc_source_id
                    )
                )
                and source_calc_state.state not in [STATE_UNAVAILABLE, STATE_UNKNOWN]
            ):
                try:
                    self._attr_calculated_current_value += round(
                        (
                            Decimal(source_calc_state.state)
                            * Decimal(adjustment)
                            * Decimal(self._attr_multiplier)
                        ),
                        PRECISION,
                    )
                except (DecimalException, InvalidOperation) as err:
                    _LOGGER.error(
                        "Error while parsing value %s from sensor %s: %s",
                        source_calc_state.state,
                        self._sensor_calc_source_id,
                        err,
                    )
                    self._attr_calculated_current_value = Decimal(0)
        self._input_device_class = new_state_attributes.get(ATTR_DEVICE_CLASS)
        self._attr_native_unit_of_measurement = new_state_attributes.get(
            ATTR_UNIT_OF_MEASUREMENT
        )
        self._last_valid_state = new_state_val
        self.async_write_ha_state()

    @callback
    def async_tariff_change(self, event: Event[EventStateChangedData]) -> None:
        """Handle tariff changes."""
        if (new_state := event.data["new_state"]) is None:
            return

        self._change_status(new_state.state)

    def _change_status(self, tariff: str) -> None:
        if self._tariff == tariff:
            self._collecting = async_track_state_change_event(
                self.hass, [self._sensor_source_id], self.async_reading
            )
        else:
            if self._collecting:
                self._collecting()
            self._collecting = None

        # Reset the last_valid_state during state change because if
        # the last state before the tariff change was invalid,
        # there is no way to know how much "adjustment" counts for
        # which tariff. Therefore, we set the last_valid_state
        # to None and let the fallback mechanism handle the case that the old state was valid
        self._last_valid_state = None

        _LOGGER.debug(
            "%s - %s - source <%s>",
            self.name,
            COLLECTING if self._collecting is not None else PAUSED,
            self._sensor_source_id,
        )

        self.async_write_ha_state()

    async def _program_reset(self):
        """Program the reset of the utility meter."""
        if self.scheduler:
            self._next_reset = next(self.scheduler)

            _LOGGER.debug("Next reset of %s is %s", self.entity_id, self._next_reset)
            self.async_on_remove(
                async_track_point_in_time(
                    self.hass,
                    self._async_reset_meter,
                    self._next_reset,
                )
            )
            self.async_write_ha_state()

    async def _async_reset_meter(self, event):
        """Reset the utility meter status."""

        await self.async_reset_meter(self._tariff_entity)

        await self._program_reset()

    async def async_reset_meter(self, entity_id):
        """Reset meter."""
        if self._tariff_entity is not None and self._tariff_entity != entity_id:
            return
        if (
            self._tariff_entity is None
            and entity_id is not None
            and self.entity_id != entity_id
        ):
            return
        _LOGGER.debug("Reset utility meter <%s>", self.entity_id)
        self._last_reset = dt_util.utcnow()
        self._last_period = (
            Decimal(self.native_value)  # noqa: PGH003 # type: ignore
            if self.native_value
            else Decimal(0)
        )
        # update Calculated value if we have a calculation sensor
        if self._sensor_calc_source_id is not None:
            self._attr_calculated_last_value = self._attr_calculated_current_value
        self._attr_calculated_current_value = Decimal(self._calibrate_calc_value)
        self._attr_native_value = Decimal(self._calibrate_value)
        self.async_write_ha_state()

    async def async_calibrate(self, value):
        """Calibrate the Utility Meter with a given value."""
        _LOGGER.debug("Calibrate %s = %s type(%s)", self.name, value, type(value))
        self._attr_native_value = Decimal(str(value))
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Handle entity which will be added."""
        await super().async_added_to_hass()

        # track current timezone in case it changes
        # and we need to reconfigure the scheduler
        self._current_tz = self.hass.config.time_zone

        await self._program_reset()

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_RESET_METER, self.async_reset_meter
            )
        )

        if (last_sensor_data := await self.async_get_last_sensor_data()) is not None:
            self._attr_native_value = (
                None
                if last_sensor_data.native_value is None
                else Decimal(last_sensor_data.native_value)
            )
            self._input_device_class = last_sensor_data.input_device_class
            self._attr_native_unit_of_measurement = (
                last_sensor_data.native_unit_of_measurement
            )
            self._last_period = last_sensor_data.last_period
            self._last_reset = last_sensor_data.last_reset
            self._last_valid_state = last_sensor_data.last_valid_state
            if last_sensor_data.status == COLLECTING:
                # Null lambda to allow cancelling the collection on tariff change
                self._collecting = lambda: None
            self._attr_calculated_current_value = (
                Decimal(0)
                if last_sensor_data.calculated_current_value is None
                else Decimal(last_sensor_data.calculated_current_value)
            )
            self._attr_calculated_last_value = (
                Decimal(0)
                if last_sensor_data.calculated_last_value is None
                else Decimal(last_sensor_data.calculated_last_value)
            )

        @callback
        def async_source_tracking(event):
            """Wait for source to be ready, then start meter."""
            if str(self._tariff).lower() != TOTAL_TARIFF and self._tariff_entity is not None:
                # If the tariff is not TOTAL_TARIFF, we need to track the tariff entity
                # and change the status of the utility meter sensor accordingly
                #if self._tariff_entity is not None:
                _LOGGER.debug(
                    "<%s> tracks utility meter %s", self.name, self._tariff_entity
                )
                self.async_on_remove(
                    async_track_state_change_event(
                        self.hass, [self._tariff_entity], self.async_tariff_change
                    )
                )

                tariff_entity_state = self.hass.states.get(self._tariff_entity)
                if not tariff_entity_state:
                    # The utility meter is not yet added
                    return

                self._change_status(tariff_entity_state.state)
                return

            _LOGGER.debug(
                "<%s> collecting %s from %s",
                self.name,
                self.native_unit_of_measurement,
                self._sensor_source_id,
            )
            self._collecting = async_track_state_change_event(
                self.hass, [self._sensor_source_id], self.async_reading
            )

        self.async_on_remove(async_at_started(self.hass, async_source_tracking))

        async def async_track_time_zone(event):
            """Reconfigure Scheduler after time zone changes."""

            if self._current_tz != self.hass.config.time_zone:
                self._current_tz = self.hass.config.time_zone

                self._config_scheduler()
                await self._program_reset()

        self.async_on_remove(
            self.hass.bus.async_listen(EVENT_CORE_CONFIG_UPDATE, async_track_time_zone)
        )

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity will be removed from hass."""
        if self._collecting:
            self._collecting()
        self._collecting = None

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        if self._input_device_class is not None:
            return self._input_device_class
        if (
            self.native_unit_of_measurement
            in DEVICE_CLASS_UNITS[SensorDeviceClass.ENERGY]
        ):
            return SensorDeviceClass.ENERGY
        return None

    @property
    def state_class(self):
        """Return the device class of the sensor."""
        return (
            SensorStateClass.TOTAL
            if self._sensor_net_consumption
            else SensorStateClass.TOTAL_INCREASING
        )

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        state_attr = {
            ATTR_STATUS: PAUSED if self._collecting is None else COLLECTING,
            ATTR_LAST_PERIOD: str(self._last_period),
            ATTR_LAST_VALID_STATE: str(self._last_valid_state),
        }
        if self._tariff is not None:
            state_attr[ATTR_TARIFF] = self._tariff
        if last_reset := self._last_reset:
            state_attr[ATTR_LAST_RESET] = last_reset.isoformat()
        if self._next_reset is not None:
            state_attr[ATTR_NEXT_RESET] = self._next_reset.isoformat()
        if self._cron_pattern is not None:
            state_attr[CONF_CRON_PATTERN] = self._cron_pattern
        if self._period is not None:
            state_attr[ATTR_PREDEFINED_CYCLE] = METER_NAME_TYPES[self._period]
        if self._calibrate_value != 0 and str(self._tariff).lower() in [
            SINGLE_TARIFF,
            TOTAL_TARIFF,
        ]:
            state_attr[CONF_CONFIG_CALIBRATE_VALUE] = str(self._calibrate_value)
        if self._sensor_source_id is not None:
            state_attr[ATTR_SOURCE_ID] = self._sensor_source_id
        if self._sensor_calc_source_id is not None:
            state_attr[CONF_SOURCE_CALC_SENSOR] = self._sensor_calc_source_id
            state_attr[ATTR_CALC_CURRENT_VALUE] = str(
                round(self._attr_calculated_current_value, PRECISION)
            )
            state_attr[ATTR_CALC_LAST_VALUE] = str(
                round(self._attr_calculated_last_value, PRECISION)
            )
            state_attr[CONF_SOURCE_CALC_MULTIPLIER] = str(self._attr_multiplier)
            if self._calibrate_calc_value != 0 and str(self._tariff).lower() in [
                SINGLE_TARIFF,
                TOTAL_TARIFF,
            ]:
                state_attr[CONF_CONFIG_CALIBRATE_CALC_VALUE] = str(
                    self._calibrate_calc_value
                )
        return state_attr

    @property
    def extra_restore_state_data(self) -> UtilitySensorExtraStoredData:
        """Return sensor specific state data to be restored."""
        return UtilitySensorExtraStoredData(
            self.native_value,
            self.native_unit_of_measurement,
            self._last_period,
            self._last_reset,
            self._last_valid_state,
            PAUSED if self._collecting is None else COLLECTING,
            self._input_device_class,
            self._attr_calculated_current_value,
            self._attr_calculated_last_value,
        )

    async def async_get_last_sensor_data(self) -> UtilitySensorExtraStoredData | None:
        """Restore Utility Meter Sensor Extra Stored Data."""
        if (restored_last_extra_data := await self.async_get_last_extra_data()) is None:
            return None

        return UtilitySensorExtraStoredData.from_dict(
            restored_last_extra_data.as_dict()
        )

class UtilityMeterCalculatedSensor(RestoreSensor):
    """Representation of an Seperate Calculated sensor."""

    _attr_should_poll = False
    _attr_collecting_status = None
    _unrecorded_attributes = frozenset(
        {
            ATTR_NEXT_RESET,
            ATTR_SOURCE_ID,
            CONF_CONFIG_CALIBRATE_CALC_VALUE,
            CONF_CONFIG_CALIBRATE_VALUE,
            CONF_CRON_PATTERN,
            CONF_METER_TYPE,
            CONF_SOURCE_CALC_MULTIPLIER,
            CONF_SOURCE_CALC_SENSOR,
            ATTR_LINKED_METER,
        }
    )

    def __init__(
        self,
        hass: HomeAssistant,
        attribute: str,
        calibrate_calc_value: Decimal,
        cron_pattern: str | None,
        device_class: SensorDeviceClass | None,
        device_info,
        entity_id: str,
        icon: str | None,
        meter_type: str | None,
        name: str,
        source_calc_entity: str | None,
        source_entity: str | None,
        state_class: SensorStateClass | None,
        tariff: str | None,
        unique_id: str | None,
        uom: str | None,

    ) -> None:
        """Initialize the sensor."""
        self._attr_collecting_status = None
        self._attr_device_class = (
            SensorDeviceClass.MONETARY if device_class is None else device_class
        )
        self._attr_device_info = device_info
        self._attr_icon = "mdi:currency-usd" if icon is None else icon
        self._attr_name = name
        self._attr_native_unit_of_measurement = CURRENCY_DOLLAR if uom is None else uom
        self._attr_suggested_display_precision = PRECISION
        self._attr_state_class = (
            SensorStateClass.TOTAL if state_class is None else state_class
        )
        self._attr_unique_id = unique_id
        self._attribute = attribute
        self._calibrate_calc_value = calibrate_calc_value or Decimal(0)
        self._cron_pattern = cron_pattern
        self._entity_id = entity_id
        self._has_logged = False
        self._period = meter_type
        self._sensor_source_id = source_entity
        self._source_calc_entity = source_calc_entity
        self._tariff = tariff if tariff is not None else SINGLE_TARIFF

    def start(self, attributes: Mapping[str, Any]) -> None:
        """Initialize unit and state upon source initial update."""
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Handle added to Hass."""
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, self._entity_id, self._async_attribute_sensor_state_listener
            )
        )
        self.async_on_remove(
            async_track_state_report_event(
                self.hass, self._entity_id, self._async_attribute_sensor_state_listener
            )
        )

        # Replay current state of source entities
        state = self.hass.states.get(self._entity_id)
        state_event = Event("", {"entity_id": self._entity_id, "new_state": state})
        self._async_attribute_sensor_state_listener(state_event, update_state=False)
        _LOGGER.debug("Complete Async added to Hass: %s", state)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes of the sensor."""

        state_attr = {
            ATTR_LINKED_METER: self._entity_id,
            ATTR_STATUS: (
                self._attr_collecting_status
                if self._attr_collecting_status is not None
                else "unknown"
            ),
        }
        if self._period is not None:
            state_attr[ATTR_PREDEFINED_CYCLE] = METER_NAME_TYPES[self._period]
        elif self._cron_pattern is not None:
            state_attr[CONF_CRON_PATTERN] = self._cron_pattern
        if self._sensor_source_id is not None:
            state_attr[ATTR_SOURCE_ID] = self._sensor_source_id
        if self._source_calc_entity is not None:
            state_attr[CONF_SOURCE_CALC_SENSOR] = self._source_calc_entity
            if self._calibrate_calc_value != 0 and str(self._tariff).lower() in [
                SINGLE_TARIFF,
                TOTAL_TARIFF,
            ]:
                state_attr[CONF_CONFIG_CALIBRATE_CALC_VALUE] = str(
                    self._calibrate_calc_value
                )
        return state_attr

    @callback
    def _async_attribute_sensor_state_listener(
        self, event: Event, update_state: bool = True
    ) -> None:
        """Handle the sensor state changes."""
        new_state = event.data["new_state"]
        _LOGGER.debug("Received new state: %s", new_state)

        self._attr_native_value = None
        if (
            new_state is None
            or new_state.state is None
            or new_state.state in [STATE_UNAVAILABLE, STATE_UNKNOWN]
            or hasattr(new_state, "attributes") is False
        ):
            if not update_state:
                _LOGGER.debug("Ignoring state update")
            else:
                _LOGGER.debug(
                    "State update for %s is None or unavailable, setting to STATE_UNAVAILABLE",
                    self._entity_id,
                )
                #self._attr_native_value = STATE_UNAVAILABLE #Decimal(0)
                self._attr_collecting_status = STATE_UNAVAILABLE
                self.async_write_ha_state()
            return
        if hasattr(new_state, "attributes"):
            if self._attribute not in new_state.attributes:
                if not self._has_logged:
                    _LOGGER.error(
                        "Attribute (%s) not found in Attributes for entity %s, Dictionary: %s",
                        self._attribute,
                        self._entity_id,
                        new_state,
                    )
                self._has_logged = True
                self._attr_native_value = STATE_UNAVAILABLE
                self.async_write_ha_state()
                return

        _LOGGER.debug("state update step 1")
        _LOGGER.debug("state update step 1 %s", self._attribute)
        _LOGGER.debug("state update step 1a %s", new_state.state)
        _LOGGER.debug("state update step 1b %s", new_state.attributes)

        self._has_logged = False
        if self._attribute in new_state.attributes:
            _LOGGER.debug("State attributes: %s", new_state.attributes)

            value = new_state.attributes[self._attribute]
            if isinstance(value, str):
                try:
                    value = Decimal(value)
                except (InvalidOperation, ValueError):
                    _LOGGER.error(
                        "Invalid value for attribute (%s) in entity %s: %s",
                        self._attribute,
                        self._entity_id,
                        value,
                    )
                    self._attr_native_value = STATE_UNAVAILABLE
                    self.async_write_ha_state()
                    return
            self._attr_native_value = value
            _LOGGER.debug(
                "Setting attribute (%s) value: %s",
                self._attribute,
                self._attr_native_value,
            )
        if "status" in new_state.attributes:
            self._attr_collecting_status = new_state.attributes["status"]
        _LOGGER.debug("state update step 3")
        self.async_write_ha_state()
        return
