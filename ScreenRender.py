#!/usr/bin/python
# -*- coding:utf-8 -*-
from collections import namedtuple
import copy
import numpy as np
from datetime import datetime

import logging
from PIL import Image,ImageDraw,ImageColor, ImageFont
from DataFetch import DData

EDP7IN5_SHAPE = (800, 480)
BND_WIDTH = 0
BLACK = 0

RRoi = namedtuple("BBox", ["left", "upper", "right", "lower"])

def simple_panel_renderer(fill=1, outline=BLACK, width=BND_WIDTH):
    def decorator(func):
        def wrapper(self, roi_image, data, offset, *args, **kwargs):
            draw = ImageDraw.Draw(roi_image)

            draw.rectangle(
                [0, 0, roi_image.width - width//2, roi_image.height - width//2],
                outline=outline,
                fill=fill,
                width=width
            )

            result = func(self, draw, data)
            self.screen.paste(roi_image, offset, *args, **kwargs)
            return result
        return wrapper
    return decorator

class ScreenRender():
    def __init__(self, shape=EDP7IN5_SHAPE) -> None: 
        self.const_background = self._init_background(shape)
        self.screen = copy.copy(self.const_background)
        self._init_fonts([16, 22, 24, 32, 40, 48, 64, 110])

    def _init_fonts(self, sizes):
        self.DejaVu = {
            size: ImageFont.truetype("fonts/DejaVuSans.ttf", size=size)
            for size in sizes
        }
        self.weather_font = ImageFont.truetype("/home/jrosa/Private/E-Ink-fightradar-rpi-/fonts/easy_weather_icons_font.ttf", size=64)
        self.weather_font_big = ImageFont.truetype("/home/jrosa/Private/E-Ink-fightradar-rpi-/fonts/easy_weather_icons_font.ttf", size=150)

    def _init_background(self, shape):
        return Image.new('1', shape, 255)

    def render_parcels(self, data: DData):
        """
        Main function to render all modules.
        """
        big_panel_width = 160
        big_panel_hight = 180
        # Define ROIs: (left, upper, right, lower)
        datetime_roi = RRoi(0, 0, 800, 60)
        temp_roi = RRoi(0, 60, big_panel_width, 60+big_panel_hight)
        clouds_roi = RRoi(big_panel_width, 60, 2*big_panel_width, 60+big_panel_hight)
        precipitation_roi = RRoi(2*big_panel_width, 60, 3*big_panel_width, 60+big_panel_hight)
        wind_roi = RRoi(3*big_panel_width, 60, 4*big_panel_width, 60+big_panel_hight)
        moisture_roi = RRoi(4*big_panel_width, 60, 5*big_panel_width, 60+big_panel_hight)
        hour_count = 6
        hour_width = EDP7IN5_SHAPE[0]//hour_count
        # Define hourly ROIs: (left, upper, right, lower)
        hourly_rois = [RRoi(i*hour_width,60+big_panel_hight, (i+1)*hour_width, EDP7IN5_SHAPE[1]) for i in range(hour_count)]

        # Render each module
        self._render_datetime(self.screen.crop(datetime_roi), data, datetime_roi[:2])
        self._render_current_temperature(self.screen.crop(temp_roi), data, temp_roi[:2])
        self._render_clouds(self.screen.crop(clouds_roi), data, clouds_roi[:2])
        self._render_wind(self.screen.crop(wind_roi), data, wind_roi[:2])
        self._render_percipitation(self.screen.crop(precipitation_roi), data, precipitation_roi[:2])
        self._render_humidity(self.screen.crop(moisture_roi), data, moisture_roi[:2])

        self._render_hourly(data, hourly_rois)

    @simple_panel_renderer()
    def _render_datetime(self, draw, data: DData):
        draw.text((300, 15), f"{data.update_datetime.strftime("%Y-%m-%d %H:%M")}", font=self.DejaVu[24], fill=BLACK, align="center")

    @simple_panel_renderer()
    def _render_current_temperature(self, draw, data: DData):
        draw.text((10, 10), f"{data.temp:.0f}°", font=self.DejaVu[110], fill=BLACK)

    @simple_panel_renderer()
    def _render_clouds(self, draw, data: DData):
        draw.text((10, 10), self.weather_icon(data.hourly[0].clouds), font=self.weather_font_big, fill=BLACK)

    @simple_panel_renderer()
    def _render_percipitation(self, draw, data: DData):
        draw.text((10, 10), f"{int(data.hourly[0].precipitation)}", font=self.DejaVu[110], fill=BLACK)

    @simple_panel_renderer()
    def _render_wind(self, draw, data: DData):
        angle_to_arrow = lambda a: ["↑","↗","→","↘","↓","↙","←","↖"][-round(a / 45) % 8]
        angle_to_card = lambda a: ["S","SW","W","NW","N","NE","E","SE"][-round(a / 45) % 8]
        draw.text((50, 10), f"{angle_to_arrow(data.wind_direction)}", font=self.DejaVu[64], fill=BLACK)
        draw.text((50, 100), f"{angle_to_card(data.wind_direction)}", font=self.DejaVu[64], fill=BLACK)

    @simple_panel_renderer()
    def _render_humidity(self, draw, data: DData):
        draw.text((10, 10), f"{data.humidity}%", font=self.DejaVu[64], fill=BLACK)
        draw.text((10, 140), f"Moisture", font=self.DejaVu[22], fill=BLACK)


    def _render_hourly(self, data: DData, rois: list[RRoi]):

        def hr2_mean(seq, i, par, dtype=int):
            return np.mean([getattr(seq[i], par), getattr(seq[i+1], par)], dtype=dtype)

        for i, roi in enumerate(rois):
            hour = data.hourly[2*i].datetime.hour

            # create ROI image from screen
            roi_image = self.screen.crop((roi.left, roi.upper, roi.right, roi.lower))

            draw = ImageDraw.Draw(roi_image)


            # panel background
            draw.rectangle(
                [
                    0,
                    0,
                    roi_image.width - BND_WIDTH // 2,
                    roi_image.height - BND_WIDTH // 2,
                ],
                outline=BLACK,
                fill=1,
                width=BND_WIDTH,
            )

            # hour label
            draw.text(
                (20, roi_image.height - 60),
                f"{hour:02d}⁰⁰",
                font=self.DejaVu[40],
                fill=BLACK,
            )

            cloud_pct = hr2_mean(data.hourly, 2*i, "clouds", dtype=int)
            precipitation = hr2_mean(data.hourly, 2*i, "precipitation", dtype=int)
            temp_c = hr2_mean(data.hourly, 2*i, "temp_c", dtype=int)

            weather_symbol = self.weather_icon(cloud_pct, precipitation, temp_c, data.hourly[i].datetime, data.sun_times[0], data.sun_times[1])
            draw.text((roi_image.width // 2, 60), weather_symbol, font=self.weather_font)
            draw.text(
                (50, roi_image.height//2),
                f"{temp_c:d}°",
                font=self.DejaVu[40],
                fill=BLACK,
            )

            # paste back
            self.screen.paste(roi_image, (roi.left, roi.upper))
    
    @staticmethod
    def weather_icon(
        cloud_pct: float,
        precipitation_mm: float|None = None,
        temp_c: float|None = None,
        now: datetime|None = None,
        sunrise: datetime|None = None,
        sunset: datetime|None = None
    ) -> str:

        # ---------- day/night ----------
        if now is None or sunrise is None or sunset is None:
            night = False
        else:
            night = not (sunrise <= now <= sunset)

        # ---------- condition classification ----------
        if precipitation_mm is not None and precipitation_mm > 0:
            if temp_c is not None and temp_c <= 0:
                condition = "snow"
            elif precipitation_mm > 10:
                condition = "heavy_rain"
            else:
                condition = "rain"
        else:
            if cloud_pct <= 10:
                condition = "clear"
            elif cloud_pct <= 30:
                condition = "few_clouds"
            elif cloud_pct <= 60:
                condition = "scattered"
            elif cloud_pct <= 85:
                condition = "broken"
            else:
                condition = "overcast"

        # ---------- icon map (subset of font glyphs) ----------
        icons = {
            "clear":        ("\uE96D", "\uE96E"),
            "few_clouds":   ("\uE967", "\uE968"),
            "scattered":    ("\uE9D3", "\uE9D4"),
            "broken":       ("\uE9DF", "\uE9E0"),
            "overcast":     ("\uE961", "\uE962"),
            "rain":         ("\uE92E", "\uE932"),
            "heavy_rain":   ("\uE931", "\uE931"),
            "snow":         ("\uE940", "\uE941"),
            "wind":         ("\uE900", "\uE900"),  # fallback / generic
        }

        day_icon, night_icon = icons.get(condition, ("\uE900", "\uE900"))
        return night_icon if night else day_icon

    def reset_screen(self):
        self.screen = copy.copy(self.const_background)

    def show_image(self):
        # PIL
        self.screen.show()

    def __call__(self, ddata:DData):
        self.reset_screen()
        self.render_parcels(ddata)
        return self.get_outputimage()

    def get_outputimage(self):
        return copy.copy(self.screen)
