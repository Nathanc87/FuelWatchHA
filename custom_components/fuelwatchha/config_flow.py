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
    """Configure the cheapest station by suburb or postcode."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Select suburb or postcode and fuel type."""
        errors: dict[str, str] = {}
        if user_input is not None:
            suburb = str(user_input.get(CONF_SUBURB, "")).strip()
            postcode = str(user_input.get(CONF_POSTCODE, "")).strip()
            product = int(user_input[CONF_PRODUCT])

            if not suburb and not postcode:
                errors["base"] = "location_required"
            elif postcode and (not postcode.isdigit() or len(postcode) != 4):
                errors[CONF_POSTCODE] = "invalid_postcode"
            else:
                session: aiohttp.ClientSession = async_get_clientsession(self.hass)
                # Prefer a suburb query when supplied. The API may omit postcode
                # metadata for stations, so suburb mode remains a reliable option.
                stations = await fetch_stations(
                    session, suburb if suburb else "", product, "today"
                )
                if postcode and not suburb:
                    matching = [
                        station for station in stations
                        if str(station.get("postcode", "")).strip() == postcode
                    ]
                    if not matching:
                        errors[CONF_POSTCODE] = "no_stations_found"
                        stations = []
                    else:
                        stations = matching

                if stations:
                    location_key = postcode if postcode and not suburb else suburb.lower()
                    await self.async_set_unique_id(f"{location_key}_{product}")
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=f"{suburb or postcode} — {FUEL_PRODUCTS.get(product, str(product))}",
                        data={
                            CONF_SUBURB: suburb,
                            CONF_POSTCODE: postcode if not suburb else "",
                            CONF_PRODUCT: str(product),
                        },
                    )
                elif not errors:
                    errors["base"] = "no_stations_found"

        product_options = [
            SelectOptionDict(value=str(k), label=v) for k, v in FUEL_PRODUCTS.items()
        ]
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Optional(CONF_SUBURB, default=""): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.TEXT)
                ),
                vol.Optional(CONF_POSTCODE, default=""): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.TEXT)
                ),
                vol.Required(CONF_PRODUCT, default="1"): SelectSelector(
                    SelectSelectorConfig(options=product_options, mode=SelectSelectorMode.LIST)
                ),
            }),
            errors=errors,
        )
