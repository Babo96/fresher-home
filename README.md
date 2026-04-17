# Beurer FreshHome Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Home Assistant custom integration for controlling Beurer FreshHome air purifiers via the cloud API.

## Description

This integration allows you to control your Beurer FreshHome air purifiers directly from Home Assistant. It connects to Beurer's cloud servers using a SignalR WebSocket connection, providing real-time device control and sensor updates.

This integration was reverse-engineered from the official Beurer FreshHome mobile app. It enables seamless integration of your air purifiers into your smart home automation workflows.

## Supported Devices

The following Beurer FreshHome air purifier models are supported:

| Model | Status |
|-------|--------|
| LR 500 | ✅ Tested and confirmed working |
| LR 400 | ✅ Should work (same protocol) |
| LR 401 | ✅ Should work (same protocol) |
| LR 405 | ✅ Should work (same protocol) |
| LR 406 | ✅ Should work (same protocol) |

Other Beurer FreshHome models may also work but have not been tested. If you have a different model, please open an issue to report your experience.

## Credits

- **Reverse Engineering**: The underlying SignalR protocol was mainly reverse-engineered by me from the Beurer FreshHome mobile app.
- **Development**: The clean Home Assistant architecture and implementation was primarily generated with the assistance of AI coding tools (OpenCode/Antigravity), heavily guided and reviewed by me.
- Not affiliated with or endorsed by Beurer GmbH
- All product names and trademarks are property of their respective owners

## Features

### Control Functions

This integration provides full control over your air purifier with the following functions:

| Function | Description |
|----------|-------------|
| **Power** | Turn the device on or off |
| **Fan Speed** | Set speed level from 1 to 4 |
| **Mode** | Choose between Manual, Auto, Sleep, or Turbo modes |
| **Timer** | Set auto-off timer from 0 to 480 minutes |
| **Sleep Mode** | Enable quiet operation mode |
| **UV Light** | Control the built-in UV-C sterilization light |
| **Temperature Unit** | Switch between Celsius and Fahrenheit display |
| **Filter Reset** | Reset the filter replacement timer |
| **Refresh State** | Force an immediate state update from the device |
| **Buzzer** | Enable or disable button press sounds |

### Sensor Readings

The integration exposes the following sensor data from your air purifier:

| Sensor | Unit | Description |
|--------|------|-------------|
| **PM2.5** | µg/m³ | Fine particulate matter concentration |
| **Air Quality Index** | - | Overall air quality rating (1-4) |
| **Humidity** | % | Relative humidity level |
| **Temperature** | °C/°F | Current room temperature |
| **Filter Status** | % | Remaining filter life percentage |

## Installation

### Manual Installation (Recommended)

This is the primary installation method since the repository is hosted on Forgejo.

#### Option A: Using HACS Developer Tools (if you mirror to GitHub)

If you mirror this repository to GitHub, you can install via HACS:

1. Open HACS in your Home Assistant instance
2. Go to **Integrations**
3. Click the **⋮** menu and select **Custom repositories**
4. Add your GitHub mirror URL
5. Set the category to **Integration**
6. Click **Add**
7. Find **Beurer FreshHome** in the HACS store and click **Download**
8. Restart Home Assistant

#### Option B: Manual Download

1. Download or clone this repository
2. Copy the `custom_components/beurer/` folder to your Home Assistant `config/custom_components/` directory
3. Install the Python dependency: `pip install signalrcore` or add `signalrcore` to your `requirements.txt`
4. Restart Home Assistant
5. Add the integration via **Settings** → **Devices & Services** → **Add Integration** → **"Beurer FreshHome"**

> **Note:** HACS custom repository installation requires the repository to be hosted on GitHub. If you mirror this repo to GitHub, you can add it via HACS → Custom Repositories with the GitHub URL.

## Configuration

After installation, add the integration to Home Assistant:

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for **Beurer FreshHome**
4. Enter your Beurer account credentials:
   - **Email**: Your Beurer FreshHome app login email
   - **Password**: Your Beurer FreshHome app password
5. The integration will automatically discover all devices associated with your account

## Entities

Each connected air purifier creates the following entities in Home Assistant:

| Entity | Type | Description |
|--------|------|-------------|
| Air Purifier | `fan` | Main control entity with on/off and speed |
| Power | `switch` | Toggle device power |
| Sleep Mode | `switch` | Enable/disable sleep mode |
| UV Light | `switch` | Toggle UV-C sterilization |
| Mode | `select` | Choose operating mode (Manual/Auto/Sleep/Turbo) |
| Temperature Unit | `select` | Switch between °C and °F |
| Timer | `number` | Set auto-off timer (0-480 minutes) |
| Filter Reset | `button` | Reset filter replacement timer |
| Refresh | `button` | Force immediate state refresh |
| PM2.5 | `sensor` | Fine particulate matter level |
| Air Quality | `sensor` | Air quality index (1-4) |
| Humidity | `sensor` | Relative humidity percentage |
| Temperature | `sensor` | Current temperature |
| Filter Life | `sensor` | Remaining filter life percentage |

## Troubleshooting

### Device Not Found

If your device does not appear after configuration:

- Ensure the device is connected to WiFi and showing as online in the Beurer FreshHome mobile app
- Verify your account credentials are correct
- Try removing and re-adding the integration

### Authentication Failed

- Double-check your email and password
- Ensure you are using the same credentials as the official Beurer FreshHome mobile app
- If you recently changed your password, try logging out and back into the mobile app first

### Connection Drops

The integration includes automatic reconnection with exponential backoff. If connection issues persist:

- Check your internet connection
- Verify the Beurer cloud service is operational
- Check Home Assistant logs for specific error messages

### Sensors Not Updating

If sensor values appear stale:

- Press the **Refresh** button entity to force an immediate state update
- Check that the device is online in the mobile app
- Verify the device firmware is up to date

## Contributing

Contributions are welcome. Please open an issue or pull request on the repository.

When submitting pull requests, please follow the template in `.github/PULL_REQUEST_TEMPLATE.md`.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
