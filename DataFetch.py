from collections import namedtuple
import pandas as pd
import asyncio
import datetime

from open_meteo import OpenMeteo, Forecast
from open_meteo.models import DailyParameters, HourlyParameters


BBox = namedtuple("BBox", ["min_lon", "min_lat", "max_lon", "max_lat"])
LLoc = namedtuple("LLoc", ["lat", "lon"])

poland_bbox = BBox(
    min_lon=14.07,
    min_lat=49.00,
    max_lon=24.15,
    max_lat=54.84,
)

krakow_loc = LLoc(50.061667, 19.9375)

DData = namedtuple("DData", ["update_datetime", "forecast_datetime", "curr_temp", "curr_wind_speed", "curr_wind_direction"])

class DataFetch():
    def __init__(self) -> None:
        pass

    async def getOpenMeteoData(self):
        async with OpenMeteo() as open_meteo:
            forecast = await open_meteo.forecast(
                latitude=krakow_loc.lat,
                longitude=krakow_loc.lon,
                current_weather=True,
                daily=[
                    DailyParameters.SUNRISE,
                    DailyParameters.SUNSET,
                    DailyParameters.PRECIPITATION_HOURS
                ],
            )
        return forecast

    def populate_tuple(self, forecast: Forecast):
        for_datetime = forecast.current_weather.time
        temp = forecast.current_weather.temperature
        wind_dir = forecast.current_weather.wind_direction
        wind_speed = forecast.current_weather.wind_speed
        ddata = DData(
            update_datetime=datetime.datetime.now(),
            forecast_datetime=for_datetime.strftime("%Y-%m-%d %H:%M"),
            curr_temp=temp,
            curr_wind_direction=wind_dir,
            curr_wind_speed=wind_speed,
        )
        return ddata

    def __call__(self):
        forecast = asyncio.run(self.getOpenMeteoData())
        return self.populate_tuple(forecast)


if __name__ == "__main__":
    dfe = DataFetch()
    print(dfe())
