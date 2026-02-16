from collections import namedtuple
from dataclasses import dataclass
import logging
import numpy as np
import asyncio
import datetime

from open_meteo import OpenMeteo, Forecast, CurrentWeather, OpenMeteoConnectionError
from open_meteo.models import DailyParameters, HourlyParameters


BBox = namedtuple("BBox", ["min_lon", "min_lat", "max_lon", "max_lat"])
LLoc = namedtuple("LLoc", ["lat", "lon"])

log = logging.getLogger(__name__)

poland_bbox = BBox(
    min_lon=14.07,
    min_lat=49.00,
    max_lon=24.15,
    max_lat=54.84,
)

krakow_loc = LLoc(50.061667, 19.9375)

@dataclass()
class HourlyWeather:
    datetime_d: datetime.datetime
    temp_c: float
    clouds: int
    precipitation: float
    weather_code: int

    def __init__(self, forecast: Forecast, datetime_i: datetime.datetime):
        if forecast.hourly is not None: 
            hourly_forecast = forecast.hourly
        else:
            raise ValueError("hourly_forecast is None")
        
        hour_index = hourly_forecast.time.index(datetime_i)

        try:
            self.datetime_d = datetime_i
            self.temp_c = hourly_forecast.temperature_2m[hour_index] # pyright: ignore[reportOptionalSubscript]
            self.clouds = hourly_forecast.cloud_cover[hour_index] # pyright: ignore[reportOptionalSubscript]
            self.precipitation = hourly_forecast.precipitation[hour_index] # pyright: ignore[reportOptionalSubscript]
            self.weather_code = hourly_forecast.weather_code[hour_index] # pyright: ignore[reportOptionalSubscript]
        except (TypeError, IndexError) as e:
            raise IndexError(f"Error fetching data at {datetime_i}: {e}")


@dataclass()
class CumDayWeather:
    precipitation_mm: float
    temp_c_max: float
    temp_c_min: float
    humidity: float
    weather_code: int
        
    def __init__(self, forecast: Forecast, datetime_i: datetime.datetime):
        if forecast.daily is not None: 
            daily_forecast = forecast.daily
        else:
            raise ValueError("daily_forecast is None")
        
        if forecast.hourly is not None: 
            hourly_forecast = forecast.hourly
        else:
            raise ValueError("hourly_forecast is None")
        
        hour_index_start = hourly_forecast.time.index(datetime_i)
        hour_index_stop = hour_index_start + 24
        
        day_index = 0

        try:
            self.precipitation_mm = daily_forecast.precipitation_sum[day_index] # pyright: ignore[reportOptionalSubscript]
            self.temp_c_max = daily_forecast.temperature_2m_max[day_index] # pyright: ignore[reportOptionalSubscript]
            self.temp_c_min = daily_forecast.temperature_2m_min[day_index] # pyright: ignore[reportOptionalSubscript]
            self.humidity = np.mean(hourly_forecast.relative_humidity_2m[hour_index_start:hour_index_stop], dtype=float) # pyright: ignore[reportOptionalSubscript]
            self.weather_code = daily_forecast.weathercode[day_index] # pyright: ignore[reportOptionalSubscript]
        except (TypeError, IndexError) as e:
            raise IndexError(f"Error fetching data at {datetime_i}: {e}")

@dataclass
class WeatherData:
    update_datetime: datetime.datetime
    current_weather: CurrentWeather
    suntimes: tuple[datetime.datetime, datetime.datetime]
    hourly_weathers: list[HourlyWeather]
    cum_day_weather: CumDayWeather

    def __init__(self, forecast: Forecast, datetime_i: datetime.datetime):
        if forecast.current_weather is None:
            raise ValueError("forecast.current_weather  is None")
        if forecast.daily is None or forecast.daily.sunrise is None:
            raise ValueError("forecast.daily.sunrise is None")
        if forecast.daily is None or forecast.daily.sunset is None:
            raise ValueError("forecast.daily.sunset is None")

        self.update_datetime = datetime_i
        self.current_weather = forecast.current_weather
        self.suntimes = forecast.daily.sunrise[0], forecast.daily.sunset[0]
        self.hourly_weathers = [HourlyWeather(forecast, datetime_i+datetime.timedelta(hours=h)) for h in range(12)]
        self.cum_day_weather = CumDayWeather(forecast, datetime_i)

    def __repr__(self) -> str:
        hourly_formatted = "".join([f"\n\t{h}" for h in self.hourly_weathers])

        return (
            f"DData(\n"
            f"  {self.current_weather}\n"
            f"  Suntimes={self.suntimes}\n"
            f"  cum_day={self.cum_day_weather}\n"
            f"  hourly=[{hourly_formatted}\n  ]\n"
            f")"
        )

class DataFetch():
    def __init__(self) -> None:
        pass

    async def getOpenMeteoData(self) -> Forecast:
        async with OpenMeteo() as open_meteo:
            forecast: Forecast = await open_meteo.forecast(
                latitude=krakow_loc.lat,
                longitude=krakow_loc.lon,
                current_weather=True,
                hourly=[
                    HourlyParameters.TEMPERATURE_2M,
                    HourlyParameters.WIND_SPEED_10M,
                    HourlyParameters.WIND_DIRECTION_10M,
                    HourlyParameters.PRECIPITATION,
                    HourlyParameters.CLOUD_COVER,
                    HourlyParameters.RELATIVE_HUMIDITY_2M,
                    HourlyParameters.WEATHER_CODE
                ],
                daily=[
                    DailyParameters.SUNRISE,
                    DailyParameters.SUNSET,
                    DailyParameters.WEATHER_CODE,
                    DailyParameters.TEMPERATURE_2M_MAX,
                    DailyParameters.TEMPERATURE_2M_MIN,
                    DailyParameters.PRECIPITATION_SUM
                ]
            )
        return forecast

    def __call__(self):
        forecast = None
        datetime_i = datetime.datetime.today()
        try:
            forecast = asyncio.run(self.getOpenMeteoData())
            self.forecast = forecast
            datetime_i = datetime.datetime.now()
            datetime_i = datetime_i.replace(minute=0, second=0, microsecond=0)

        except OpenMeteoConnectionError as e:
            log.error("Failed to connect to OpenMeteo API: {e}", exc_info=True)
            
        if self.forecast is None:
            log.critical("No forecast data available. Exiting application.")
            raise
        elif forecast is None:
            forecast = self.forecast
        

        return WeatherData(forecast, datetime_i)


if __name__ == "__main__":
    dfe = DataFetch()
    x = dfe()
    print(x)
