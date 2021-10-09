from __future__ import annotations

from datetime import datetime, timedelta

from rich.console import Console
from rich.style import Style
from rich.table import Table

from weather_command._config import WEATHER_BASE_URL, apppend_api_key
from weather_command._location import get_location_details
from weather_command._weather import WeatherIcons, get_current_weather, get_one_call_current_weather
from weather_command.models.location import Location
from weather_command.models.weather import CurrentWeather, OneCallWeather

HEADER_ROW_STYLE = Style(color="sky_blue2", bold=True)


def show_current(
    console: Console,
    how: str,
    city_zip: str,
    *,
    state_code: str | None = None,
    country_code: str | None = None,
    units: str = "metric",
    am_pm: bool = False,
    temp_only: bool = False,
    terminal_width: int | None = None,
) -> None:
    url = _build_url(
        forecast_type="current",
        how=how,
        city_zip=city_zip,
        units=units,
        state_code=state_code,
        country_code=country_code,
    )

    if terminal_width:
        console.width = terminal_width

    with console.status("Getting weather..."):
        current_weather = get_current_weather(url, console)

    if not temp_only:
        console.print(_current_weather_all(current_weather, units, am_pm))
    else:
        console.print(_current_weather_temp(current_weather, units))


def show_daily(
    console: Console,
    how: str,
    city_zip: str,
    *,
    state_code: str | None = None,
    country_code: str | None = None,
    units: str = "metric",
    am_pm: bool = False,
    temp_only: bool = False,
    terminal_width: int | None = None,
) -> None:
    if terminal_width:
        console.width = terminal_width

    with console.status("Getting weather..."):
        location = get_location_details(
            how=how, city_zip=city_zip, state=state_code, country=country_code, console=console
        )
        url = _build_url(forecast_type="daily", units=units, lon=location.lon, lat=location.lat)
        weather = get_one_call_current_weather(url, console)
        if not temp_only:
            console.print(_daily_all(weather, units, am_pm, location))
        else:
            console.print(_daily_temp_only(weather, units, am_pm, location))


def show_hourly(
    console: Console,
    how: str,
    city_zip: str,
    *,
    state_code: str | None = None,
    country_code: str | None = None,
    units: str = "metric",
    am_pm: bool = False,
    temp_only: bool = False,
    terminal_width: int | None = None,
) -> None:
    if terminal_width:
        console.width = terminal_width

    with console.status("Getting weather..."):
        location = get_location_details(
            how=how, city_zip=city_zip, state=state_code, country=country_code, console=console
        )
        url = _build_url(forecast_type="hourly", units=units, lon=location.lon, lat=location.lat)
        weather = get_one_call_current_weather(url, console)
        if not temp_only:
            console.print(_hourly_all(weather, units, am_pm, location))
        else:
            console.print(_hourly_temp_only(weather, units, am_pm, location))


def _build_url(
    forecast_type: str,
    units: str,
    how: str | None = None,
    city_zip: str | None = None,
    lon: float | None = None,
    lat: float | None = None,
    state_code: str | None = None,
    country_code: str | None = None,
) -> str:
    if forecast_type == "current":
        if how == "city":
            url = f"{WEATHER_BASE_URL}/weather?q={city_zip}&units={units}"
        else:
            url = f"{WEATHER_BASE_URL}/weather?zip={city_zip}&units={units}"

        if state_code:
            url = f"{url}&state_code={state_code}"

        if country_code:
            url = f"{url}&country_code={country_code}"
    else:
        url = f"{WEATHER_BASE_URL}/onecall?lat={lat}&lon={lon}&units={units}"

    return apppend_api_key(url)


