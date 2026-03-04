"""FuelWatch HA integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import CONF_PRODUCT, CONF_STATION_TRADING_NAME, CONF_SUBURB, DOMAIN
from .coordinator import FuelWatchCoordinator

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up FuelWatch HA from a config entry."""
    coordinator = FuelWatchCoordinator(
        hass=hass,
        suburb=entry.data[CONF_SUBURB],
        product=int(entry.data[CONF_PRODUCT]),
        station_trading_name=entry.data.get(CONF_STATION_TRADING_NAME, ""),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
