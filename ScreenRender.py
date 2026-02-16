#!/usr/bin/python
# -*- coding:utf-8 -*-
from collections import namedtuple
import copy
import numpy as np
from datetime import datetime
from itertools import accumulate

import logging
from PIL import Image, ImageDraw, ImageColor, ImageFont
from DataFetch import WeatherData
from texts import TextsSelector

EDP7IN5_SHAPE = (800, 480)
BND_WIDTH = 1
BLACK = 0
WHITE = 1

RRoi = namedtuple("RRoi", ["left", "upper", "right", "lower"])


def simple_panel_renderer(fill=WHITE, outline=BLACK, width=BND_WIDTH):
    def decorator(func):
        def wrapper(self, roi_image, data, offset, *args, **kwargs):
            draw = ImageDraw.Draw(roi_image)

            draw.rectangle(
                [0, 0, roi_image.width - width // 2, roi_image.height - width // 2],
                outline=outline,
                fill=fill,
                width=width,
            )

            result = func(self, draw, data)
            self.screen.paste(roi_image, offset, *args, **kwargs)
            return result

        return wrapper

    return decorator


class ScreenRender:
    def __init__(self, shape=EDP7IN5_SHAPE) -> None:
        self.const_background = self._init_background(shape)
        self.screen = copy.copy(self.const_background)
        self._init_fonts([11, 12, 16, 22, 24, 32, 40, 48, 64, 110])
        self.text_selector = iter(TextsSelector(False))

    def _init_fonts(self, sizes):
        self.DejaVu = {
            size: ImageFont.truetype("./fonts/DejaVuSans.ttf", size=size)
            for size in sizes
        }
        self.DejaVuBold = {
            size: ImageFont.truetype("./fonts/DejaVuSans-Bold.ttf", size=size)
            for size in sizes
        }
        self.weather_font = ImageFont.truetype(
            "./fonts/easy_weather_icons_font.ttf", size=64
        )
        self.weather_font_middle = ImageFont.truetype(
            "./fonts/easy_weather_icons_font.ttf", size=96
        )
        self.weather_font_big = ImageFont.truetype(
            "./fonts/easy_weather_icons_font.ttf", size=150
        )

    def _init_background(self, shape):
        return Image.new("1", shape, WHITE)

    def render_parcels(self, data: WeatherData):
        scr_w = EDP7IN5_SHAPE[0]
        scr_h = EDP7IN5_SHAPE[1]

        header_h = 60
        panel_h = 200
        divider_h = 40
        footer_y = header_h + panel_h + divider_h

        ratios = [0.35, 0.20, 0.20, 0.15, 0.10]

        edges = [0] + list(accumulate(ratios))
        x_coords = [int(e * scr_w) for e in edges]

        x_coords[-1] = scr_w

        main_rois = [
            RRoi(x_coords[i], header_h, x_coords[i + 1], footer_y)
            for i in range(len(ratios))
        ]

        divider_roi = RRoi(0, header_h + panel_h, scr_w, footer_y)

        # 5. Hourly ROIs
        hour_count = 10
        h_step = scr_w // hour_count
        hourly_rois = [
            RRoi(i * h_step, footer_y, (i + 1) * h_step, scr_h)
            for i in range(hour_count)
        ]

        temp_roi, clouds_roi, precip_roi, wind_roi, humid_roi = main_rois

        tasks = [
            (self._render_datetime, RRoi(0, 0, scr_w, header_h)),
            (self._render_current_temperature, temp_roi),
            (self._render_weather_icon, clouds_roi),
            (self._render_percipitation, precip_roi),
            (self._render_wind, wind_roi),
            (self._render_humidity, humid_roi),
            (self._render_divider, divider_roi),
        ]

        for func, roi in tasks:
            func(self.screen.crop(roi), data, roi[:2])

        self._render_hourly(data, hourly_rois)

    @simple_panel_renderer(width=2)
    def _render_datetime(self, draw: ImageDraw.ImageDraw, data: WeatherData):
        w, h = draw.im.size
        draw.text(
            (w // 2, h // 2),
            f"{data.update_datetime.strftime("%Y-%m-%d %H:%M")}   ({datetime.now().strftime("%H:%M")})",
            font=self.DejaVuBold[24],
            fill=BLACK,
            anchor="mm",
        )

    @simple_panel_renderer()
    def _render_current_temperature(self, draw: ImageDraw.ImageDraw, data: WeatherData):
        w, h = draw.im.size
        draw.text(
            (w // 2, 30),
            f"{int(data.current_weather.temperature)}°",
            font=self.DejaVuBold[110],
            fill=BLACK,
            anchor="mt",
        )
        draw.text(
            (w // 2, 150),
            f"{int(data.cum_day_weather.temp_c_min)}° : {int(data.cum_day_weather.temp_c_max)}°",
            font=self.DejaVu[48],
            fill=BLACK,
            anchor="mt",
        )

    @simple_panel_renderer()
    def _render_weather_icon(self, draw, data: WeatherData):
        w, h = draw.im.size
        draw.text(
            (w // 2, h // 2 - 15),
            self.weather_icon(data.current_weather.weather_code),
            font=self.weather_font_big,
            fill=BLACK,
            anchor="mm",
        )

    @simple_panel_renderer()
    def _render_percipitation(self, draw: ImageDraw.ImageDraw, data: WeatherData):
        w, h = draw.im.size
        draw.text(
            (10, int(h * 2 / 5)),
            f"{10+int(data.hourly_weathers[0].precipitation)}",
            font=self.DejaVu[64],
            fill=BLACK,
            anchor="lb",
        )
        draw.text(
            (10, int(h * 3 / 4)),
            f"{int(data.cum_day_weather.precipitation_mm)}",
            font=self.DejaVu[64],
            fill=BLACK,
            anchor="lb",
        )
        draw.rectangle(
            (10, int(h * 2 / 5) + 15, w - 10, int(h * 2 / 5) + 25),
            fill=BLACK,
            outline=BLACK,
        )
        draw.text(
            (w - 10, int(h * 2 / 5)),
            f"mm/h",
            font=self.DejaVu[16],
            fill=BLACK,
            anchor="rb",
        )
        draw.text(
            (w - 10, int(h * 3 / 4)),
            f"mm/d",
            font=self.DejaVu[16],
            fill=BLACK,
            anchor="rb",
        )

    @simple_panel_renderer()
    def _render_wind(self, draw: ImageDraw.ImageDraw, data: WeatherData):
        w, h = draw.im.size
        angle_to_arrow = lambda a: [
            "↓",
            "↙",
            "←",
            "↖",
            "↑",
            "↗",
            "→",
            "↘",
        ][round(a / 45) % 8]
        angle_to_card = lambda a: ["N", "NE", "E", "SE", "S", "SW", "W", "NW"][
            round(a / 45) % 8
        ]
        draw.text(
            (w // 2, 50),
            f"{angle_to_arrow(data.current_weather.wind_direction)}",
            font=self.DejaVu[64],
            fill=BLACK,
            anchor="mm",
        )
        draw.text(
            (w // 2, 100),
            f"{angle_to_card(data.current_weather.wind_direction)}",
            font=self.DejaVu[64],
            fill=BLACK,
            anchor="mt",
        )

    @simple_panel_renderer()
    def _render_humidity(self, draw: ImageDraw.ImageDraw, data: WeatherData):
        draw.text(
            (10, 10),
            f"{int(data.cum_day_weather.humidity)}%",
            font=self.DejaVu[64],
            fill=BLACK,
            direction="ttb",
        )

    @simple_panel_renderer()
    def _render_divider(self, draw: ImageDraw.ImageDraw, data: WeatherData):
        w, h = draw.im.size
        draw.rectangle([0, 0, w, h], fill=BLACK)
        text = next(self.text_selector)
        text_size = self.get_text_size(text)
        draw.text(
            (w // 2, h // 2), text, font=self.DejaVu[text_size], fill=WHITE, anchor="mm"
        )

    @staticmethod
    def get_text_size(text: str):
        lines = text.split("\n")
        lines_nr = len(lines)
        return 22 // lines_nr

    def _render_hourly(self, data: WeatherData, rois: list[RRoi]):

        for i, roi in enumerate(rois):
            hour = data.hourly_weathers[i].datetime_d.hour + 1

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
                (w // 2, roi_image.height - int(roi_image.height / 3.5)),
                f"{hour:02d}ʰ",
                font=self.DejaVu[40],
                fill=BLACK,
                anchor="mt",
            )

            temp_c = int(data.hourly_weathers[i].temp_c)

            weather_symbol = self.weather_icon(data.hourly_weathers[i].weather_code)
            draw.text(
                (w // 2, roi_image.height // 10),
                weather_symbol,
                font=self.weather_font,
                fill=BLACK,
                anchor="mt",
            )
            draw.text(
                (w // 2, int(roi_image.height / 2.1)),
                f"{temp_c:d}°",
                font=self.DejaVu[40],
                fill=BLACK,
                anchor="mt",
            )

            # paste back
            self.screen.paste(roi_image, (roi.left, roi.upper))

    @staticmethod
    def weather_icon(
        wmo: int,
        now: datetime | None = None,
        sunrise: datetime | None = None,
        sunset: datetime | None = None,
    ) -> str:
        # 1. Day/Night index (0 = Day, 1 = Night)
        is_night = now and sunrise and sunset and not (sunrise <= now <= sunset)
        idx = 1 if is_night else 0

        # 2. WMO to Font Glyph Mapping (\uE9xx range)
        match wmo:
            case 0:
                return ("\ue96d", "\u263e")[idx]  # Clear (Sun/Moon)
            case 1 | 2:
                return ("\ue967", "\ue968")[idx]  # Few Clouds
            case 3:
                return ("\ue961", "\ue962")[idx]  # Overcast
            case 45 | 48:
                return ("\ue901", "\ue901")[idx]  # Fog
            case 51 | 53 | 55:
                return ("\ue92e", "\ue932")[idx]  # Drizzle
            case 61 | 63 | 80 | 81:
                return ("\ue92e", "\ue932")[idx]  # Rain
            case 65 | 82:
                return ("\ue931", "\ue931")[idx]  # Heavy Rain
            case 71 | 73 | 75 | 77 | 85 | 86:
                return ("\ue940", "\ue941")[idx]  # Snow
            case _ if wmo >= 95:
                return ("\ue950", "\ue950")[idx]  # Thunderstorm
            case _:
                return ("\ue900", "\ue900")[idx]  # Fallback (Wind/Generic)

    def reset_screen(self):
        self.screen = copy.copy(self.const_background)

    def show_image(self):
        # PIL
        self.screen.show()

    def __call__(self, ddata: WeatherData):
        self.reset_screen()
        self.render_parcels(ddata)
        return self.get_outputimage()

    def get_outputimage(self):
        return copy.copy(self.screen)
