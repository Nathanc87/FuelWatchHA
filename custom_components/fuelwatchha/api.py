"""FuelWatch RSS API client."""
from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from typing import Any

import aiohttp

from .const import FUELWATCH_RSS_URL

_LOGGER = logging.getLogger(__name__)

# Avoid repeating the same feed parse warning on every coordinator refresh.
_PARSE_ERROR_LOGGED = False

# XML entities that are valid without escaping. Bare ampersands in feed text
# are common enough to repair safely before parsing.
_INVALID_AMPERSAND = re.compile(r"&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9A-Fa-f]+;)")
_INVALID_XML_CHAR = re.compile(
    r"[\x00-\x08\x0B\x0C\x0E-\x1F]"
)

# Tags present in each FuelWatch RSS <item>
_ITEM_TAGS = (
    "brand",
    "date",
    "price",
    "trading-name",
    "location",
    "address",
    "phone",
    "latitude",
    "longitude",
    "site-features",
)


async def fetch_stations(
    session: aiohttp.ClientSession,
    suburb: str,
    product: int,
    day: str = "today",
) -> list[dict[str, Any]]:
    """Fetch stations from FuelWatch RSS feed.

    Returns a list of station dicts sorted cheapest first,
    or an empty list if the feed returns no results or an error occurs.
    """
    params: dict[str, Any] = {
        "Product": product,
        "Suburb": suburb,
        "Day": day,
    }

    try:
        async with session.get(
            FUELWATCH_RSS_URL,
            params=params,
            timeout=aiohttp.ClientTimeout(total=20),
        ) as response:
            response.raise_for_status()
            content = await response.text(encoding="utf-8", errors="replace")
    except aiohttp.ClientResponseError as err:
        _LOGGER.error(
            "FuelWatch HA: HTTP %s fetching %s %s (%s)",
            err.status, suburb, product, day,
        )
        return []
    except aiohttp.ClientError as err:
        _LOGGER.error(
            "FuelWatch HA: connection error fetching %s %s (%s): %s",
            suburb, product, day, err,
        )
        return []

    return _parse_rss(content)


def _parse_rss(xml_text: str) -> list[dict[str, Any]]:
    """Parse FuelWatch RSS XML and return list of station dicts."""
    global _PARSE_ERROR_LOGGED

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        # Some feed entries contain bare '&' characters, which are not valid
        # XML. Escape only ampersands that do not begin a valid entity.
        repaired = _INVALID_XML_CHAR.sub("", xml_text)
        repaired = _INVALID_AMPERSAND.sub("&amp;", repaired)
        try:
            root = ET.fromstring(repaired)
        except ET.ParseError as err:
            if not _PARSE_ERROR_LOGGED:
                _LOGGER.warning(
                    "FuelWatch HA: RSS response was not valid XML; "
                    "skipping this update (%s)",
                    err,
                )
                _PARSE_ERROR_LOGGED = True
            return []

    _PARSE_ERROR_LOGGED = False
    stations: list[dict[str, Any]] = []

    for item in root.iter("item"):
        station: dict[str, Any] = {}

        for tag in _ITEM_TAGS:
            el = item.find(tag)
            if el is not None and el.text:
                station[tag] = el.text.strip()

        # Skip incomplete entries (must have at least a price and trading name)
        if "price" in station and "trading-name" in station:
            try:
                station["price"] = float(station["price"])
            except (ValueError, TypeError):
                pass
            stations.append(station)

    # Already sorted cheapest first by FuelWatch, but enforce it defensively
    stations.sort(key=lambda s: float(s.get("price", 9999)))

    return stations
