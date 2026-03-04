"""Config flow for FuelWatch HA."""
from __future__ import annotations

from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import fetch_stations
from .const import (
    CONF_PRODUCT,
    CONF_STATION_TRADING_NAME,
    CONF_SUBURB,
    DOMAIN,
    FUEL_PRODUCTS,
)


class FuelWatchHAConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """FuelWatch HA config flow."""

    VERSION = 1

    def __init__(self) -> None:
        self._suburb: str = ""
        self._product: int = 1
        self._stations: list[dict] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 1 — suburb and fuel type."""
        errors: dict[str, str] = {}

        if user_input is not None:
            suburb = user_input[CONF_SUBURB].strip()
            product = int(user_input[CONF_PRODUCT])

            if not suburb:
                errors[CONF_SUBURB] = "suburb_required"
            else:
                session: aiohttp.ClientSession = async_get_clientsession(self.hass)
                stations = await fetch_stations(session, suburb, product, "today")

                if not stations:
                    errors[CONF_SUBURB] = "no_stations_found"
                else:
                    self._suburb = suburb
                    self._product = product
                    self._stations = stations
                    return await self.async_step_station()

        product_options = [
            SelectOptionDict(value=str(k), label=v)
            for k, v in FUEL_PRODUCTS.items()
        ]

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SUBURB): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.TEXT)
                    ),
                    vol.Required(CONF_PRODUCT, default="1"): SelectSelector(
                        SelectSelectorConfig(
                            options=product_options,
                            mode=SelectSelectorMode.LIST,
                        )
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_station(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 2 — select station."""
        if user_input is not None:
            index = int(user_input["station"])
            station = self._stations[index]
            trading_name: str = station.get("trading-name", station.get("brand", "Unknown"))
            product_label = FUEL_PRODUCTS.get(self._product, str(self._product))

            unique_id = (
                f"{self._suburb.lower()}_{self._product}"
                f"_{trading_name.lower().replace(' ', '_')}"
            )
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"{trading_name} — {product_label}",
                data={
                    CONF_SUBURB: self._suburb,
                    CONF_PRODUCT: str(self._product),
                    CONF_STATION_TRADING_NAME: trading_name,
                },
            )

        station_options = [
            SelectOptionDict(
                value=str(i),
                label=(
                    f"#{i + 1}  {s.get('trading-name', s.get('brand', f'Station {i+1}'))}"
                    f"  —  {s.get('address', '')}  ({s.get('price', '?')}¢)"
                ),
            )
            for i, s in enumerate(self._stations)
        ]

        return self.async_show_form(
            step_id="station",
            description_placeholders={
                "suburb": self._suburb,
                "product": FUEL_PRODUCTS.get(self._product, str(self._product)),
                "count": str(len(self._stations)),
            },
            data_schema=vol.Schema(
                {
                    vol.Required("station"): SelectSelector(
                        SelectSelectorConfig(
                            options=station_options,
                            mode=SelectSelectorMode.LIST,
                        )
                    ),
                }
            ),
            errors={},
        )
