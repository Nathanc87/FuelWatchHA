"""DataUpdateCoordinator for FuelWatch HA."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_POSTCODE, DOMAIN, FUEL_PRODUCTS
from .api import fetch_stations

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(hours=1)


class FuelWatchCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch fuel prices and select the cheapest station in a postcode."""

    def __init__(
        self,
        hass: HomeAssistant,
        suburb: str,
        product: int,
        station_trading_name: str = "",
        postcode: str = "",
    ) -> None:
        self.suburb = suburb
        self.product = product
        self.station_trading_name = station_trading_name
        self.postcode = postcode
        self.is_postcode_mode = bool(postcode)

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{postcode or suburb}_{product}",
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch today/tomorrow, then select the cheapest matching station."""
        session: aiohttp.ClientSession = async_get_clientsession(self.hass)
        query_suburb = "" if self.is_postcode_mode else self.suburb
        try:
            today_stations, tomorrow_stations = await asyncio.gather(
                fetch_stations(session, query_suburb, self.product, "today"),
                fetch_stations(session, query_suburb, self.product, "tomorrow"),
            )
        except Exception as err:
            raise UpdateFailed(f"Error fetching FuelWatch data: {err}") from err

        product_label = FUEL_PRODUCTS.get(self.product, str(self.product))
        return {
            "today": self._find_station(today_stations, "today", product_label),
            "tomorrow": self._find_station(tomorrow_stations, "tomorrow", product_label),
        }

    def _find_station(
        self,
        stations: list[dict[str, Any]],
        day: str,
        product_label: str,
    ) -> dict[str, Any] | None:
        """Return the lowest priced station matching this entry."""
        if self.is_postcode_mode:
            postcode = self.postcode.zfill(4)
            matches = [
                station for station in stations
                if str(station.get("postcode", "")).zfill(4) == postcode
            ]
            return matches[0] if matches else None

        if not stations:
            _LOGGER.debug("FuelWatch HA: no %s results for %s %s", day, self.suburb, product_label)
            return None
        if self.station_trading_name:
            name_lower = self.station_trading_name.lower()
            for station in stations:
                if station.get("trading-name", "").lower() == name_lower:
                    return station
            _LOGGER.debug("FuelWatch HA: station '%s' not found in %s results", self.station_trading_name, day)
            return None
        return stations[0]
