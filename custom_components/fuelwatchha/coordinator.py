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

from .api import fetch_stations
from .const import DOMAIN, FUEL_PRODUCTS

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(hours=1)


class FuelWatchCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator that fetches today and tomorrow prices in one update cycle."""

    def __init__(
        self,
        hass: HomeAssistant,
        suburb: str,
        product: int,
        station_trading_name: str,
    ) -> None:
        self.suburb = suburb
        self.product = product
        self.station_trading_name = station_trading_name

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{suburb}_{product}_{station_trading_name}",
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch today and tomorrow data concurrently, return matched station data."""
        session: aiohttp.ClientSession = async_get_clientsession(self.hass)

        try:
            today_stations, tomorrow_stations = await asyncio.gather(
                fetch_stations(session, self.suburb, self.product, "today"),
                fetch_stations(session, self.suburb, self.product, "tomorrow"),
            )
        except Exception as err:
            raise UpdateFailed(f"Error fetching FuelWatch data: {err}") from err

        product_label = FUEL_PRODUCTS.get(self.product, str(self.product))

        today = self._find_station(today_stations, "today", product_label)
        tomorrow = self._find_station(tomorrow_stations, "tomorrow", product_label)

        return {
            "today": today,
            "tomorrow": tomorrow,
        }

    def _find_station(
        self,
        stations: list[dict[str, Any]],
        day: str,
        product_label: str,
    ) -> dict[str, Any] | None:
        """Find the tracked station in the results list."""
        if not stations:
            _LOGGER.debug(
                "FuelWatch HA: no %s results for %s %s",
                day, self.suburb, product_label,
            )
            return None

        if self.station_trading_name:
            name_lower = self.station_trading_name.lower()
            for station in stations:
                if station.get("trading-name", "").lower() == name_lower:
                    return station
            _LOGGER.debug(
                "FuelWatch HA: station '%s' not found in %s results for %s",
                self.station_trading_name, day, self.suburb,
            )
            return None

        # Fallback — return cheapest (should not normally reach here)
        return stations[0]
