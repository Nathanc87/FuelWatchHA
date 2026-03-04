# FuelWatch HA

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

A Home Assistant custom integration for tracking Western Australian fuel prices via [FuelWatch](https://www.fuelwatch.wa.gov.au/).

---

## Features

- Select your preferred station from a live dropdown during setup
- Tracks today's and tomorrow's price for your chosen station
- Supports ULP, PULP, Diesel, Brand Diesel, LPG, 98 RON, and E85
- Fully async — no blocking calls, uses HA's built-in HTTP client
- No external Python dependencies
- Hourly updates

---

## Installation via HACS

1. In Home Assistant go to **HACS → Integrations → ⋮ → Custom repositories**
2. Add `https://github.com/Nathanc87/fuelwatchha` as an **Integration**
3. Search for **FuelWatch HA** and install
4. Restart Home Assistant

---

## Setup

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **FuelWatch HA**
3. Enter a **suburb** (e.g. `Secret Harbour`) and select a **fuel type**
4. A live list of stations in the area will load — select your preferred station
5. Click submit

You can add multiple entries for different stations or fuel types.

---

## Sensors created per entry

| Sensor | Description |
|---|---|
| `Price (Today)` | Today's price in cents per litre |
| `Price (Tomorrow)` | Tomorrow's price in cents per litre (available after ~2:30 PM WA time) |
| `Trading Name` | Station trading name |

Each entry creates a device named after the station (e.g. `Puma Secret Harbour`).

---

## Notes

- **FuelWatch maintenance window:** The service is unavailable every Wednesday 5–10 PM WA time. Sensors will show unavailable during this window and recover automatically.
- **Tomorrow prices:** FuelWatch publishes the next day's prices after 2:30 PM. The `Price (Tomorrow)` sensor will be unavailable until then.
- **Brand Diesel:** Not available at all stations. If no results are returned for a suburb, try a nearby larger suburb.

---

## License

MIT