def _current_weather_all(current_weather: CurrentWeather, units: str, am_pm: bool) -> Table:
    temp_unit = _temp_units(units)
    speed_unit = _speed_units(units)
    precip_unit = _precip_units(units)
    conditions = current_weather.weather[0].description
    weather_icon = WeatherIcons.get_icon(conditions)
    if weather_icon:
        conditions += f" {weather_icon}"
    if not am_pm:
        sunrise = str(
            (current_weather.sys.sunrise + timedelta(seconds=current_weather.timezone)).time()
        )
        sunset = str(
            (current_weather.sys.sunset + timedelta(seconds=current_weather.timezone)).time()
        )
    else:
        sunrise = datetime.strftime(
            (current_weather.sys.sunrise + timedelta(seconds=current_weather.timezone)), "%I:%M %p"
        )
        sunset = datetime.strftime(
            (current_weather.sys.sunset + timedelta(seconds=current_weather.timezone)), "%I:%M %p"
        )

    table = Table(
        title=f"Current weather for {current_weather.name}", header_style=HEADER_ROW_STYLE
    )
    table.add_column(f"Temperature ({temp_unit}) :thermometer:")
    table.add_column(f"Feels Like ({temp_unit}) :thermometer:")
    table.add_column("Humidity")
    table.add_column("Conditions")
    table.add_column(f"Wind Speed ({speed_unit})")
    table.add_column(f"Wind Gusts ({speed_unit})")
    table.add_column(f"Rain 1 Hour ({precip_unit}) :cloud_with_rain:")
    table.add_column(f"Rain 3 Hour ({precip_unit}) :cloud_with_rain:")
    table.add_column(f"Snow 1 Hour ({precip_unit}) :snowflake:")
    table.add_column(f"Snow 3 Hour ({precip_unit}) :snowflake:")
    table.add_column("Sunrise :sunrise:")
    table.add_column("Sunset :sunset:")

    if current_weather.rain and current_weather.rain.one_hour:
        rain_one_hour = (
            str(_mm_to_in(current_weather.rain.one_hour))
            if units == "imperial"
            else str(current_weather.rain.one_hour)
        )
    else:
        rain_one_hour = "0"

    if current_weather.rain and current_weather.rain.three_hour:
        rain_three_hour = (
            str(_mm_to_in(current_weather.rain.three_hour))
            if units == "imperial"
            else str(current_weather.rain.three_hour)
        )
    else:
        rain_three_hour = "0"

    if current_weather.snow and current_weather.snow.one_hour:
        snow_one_hour = (
            str(_mm_to_in(current_weather.snow.one_hour))
            if units == "imperial"
            else str(current_weather.snow.one_hour)
        )
    else:
        snow_one_hour = "0"

    if current_weather.snow and current_weather.snow.three_hour:
        snow_three_hour = (
            str(_mm_to_in(current_weather.snow.three_hour))
            if units == "imperial"
            else str(current_weather.snow.three_hour)
        )
    else:
        snow_three_hour = "0"

    if current_weather.wind and current_weather.wind.speed:
        wind = (
            str(round(_kph_to_mph(current_weather.wind.speed)))
            if units == "imperial"
            else str(round(current_weather.wind.speed))
        )
    else:
        wind = "0"

    if current_weather.wind and current_weather.wind.gust:
        gusts = (
            str(round(_kph_to_mph(current_weather.wind.gust)))
            if units == "imperial"
            else str(round(current_weather.wind.gust))
        )
    else:
        gusts = "0"

    table.add_row(
        str(round(current_weather.main.temp)),
        str(round(current_weather.main.feels_like)),
        f"{current_weather.main.humidity}%" if current_weather.main.humidity else "0%",
        conditions,
        wind,
        gusts,
        rain_one_hour,
        rain_three_hour,
        snow_one_hour,
        snow_three_hour,
        sunrise,
        sunset,
    )

    return table


def _current_weather_temp(current_weather: CurrentWeather, units: str) -> Table:
    temp_unit = _temp_units(units)

    table = Table(
        title=f"Current weather for {current_weather.name}", header_style=HEADER_ROW_STYLE
    )
    table.add_column(f"Temperature ({temp_unit}) :thermometer:")
    table.add_column(f"Feels Like ({temp_unit}) :thermometer:")
    table.add_row(
        str(round(current_weather.main.temp)),
        str(round(current_weather.main.feels_like)),
    )

    return table


