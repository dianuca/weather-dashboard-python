# Python Weather Dashboard

Python Weather Dashboard is a desktop application built with Python and Tkinter that retrieves current weather conditions and forecast data from the OpenWeather REST API.

Users can search for any city and view the current temperature, weather description, local time, wind speed, precipitation, humidity, short-term forecast and multi-day forecast in a clear card-based interface.

## Screenshots

### Current Weather Dashboards

The dashboard updates dynamically according to the searched city and the information returned by the OpenWeather API.

<p align="center">
  <img src="screenshots/barcelona-weather-dashboard.png" width="46%" alt="Barcelona clear weather dashboard">
  <img src="screenshots/sibiu-weather-dashboard.png" width="46%" alt="Sibiu rainy weather dashboard">
</p>

### Weather Measurements

Wind speed, precipitation and humidity are displayed in separate summary cards for quick access.

<p align="center">
  <img src="screenshots/weather-metrics.png" width="90%" alt="Wind speed, precipitation and humidity cards">
</p>

### Hourly and Daily Forecast

Forecast information is presented both at three-hour intervals and as a multi-day overview containing minimum and maximum temperatures.

<p align="center">
  <img src="screenshots/hourly-daily-forecast.png" width="90%" alt="Hourly and daily weather forecast">
</p>

### Error Handling

When a city cannot be found, the application displays a clear error dialog instead of terminating unexpectedly.

<p align="center">
  <img src="screenshots/invalid-city-error.png" width="55%" alt="Invalid city error dialog">
</p>

## Features

- Search for weather information by city name
- Display the current temperature
- Display the current weather description
- Show the searched city's local date and time
- Display wind speed
- Display precipitation information
- Display humidity
- Show weather icons based on current conditions
- Present forecasts at three-hour intervals
- Provide a multi-day weather overview
- Calculate daily minimum and maximum temperatures
- Download and resize weather icons
- Cache downloaded icons during the application session
- Handle invalid city searches
- Handle network and API errors
- Use request timeouts
- Validate API responses before displaying data
- Load the API key securely from an environment variable

## Technology Stack

- Python 3.11+
- Tkinter
- Requests
- Pillow
- OpenWeather REST API
- JSON
- Python `datetime`
- Environment variables

## Application Workflow

```text
City Search
    │
    ▼
Input Validation
    │
    ▼
OpenWeather API Request
    │
    ├── Current weather data
    └── Forecast data
    │
    ▼
JSON Validation and Processing
    │
    ├── Temperature
    ├── Weather condition
    ├── Wind speed
    ├── Precipitation
    ├── Humidity
    ├── Timezone
    └── Forecast entries
    │
    ▼
Timezone Conversion
    │
    ▼
Forecast Aggregation
    │
    ├── Three-hour forecast
    └── Daily minimum and maximum values
    │
    ▼
Tkinter Dashboard Update
```

## How It Works

1. The user enters the name of a city.
2. The application validates the input.
3. A request is sent to the OpenWeather API.
4. The returned JSON response is checked for missing or invalid values.
5. The current weather information is extracted.
6. The location timezone is used to calculate the city's local time.
7. Forecast entries are organised into short-term and daily views.
8. Weather icons are downloaded and resized using Pillow.
9. The Tkinter interface is updated with the processed information.
10. Errors are displayed through user-friendly dialogs.

## Weather Information

The application displays the following information for the selected city:

| Information | Description |
|---|---|
| City | Name of the searched location |
| Local time | Date and time adjusted to the city's timezone |
| Temperature | Current temperature |
| Weather condition | Description of the current weather |
| Wind speed | Current wind measurement |
| Precipitation | Rain or precipitation information when available |
| Humidity | Current atmospheric humidity |
| Short-term forecast | Weather information at three-hour intervals |
| Daily forecast | Minimum and maximum temperature for each forecast day |

## Forecast Processing

The OpenWeather forecast data contains entries at three-hour intervals.

The application processes these entries in two ways.

### Three-Hour Forecast

Upcoming forecast entries are displayed chronologically and include information such as:

- local time;
- temperature;
- weather condition;
- weather icon.

### Daily Forecast

Forecast entries are grouped according to the local calendar date of the searched city.

For each day, the application calculates:

- minimum temperature;
- maximum temperature;
- representative weather condition;
- representative weather icon.

This allows multiple three-hour entries to be transformed into a simpler daily summary.

## Timezone Conversion

Weather timestamps are converted using the timezone offset returned by the OpenWeather API.

This means the displayed time belongs to the searched city rather than to the computer running the application.

The conversion process ensures that:

- forecast entries use the target city's local time;
- forecast days are grouped according to the correct local date;
- users can search for cities located in different timezones.

## Weather Icon Handling

Weather icons are retrieved according to the condition codes returned by the API.

The application:

1. identifies the required icon;
2. downloads it when necessary;
3. opens it using Pillow;
4. resizes it for the interface;
5. stores it in memory;
6. reuses the cached version when the same icon is needed again.

Caching reduces repeated network requests during the same application session.

## Project Structure

