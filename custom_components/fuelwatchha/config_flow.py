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
from .const import CONF_POSTCODE, CONF_PRODUCT, CONF_SUBURB, DOMAIN, FUEL_PRODUCTS


class FuelWatchHAConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure the cheapest station for a postcode and fuel type."""

    VERSION = 1

    def __init__(self) -> None:
        self._postcode = ""
        self._product = 1
        self._station: dict[str, Any] | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Select postcode and fuel type."""
        errors: dict[str, str] = {}
        if user_input is not None:
            postcode = str(user_input[CONF_POSTCODE]).strip()
            product = int(user_input[CONF_PRODUCT])
            if not postcode.isdigit() or len(postcode) != 4:
                errors[CONF_POSTCODE] = "invalid_postcode"
            else:
                session: aiohttp.ClientSession = async_get_clientsession(self.hass)
                stations = await fetch_stations(session, "", product, "today")
                matching = [s for s in stations if str(s.get("postcode", "")).zfill(4) == postcode]
                if not matching:
                    errors[CONF_POSTCODE] = "no_stations_found"
                else:
                    self._postcode = postcode
                    self._product = product
                    self._station = matching[0]
                    await self.async_set_unique_id(f"{postcode}_{product}")
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=f"{postcode} — {FUEL_PRODUCTS.get(product, str(product))}",
                        data={
                            CONF_POSTCODE: postcode,
                            CONF_PRODUCT: str(product),
                            CONF_SUBURB: "",
                        },
                    )

        product_options = [
            SelectOptionDict(value=str(k), label=v) for k, v in FUEL_PRODUCTS.items()
        ]
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_POSTCODE): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.TEXT)
                ),
                vol.Required(CONF_PRODUCT, default="1"): SelectSelector(
                    SelectSelectorConfig(options=product_options, mode=SelectSelectorMode.LIST)
                ),
            }),
            errors=errors,
        )
