#!/usr/bin/python
# -*- coding:utf-8 -*-
from collections import namedtuple
import copy
import numpy as np
from datetime import datetime
from itertools import accumulate

import logging
from PIL import Image,ImageDraw,ImageColor, ImageFont
from DataFetch import WeatherData

EDP7IN5_SHAPE = (800, 480)
BND_WIDTH = 0
BLACK = 1
WHITE = 0

RRoi = namedtuple("RRoi", ["left", "upper", "right", "lower"])

def simple_panel_renderer(fill=WHITE, outline=BLACK, width=BND_WIDTH):
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
            size: ImageFont.truetype("./fonts/DejaVuSans.ttf", size=size)
            for size in sizes
        }
        self.DejaVuBold = {
            size: ImageFont.truetype("./fonts/DejaVuSans-Bold.ttf", size=size)
            for size in sizes
        }
        self.weather_font = ImageFont.truetype("./fonts/easy_weather_icons_font.ttf", size=64)
        self.weather_font_big = ImageFont.truetype("./fonts/easy_weather_icons_font.ttf", size=150)

    def _init_background(self, shape):
        return Image.new('1', shape, WHITE)

    def render_parcels(self, data: WeatherData):
        # 1. Dimensions - Ensure we have the correct Width vs Height
        # Typically: Index 1 is Width (800), Index 0 is Height (480)
        scr_w = EDP7IN5_SHAPE[0]
        scr_h = EDP7IN5_SHAPE[1]
        
        header_h = 60
        panel_h = 200
        divider_h = 30
        footer_y = header_h + panel_h + divider_h

        # 2. Normalized Widths (Must sum to 1.0)
        ratios = [0.35, 0.20, 0.15, 0.10, 0.20]
        
        # 3. Calculate X-coordinates (Edges)
        # [0, 0.25, 0.45, 0.60, 0.80, 1.0] * screen_width
        edges = [0] + list(accumulate(ratios))
        x_coords = [int(e * scr_w) for e in edges]
        
        # Ensure the last pixel is exactly the screen edge to avoid rounding gaps
        x_coords[-1] = scr_w

        # 4. Generate Main ROIs by pairing adjacent x-coordinates
        # This guarantees 'right' is always >= 'left'
        main_rois = [
            RRoi(x_coords[i], header_h, x_coords[i+1], footer_y)
            for i in range(len(ratios))
        ]

        divider_roi = RRoi(0, header_h+panel_h, scr_w, footer_y)

        # 5. Hourly ROIs
        hour_count = 10
        h_step = scr_w // hour_count
        hourly_rois = [
            RRoi(i * h_step, footer_y, (i + 1) * h_step, scr_h)
            for i in range(hour_count)
        ]

        # 6. Render Mapping
        # Unpack main_rois into the specific modules
        temp_roi, clouds_roi, precip_roi, wind_roi, humid_roi = main_rois

        tasks = [
            (self._render_datetime, RRoi(0, 0, scr_w, header_h)),
            (self._render_current_temperature, temp_roi),
            (self._render_clouds, clouds_roi),
            (self._render_percipitation, precip_roi),
            (self._render_wind, wind_roi),
            (self._render_humidity, humid_roi),
            (self._render_divider, divider_roi)
        ]

        for func, roi in tasks:
            # Debug print if you still encounter issues:
            # print(f"Rendering {func.__name__} at {roi}")
            func(self.screen.crop(roi), data, roi[:2])

        self._render_hourly(data, hourly_rois)

    @simple_panel_renderer(width=2)
    def _render_datetime(self, draw: ImageDraw.ImageDraw, data: WeatherData):
        w, h = draw.im.size
        draw.text((w//2, h//2), f"{data.update_datetime.strftime("%Y-%m-%d %H:%M")}", font=self.DejaVu[24], fill=BLACK, anchor='mm')

    @simple_panel_renderer()
    def _render_current_temperature(self, draw: ImageDraw.ImageDraw, data: WeatherData):
        w, h = draw.im.size
        draw.text((w//2, 30), f"{int(data.current_weather.temperature)}°", font=self.DejaVuBold[110], fill=BLACK, anchor="mt")
        draw.text((w//2, 150), f"{int(data.cum_day_weather.temp_c_min)}:{int(data.cum_day_weather.temp_c_max)}°", font=self.DejaVu[48], fill=BLACK, anchor="mt")

    @simple_panel_renderer()
    def _render_clouds(self, draw, data: WeatherData):
        draw.text((10, 10), self.weather_icon(data.current_weather.weather_code), font=self.weather_font_big, fill=BLACK)

    @simple_panel_renderer()
    def _render_percipitation(self, draw: ImageDraw.ImageDraw, data: WeatherData):
        draw.text((10, 10), f"{int(data.hourly_weathers[0].precipitation)}", font=self.DejaVu[64], fill=BLACK)
        draw.text((10, 80), f"{int(data.cum_day_weather.precipitation_mm)}", font=self.DejaVu[64], fill=BLACK)
        draw.text((60, 35), f"\uEA0D", font=self.weather_font, fill=BLACK)
        draw.text((60, 100), f"mm", font=self.DejaVu[32], fill=BLACK)

    @simple_panel_renderer()
    def _render_wind(self, draw: ImageDraw.ImageDraw, data: WeatherData):
        w, h = draw.im.size
        angle_to_arrow = lambda a: ["↓","↙","←","↖","↑","↗","→","↘",][round(a / 45) % 8]
        angle_to_card = lambda a: ["N","NE","E","SE", "S","SW","W","NW"][round(a / 45) % 8]
        draw.text((w//2, 10), f"{angle_to_arrow(data.current_weather.wind_speed)}", font=self.DejaVu[64], fill=BLACK, anchor='mt')
        draw.text((w//2, 100), f"{angle_to_card(data.current_weather.wind_direction)}", font=self.DejaVu[64], fill=BLACK, anchor='mt')
        

    @simple_panel_renderer()
    def _render_humidity(self, draw: ImageDraw.ImageDraw, data: WeatherData):
        draw.text((10, 10), f"{int(data.cum_day_weather.humidity)}%", font=self.DejaVu[64], fill=BLACK)
        draw.text((10, 140), f"Moisture", font=self.DejaVu[22], fill=BLACK)

    @simple_panel_renderer()
    def _render_divider(self, draw: ImageDraw.ImageDraw, data: WeatherData):
        w, h = draw.im.size
        draw.rectangle([0, 0, w, h], fill=BLACK)
        draw.text((w//2, h//2), "Miejsce na twoją reklamę", font=self.DejaVu[32], fill=WHITE, anchor='mm')


    def _render_hourly(self, data: WeatherData, rois: list[RRoi]):

        for i, roi in enumerate(rois):
            hour = data.hourly_weathers[i].datetime_d.hour+1

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
                fill=WHITE,
                width=BND_WIDTH,
            )

            w, h = draw.im.size
            # hour label
            draw.text(
                (w//2, roi_image.height - int(roi_image.height/3.5)),
                f"{hour:02d}⁰",
                font=self.DejaVu[40],
                fill=BLACK,
                anchor="mt"
            )

            temp_c = int(data.hourly_weathers[i].temp_c)

            weather_symbol = self.weather_icon(data.hourly_weathers[i].weather_code)
            draw.text((w//2, roi_image.height//10), weather_symbol, font=self.weather_font, fill=BLACK, anchor="mt")
            draw.text(
                (w//2, int(roi_image.height/2.1)),
                f"{temp_c:d}°",
                font=self.DejaVu[40],
                fill=BLACK,
                anchor="mt"
            )

            # paste back
            self.screen.paste(roi_image, (roi.left, roi.upper))

    @staticmethod
    def weather_icon(
        wmo: int,
        now: datetime | None = None,
        sunrise: datetime | None = None,
        sunset: datetime | None = None
    ) -> str:
        # 1. Day/Night index (0 = Day, 1 = Night)
        is_night = now and sunrise and sunset and not (sunrise <= now <= sunset)
        idx = 1 if is_night else 0

        # 2. WMO to Font Glyph Mapping (\uE9xx range)
        match wmo:
            case 0:                             return ("\uE96D", "\u263E")[idx] # Clear (Sun/Moon)
            case 1 | 2:                         return ("\uE967", "\uE968")[idx] # Few Clouds
            case 3:                             return ("\uE961", "\uE962")[idx] # Overcast
            case 45 | 48:                       return ("\uE901", "\uE901")[idx] # Fog
            case 51 | 53 | 55:                  return ("\uE92E", "\uE932")[idx] # Drizzle
            case 61 | 63 | 80 | 81:             return ("\uE92E", "\uE932")[idx] # Rain
            case 65 | 82:                       return ("\uE931", "\uE931")[idx] # Heavy Rain
            case 71 | 73 | 75 | 77 | 85 | 86:   return ("\uE940", "\uE941")[idx] # Snow
            case _ if wmo >= 95:                return ("\uE950", "\uE950")[idx] # Thunderstorm
            case _:                             return ("\uE900", "\uE900")[idx] # Fallback (Wind/Generic)

    def reset_screen(self):
        self.screen = copy.copy(self.const_background)

    def show_image(self):
        # PIL
        self.screen.show()

    def __call__(self, ddata:WeatherData):
        self.reset_screen()
        self.render_parcels(ddata)
        return self.get_outputimage()

    def get_outputimage(self):
        return copy.copy(self.screen)