```text
weather-dashboard-python/
├── app.py
├── requirements.txt
├── screenshots/
│   ├── barcelona-weather-dashboard.png
│   ├── sibiu-weather-dashboard.png
│   ├── weather-metrics.png
│   ├── hourly-daily-forecast.png
│   └── invalid-city-error.png
├── .gitignore
└── README.md
```

| File or directory | Responsibility |
|---|---|
| `app.py` | Contains the interface, API communication and weather-processing logic |
| `requirements.txt` | Lists the required Python packages |
| `screenshots/` | Contains the images displayed in this README |
| `.gitignore` | Excludes credentials, virtual environments and generated files |
| `README.md` | Contains project documentation |

## Requirements

Before running the application, make sure the following are available:

- Python 3.11 or newer
- `pip`
- An OpenWeather API key
- Internet access
- Tkinter support in the installed Python version

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/dianuca/weather-dashboard-python.git
cd weather-dashboard-python
```

### 2. Create a Virtual Environment

On macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

On Windows Command Prompt:

```cmd
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install the Dependencies

```bash
pip install -r requirements.txt
```

The main dependencies are:

```text
requests
Pillow
```

Tkinter is normally included with standard Python installations.

## API Key Configuration

Create an API key using the OpenWeather platform.

The application reads the key from the following environment variable:

```text
OPENWEATHER_API_KEY
```

### macOS or Linux

```bash
export OPENWEATHER_API_KEY="your_api_key"
```

### Windows PowerShell

```powershell
$env:OPENWEATHER_API_KEY="your_api_key"
```

### Windows Command Prompt

```cmd
set OPENWEATHER_API_KEY=your_api_key
```

The environment variable must be configured in the same terminal session used to start the application.

## Running the Application

On macOS or Linux:

```bash
python3 app.py
```

On Windows:

```bash
python app.py
```

Depending on the Python configuration, the following command may also work:

```bash
python app.py
```

## Using the Application

1. Start the application.
2. Enter a city name in the search field.
3. Press the search button.
4. Wait for the weather information to load.
5. Review the current weather cards.
6. Scroll through the short-term forecast.
7. Review the multi-day forecast.
8. Enter another city to refresh the dashboard.

Examples of valid searches include:

```text
Barcelona
Sibiu
Bucharest
London
Madrid
```

## Error Handling

The application handles several possible problems.

### Empty Search

A message is displayed when the user attempts to search without entering a city name.

### Invalid City

When the requested city cannot be found, the application displays a clear error dialog.

### Network Problems

Connection failures are caught and reported instead of causing the application to close.

### Request Timeout

HTTP requests use timeouts so the application does not wait indefinitely for an API response.

### Invalid API Key

A missing or invalid API key produces an explanatory error message.

### Incomplete API Response

The JSON response is validated before values are displayed. Missing optional values are handled defensively.

Possible handled cases include:

- no precipitation information;
- missing forecast fields;
- unavailable weather icons;
- unexpected API response structures;
- invalid JSON data.

## Security

The OpenWeather API key is read from the `OPENWEATHER_API_KEY` environment variable.

The real key must not be written directly inside `app.py`.

The following files and values should never be committed to GitHub:

- API keys;
- credentials;
- `.env` files containing real secrets;
- virtual environments;
- local cache files;
- operating-system metadata.

Recommended `.gitignore` entries:

```gitignore
.venv/
venv/
env/
__pycache__/
*.pyc
.env
.DS_Store
```

## Privacy

- The application does not require a user account
- Searches are sent only to the weather API
- No personal profile is stored
- Search history is not permanently saved
- The application does not upload local files
- Weather data is displayed only during the current session

## Current Limitations

- An internet connection is required
- A valid OpenWeather API key is required
- API availability depends on the external weather service
- Searches are based on city names
- Cities with identical names may require additional location information
- Network requests may temporarily affect interface responsiveness
- The interface is primarily written in Romanian
- Temperature-unit preferences are not currently configurable
- Favourite cities are not stored
- Automatic location detection is not implemented
- Automated tests are not currently included

## Future Improvements

- Translate the complete interface into English
- Run API requests in a background thread
- Add Celsius and Fahrenheit preferences
- Add configurable wind-speed units
- Add saved and favourite cities
- Add recent-search history
- Add automatic location detection
- Add country-code selection for cities with identical names
- Add weather alerts
- Add sunrise and sunset information
- Add air-quality information
- Add animated weather backgrounds
- Add hourly temperature charts
- Add precipitation charts
- Add dark mode
- Add keyboard shortcuts
- Improve responsive behaviour for different screen sizes
- Add unit tests for forecast aggregation
- Add tests for timezone conversion
- Add tests for API response validation
- Separate the interface and API logic into multiple modules
- Package the application for macOS and Windows
- Add continuous integration through GitHub Actions

## Concepts Demonstrated

This project demonstrates:

- Python desktop application development;
- Tkinter interface design;
- REST API integration;
- HTTP requests;
- JSON processing;
- environment-variable configuration;
- timezone conversion;
- forecast aggregation;
- image downloading and resizing;
- in-memory caching;
- exception handling;
- input validation;
- user-friendly error reporting;
- virtual environments;
- dependency management.

## Author

**Diana Ciodolan**

Computer Science graduate and master's student in Advanced Information Systems and Technologies.
