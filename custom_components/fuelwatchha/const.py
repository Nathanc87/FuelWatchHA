"""Constants for FuelWatch HA."""

DOMAIN = "fuelwatchha"

FUELWATCH_RSS_URL = "http://www.fuelwatch.wa.gov.au/fuelwatch/fuelWatchRSS"

FUEL_PRODUCTS: dict[int, str] = {
    1: "Unleaded (ULP)",
    2: "Premium Unleaded (PULP)",
    4: "Diesel",
    5: "LPG",
    6: "98 RON",
    10: "E85",
    11: "Brand Diesel",
}

CONF_SUBURB = "suburb"
CONF_PRODUCT = "product"
CONF_STATION_TRADING_NAME = "station_trading_name"