def _daily_all(weather: OneCallWeather, units: str, am_pm: bool, location: Location) -> Table:
    temp_unit = _temp_units(units)
    speed_unit = _speed_units(units)
    pressure_unit = _pressure_units(units)
    table = Table(
        title=f"Hourly weather for {location.display_name}",
        header_style=HEADER_ROW_STYLE,
        show_lines=True,
    )
    table.add_column("Date/Time :date:")
    table.add_column(f"Low ({temp_unit}) :thermometer:")
    table.add_column(f"High ({temp_unit}) :thermometer:")
    table.add_column("Humidity")
    table.add_column(f"Dew Point ({temp_unit})")
    table.add_column(f"Pressure {pressure_unit}")
    table.add_column("UVI")
    table.add_column("Clouds")
    table.add_column(f"Wind ({speed_unit})")
    table.add_column(f"Wind Gusts {speed_unit}")
    table.add_column("Sunrise :sunrise:")
    table.add_column("Sunset :sunset:")

    for daily in weather.daily:
        if not am_pm:
            dt = datetime.strftime(
                (daily.dt + timedelta(seconds=weather.timezone_offset)), "%Y-%m-%d"
            )
            sunrise = str((daily.sunrise + timedelta(seconds=weather.timezone_offset)).time())
            sunset = str((daily.sunset + timedelta(seconds=weather.timezone_offset)).time())
        else:
            dt = datetime.strftime(
                (daily.dt + timedelta(seconds=weather.timezone_offset)),
                "%Y-%m-%d",
            )
            sunrise = datetime.strftime(
                (daily.sunrise + timedelta(seconds=weather.timezone_offset)), "%I:%M %p"
            )
            sunset = datetime.strftime(
                (daily.sunset + timedelta(seconds=weather.timezone_offset)), "%I:%M %p"
            )

        if daily.wind_speed:
            wind = (
                str(round(_kph_to_mph(daily.wind_speed)))
                if units == "imperial"
                else str(round(daily.wind_speed))
            )
        else:
            wind = "0"

        if daily.wind_gust:
            gusts = (
                str(round(_kph_to_mph(daily.wind_gust)))
                if units == "imperial"
                else str(round(daily.wind_gust))
            )
        else:
            gusts = "0"

        if daily.pressure:
            pressure = (
                str(_hpa_to_in(daily.pressure)) if units == "imperial" else str(daily.pressure)
            )
        else:
            pressure = "0"

        table.add_row(
            dt,
            str(round(daily.temp.min)),
            str(round(daily.temp.max)),
            f"{daily.humidity}%",
            str(round(daily.dew_point)),
            pressure,
            str(daily.uvi),
            f"{daily.clouds}%",
            wind,
            gusts,
            sunrise,
            sunset,
        )

    return table


def _daily_temp_only(weather: OneCallWeather, units: str, am_pm: bool, location: Location) -> Table:
    temp_unit = _temp_units(units)
    table = Table(
        title=f"Hourly weather for {location.display_name}",
        header_style=HEADER_ROW_STYLE,
        show_lines=True,
    )
    table.add_column("Date/Time :date:")
    table.add_column(f"Low ({temp_unit}) :thermometer:")
    table.add_column(f"High ({temp_unit}) :thermometer:")

    for daily in weather.daily:
        dt = datetime.strftime((daily.dt + timedelta(seconds=weather.timezone_offset)), "%Y-%m-%d")

        table.add_row(
            dt,
            str(round(daily.temp.min)),
            str(round(daily.temp.max)),
        )

    return table


