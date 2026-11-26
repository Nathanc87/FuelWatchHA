# FuelWatch HA

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

A Home Assistant custom integration for tracking Western Australian fuel prices from [FuelWatch](https://www.fuelwatch.wa.gov.au/) using a public JSON API.

## Features

- Enter a four-digit postcode and fuel type
- Automatically tracks the cheapest station in that postcode — no need to add individual stations
- Today's and tomorrow's cheapest prices and station names
- Hourly updates
- Fully async and uses Home Assistant's built-in HTTP client
- No external Python dependencies

## Data source

FuelWatch HA uses the public, read-only [FuelWatch JSON API](https://docs.fuelwatch.oss.bhodges.me/), an independent API that republishes WA FuelWatch price data. No API key is required. The API does not support postcode filtering, so FuelWatch HA requests the statewide station list for the selected fuel and filters it locally by postcode. Price and station data are provided by FuelWatch; API availability depends on its maintainer.

## Installation via HACS

1. In Home Assistant go to **HACS → Integrations → ⋮ → Custom repositories**
2. Add `https://github.com/Nathanc87/fuelwatchha` as an **Integration**
3. Search for **FuelWatch HA** and install
4. Restart Home Assistant

## Setup

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **FuelWatch HA**
3. Enter your four-digit postcode (e.g. `6168`) and select the fuel type
4. Submit. The integration creates one entry for that postcode and fuel type and automatically selects the cheapest station.

You can add another postcode or fuel type if you want to track more than one.

## Sensors created per entry

| Sensor | Description |
|---|---|
| `Price (Today)` | Cheapest price today in cents per litre |
| `Price (Tomorrow)` | Cheapest price tomorrow in cents per litre (when published) |
| `Cheapest Station` | Station currently offering the cheapest price today |

Price sensors include postcode, station suburb, station name, address and price date as attributes. The cheapest station can change as prices update.

## Notes

- The integration checks hourly. The API's shared source cache refreshes hourly and may be cached for up to six hours.
- Tomorrow's prices appear after FuelWatch publishes them.
- Prices are in Australian cents per litre.
- The integration requests the statewide list for the chosen fuel, then filters by postcode because the API does not offer a postcode parameter.
- Existing station-based config entries continue to use their stored station selection; new entries use postcode tracking.

## License

MIT
