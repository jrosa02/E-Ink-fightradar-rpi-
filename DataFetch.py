from collections import namedtuple
from dataclasses import dataclass, fields
from typing import Iterable
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

DHour = namedtuple("DHour", ["datetime", "temp_c", "clouds", "precipitation"])
DData = namedtuple("nDData", ["update_datetime", "temp", "wind_speed", "wind_direction", "humidity", "sun_times", "hourly"])

class DataFetch():
    def __init__(self) -> None:
        pass

    async def getOpenMeteoData(self):
        async with OpenMeteo() as open_meteo:
            forecast = await open_meteo.forecast(
                latitude=krakow_loc.lat,
                longitude=krakow_loc.lon,
                current_weather=True,
                hourly=[
                    HourlyParameters.TEMPERATURE_2M,
                    HourlyParameters.WIND_SPEED_10M,
                    HourlyParameters.WIND_DIRECTION_10M,
                    HourlyParameters.PRECIPITATION,
                    HourlyParameters.CLOUD_COVER,
                    HourlyParameters.RELATIVE_HUMIDITY_2M
                ],
                daily=[
                    DailyParameters.SUNRISE,
                    DailyParameters.SUNSET
                ]
            )
        return forecast

    @staticmethod
    def forecast_to_hourly_list(dc: object, i: int) -> list[DHour]:
        field_names = [f.name for f in fields(dc)]
        columns = [getattr(dc, name) for name in field_names]
        print(dc.time)

        def pack_row(idx: int) -> DHour:
            row = {name: col[idx] if isinstance(col, Iterable)else 0 for name, col in zip(field_names, columns)}
            return DHour(
                datetime=row["time"],
                temp_c=row["temperature_2m"],
                clouds=row["cloud_cover"],
                precipitation=row["precipitation"],
            )

        return [pack_row(idx) for idx in range(i)]

    def populate_tuple(self, forecast: Forecast):
        for_datetime = forecast.current_weather.time
        temp = forecast.current_weather.temperature
        wind_dir = forecast.current_weather.wind_direction
        wind_speed = forecast.current_weather.wind_speed
        humidity = forecast.hourly.relative_humidity_2m[0]
        sunrise = forecast.daily.sunrise[0]
        sunset = forecast.daily.sunset[0]

        ddata = DData(
            update_datetime=datetime.datetime.now(),
            temp=temp,
            wind_direction=wind_dir,
            wind_speed=wind_speed,
            humidity=humidity,
            sun_times=(sunrise, sunset),
            hourly=self.forecast_to_hourly_list(forecast.hourly, 12)
        )
        return ddata

    def __call__(self):
        forecast = asyncio.run(self.getOpenMeteoData())
        return self.populate_tuple(forecast)


if __name__ == "__main__":
    dfe = DataFetch()
    x = dfe()
    print(x)