def _hourly_all(weather: OneCallWeather, units: str, am_pm: bool, location: Location) -> Table:
    temp_unit = _temp_units(units)
    speed_unit = _speed_units(units)
    precip_units = _precip_units(units)
    pressure_units = _pressure_units(units)
    table = Table(
        title=f"Hourly weather for {location.display_name}",
        header_style=HEADER_ROW_STYLE,
        show_lines=True,
    )
    table.add_column("Date/Time :date:")
    table.add_column(f"Temperature ({temp_unit}) :thermometer:")
    table.add_column(f"Feels Like ({temp_unit}) :thermometer:")
    table.add_column("Humidity")
    table.add_column(f"Dew Point ({temp_unit})")
    table.add_column(f"Pressure {pressure_units}")
    table.add_column("UVI")
    table.add_column("Clouds")
    table.add_column(f"Wind ({speed_unit})")
    table.add_column(f"Wind Gusts {speed_unit}")
    table.add_column(f"Rain ({precip_units}) :cloud_with_rain:")
    table.add_column(f"Snow ({precip_units}) :snowflake:")

    for hourly in weather.hourly:
        if not am_pm:
            dt = datetime.strftime(
                (hourly.dt + timedelta(seconds=weather.timezone_offset)), "%Y-%m-%d %H:%M"
            )
        else:
            dt = datetime.strftime(
                (hourly.dt + timedelta(seconds=weather.timezone_offset)),
                "%Y-%m-%d %I:%M %p",
            )

        if hourly.rain:
            rain = (
                str(_mm_to_in(hourly.rain.one_hour))
                if units == "imperial"
                else str(hourly.rain.one_hour)
            )
        else:
            rain = "0"

        if hourly.snow:
            snow = (
                str(_mm_to_in(hourly.snow.one_hour))
                if units == "imperial"
                else str(hourly.snow.one_hour)
            )
        else:
            snow = "0"

        if hourly.wind_speed:
            wind = (
                str(round(_kph_to_mph(hourly.wind_speed)))
                if units == "imperial"
                else str(round(hourly.wind_speed))
            )
        else:
            wind = "0"

        if hourly.wind_gust:
            gusts = (
                str(round(_kph_to_mph(hourly.wind_gust)))
                if units == "imperial"
                else str(round(hourly.wind_gust))
            )
        else:
            gusts = "0"

        if hourly.pressure:
            pressure = (
                str(_hpa_to_in(hourly.pressure)) if units == "imperial" else str(hourly.pressure)
            )
        else:
            pressure = "0"

        table.add_row(
            dt,
            str(round(hourly.temp)),
            str(round(hourly.feels_like)),
            f"{hourly.humidity}%",
            str(round(hourly.dew_point)),
            pressure,
            str(hourly.uvi),
            f"{hourly.clouds}%",
            wind,
            gusts,
            rain,
            snow,
        )

    return table


def _hourly_temp_only(
    weather: OneCallWeather, units: str, am_pm: bool, location: Location
) -> Table:
    temp_unit = _temp_units(units)
    table = Table(
        title=f"Hourly weather for {location.display_name}",
        header_style=HEADER_ROW_STYLE,
        show_lines=True,
    )
    table.add_column("Date/Time :date:")
    table.add_column(f"Temperature ({temp_unit}) :thermometer:")
    table.add_column(f"Feels Like ({temp_unit}) :thermometer:")

    for hourly in weather.hourly:
        if not am_pm:
            dt = datetime.strftime(
                (hourly.dt + timedelta(seconds=weather.timezone_offset)), "%Y-%m-%d %H:%M"
            )
        else:
            dt = datetime.strftime(
                (hourly.dt + timedelta(seconds=weather.timezone_offset)),
                "%Y-%m-%d %I:%M %p",
            )

        table.add_row(
            dt,
            str(round(hourly.temp)),
            str(round(hourly.feels_like)),
        )

    return table


def _hpa_to_in(value: float) -> float:
    return round(value / 33.863886666667, 2)


def _kph_to_mph(value: float) -> float:
    return value / 1.609


def _mm_to_in(value: float) -> float:
    return round(value / 25.4, 2)


def _precip_units(units: str) -> str:
    _validate_units(units)
    return "mm" if units == "metric" else "in"


def _pressure_units(units: str) -> str:
    return "hPa" if units == "metric" else "in"


def _speed_units(units: str) -> str:
    _validate_units(units)
    return "kph" if units == "metric" else "mph"


def _temp_units(units: str) -> str:
    _validate_units(units)
    return "C" if units == "metric" else "F"


def _validate_units(units: str) -> None:
    if units not in ["metric", "imperial"]:
        raise ValueError("Units must either be metric or imperial")
