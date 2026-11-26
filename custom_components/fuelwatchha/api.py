"""FuelWatch JSON API client."""
from __future__ import annotations

import json
import logging
from typing import Any

import aiohttp

from .const import FUELWATCH_API_URL

_LOGGER = logging.getLogger(__name__)

# Avoid repeating identical API errors on every coordinator refresh.
_API_ERROR_LOGGED = False


async def fetch_stations(
    session: aiohttp.ClientSession,
    suburb: str,
    product: int,
    day: str = "today",
) -> list[dict[str, Any]]:
    """Fetch and normalize station prices from the public FuelWatch JSON API.

    The API returns JSON:API station resources. Normalize them to the legacy
    internal keys so existing config entries and sensor entities remain valid.
    """
    global _API_ERROR_LOGGED

    params = {
        "product": str(product),
        "suburb": suburb,
        "day": day,
    }
    headers = {"Accept": "application/vnd.api+json"}

    try:
        async with session.get(
            FUELWATCH_API_URL,
            params=params,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=25),
        ) as response:
            response.raise_for_status()
            body = await response.text(encoding="utf-8", errors="replace")
    except aiohttp.ClientResponseError as err:
        if not _API_ERROR_LOGGED:
            _LOGGER.warning(
                "FuelWatch HA: JSON API returned HTTP %s for %s, product %s (%s)",
                err.status, suburb, product, day,
            )
            _API_ERROR_LOGGED = True
        return []
    except (aiohttp.ClientError, TimeoutError) as err:
        if not _API_ERROR_LOGGED:
            _LOGGER.warning(
                "FuelWatch HA: connection error querying %s, product %s (%s): %s",
                suburb, product, day, err,
            )
            _API_ERROR_LOGGED = True
        return []

    try:
        payload = json.loads(body)
    except json.JSONDecodeError as err:
        if not _API_ERROR_LOGGED:
            _LOGGER.warning(
                "FuelWatch HA: JSON API returned an invalid JSON response (%s)",
                err,
            )
            _API_ERROR_LOGGED = True
        return []

    if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
        if not _API_ERROR_LOGGED:
            _LOGGER.warning(
                "FuelWatch HA: JSON API response did not contain a station data list"
            )
            _API_ERROR_LOGGED = True
        return []

    _API_ERROR_LOGGED = False
    meta = payload.get("meta") or {}
    source_date = meta.get("sourceDate")

    stations: list[dict[str, Any]] = []
    for resource in payload["data"]:
        if not isinstance(resource, dict):
            continue
        attributes = resource.get("attributes") or {}
        price_info = attributes.get("price") or {}
        products = price_info.get("products") or {}
        price_value = products.get(str(product), products.get(product))

        # Some API expansions return a price object; the default response
        # returns a numeric cents-per-litre value.
        if isinstance(price_value, dict):
            price_value = price_value.get("amount")

        try:
            price = float(price_value)
        except (TypeError, ValueError):
            # A station that does not sell this product is not a zero-price
            # station and should not be added to the result.
            continue

        address_info = attributes.get("address") or {}
        street = address_info.get("street") or ""
        station_suburb = address_info.get("suburb") or suburb
        state = address_info.get("state") or "WA"
        postcode = address_info.get("postcode") or ""
        address_parts = [part for part in (street, station_suburb, state, postcode) if part]
        address = ", ".join(address_parts)

        brand = attributes.get("brand")
        if isinstance(brand, dict):
            brand = brand.get("name") or brand.get("code")

        stations.append(
            {
                "trading-name": attributes.get("tradingName") or attributes.get("name") or "Unknown",
                "brand": brand,
                "price": price,
                "date": price_info.get("asAt") or source_date,
                "location": station_suburb,
                "address": address,
                "postcode": str(postcode) if postcode else "",
                "phone": attributes.get("phone"),
                "latitude": attributes.get("latitude"),
                "longitude": attributes.get("longitude"),
                "site-features": attributes.get("siteFeatures"),
            }
        )

    stations.sort(key=lambda station: station["price"])
    return stations
