"""Sensor platform for FuelWatch HA."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CURRENCY_CENT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_STATION_TRADING_NAME, DOMAIN, FUEL_PRODUCTS
from .coordinator import FuelWatchCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up FuelWatch HA sensors."""
    coordinator: FuelWatchCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            FuelPriceSensor(coordinator, entry, "today"),
            FuelPriceSensor(coordinator, entry, "tomorrow"),
            FuelTradingNameSensor(coordinator, entry),
        ]
    )


def _make_device_info(entry: ConfigEntry) -> DeviceInfo:
    """Build shared DeviceInfo for all sensors in an entry."""
    trading_name: str = entry.data.get(CONF_STATION_TRADING_NAME, "")
    product = int(entry.data.get("product", 1))
    suburb: str = entry.data.get("suburb", "")
    product_label = FUEL_PRODUCTS.get(product, str(product))

    return DeviceInfo(
        entry_type=DeviceEntryType.SERVICE,
        identifiers={(DOMAIN, entry.entry_id)},
        name=trading_name if trading_name else f"FuelWatch {suburb.title()} — {product_label}",
        manufacturer="FuelWatch WA",
        model=product_label,
        configuration_url="https://www.fuelwatch.wa.gov.au",
    )


class FuelWatchBaseSensor(CoordinatorEntity[FuelWatchCoordinator], SensorEntity):
    """Base sensor class."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: FuelWatchCoordinator,
        entry: ConfigEntry,
        name: str,
        unique_suffix: str,
    ) -> None:
        super().__init__(coordinator)
        self._attr_name = name
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_{unique_suffix}"
        self._attr_device_info = _make_device_info(entry)

    @property
    def available(self) -> bool:
        """Mark unavailable if coordinator data is missing for this sensor."""
        return super().available and self._get_value() is not None

    def _get_value(self) -> Any:
        raise NotImplementedError


class FuelPriceSensor(FuelWatchBaseSensor):
    """Price sensor for today or tomorrow."""

    _attr_native_unit_of_measurement = CURRENCY_CENT
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(
        self,
        coordinator: FuelWatchCoordinator,
        entry: ConfigEntry,
        day: str,
    ) -> None:
        super().__init__(
            coordinator,
            entry,
            name=f"Price ({day.capitalize()})",
            unique_suffix=f"price_{day}",
        )
        self._day = day

    def _get_value(self) -> float | None:
        station = (self.coordinator.data or {}).get(self._day)
        if station is None:
            return None
        try:
            return float(station["price"])
        except (KeyError, TypeError, ValueError):
            return None

    @property
    def native_value(self) -> float | None:
        return self._get_value()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        station = (self.coordinator.data or {}).get(self._day) or {}
        return {
            "suburb": self.coordinator.suburb,
            "fuel_type": FUEL_PRODUCTS.get(self.coordinator.product, str(self.coordinator.product)),
            "day": self._day,
            "station": station.get("trading-name"),
            "address": station.get("address"),
            "date": station.get("date"),
        }


class FuelTradingNameSensor(FuelWatchBaseSensor):
    """Trading name sensor — always reads from today's data."""

    def __init__(
        self,
        coordinator: FuelWatchCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(
            coordinator,
            entry,
            name="Trading Name",
            unique_suffix="trading_name",
        )

    def _get_value(self) -> str | None:
        station = (self.coordinator.data or {}).get("today")
        return station.get("trading-name") if station else None

    @property
    def native_value(self) -> str | None:
        return self._get_value()
