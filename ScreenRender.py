#!/usr/bin/python
# -*- coding:utf-8 -*-
from collections import namedtuple
import random
import sys
import os
import copy
import numpy as np
import matplotlib.pyplot as plt

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
        hourly_rois = [RRoi(i*big_panel_width,60+big_panel_hight, (i+1)*big_panel_width,EDP7IN5_SHAPE[1]) for i in range(7)]

        # Render each module
        self._render_datetime(self.screen.crop(datetime_roi), data, datetime_roi[:2])
        self._render_current_temperature(self.screen.crop(temp_roi), data, temp_roi[:2])
        self._render_clouds(self.screen.crop(clouds_roi), data, clouds_roi[:2])
        self._render_wind(self.screen.crop(wind_roi), data, wind_roi[:2])
        self._render_percipitation(self.screen.crop(precipitation_roi), data, precipitation_roi[:2])
        self._render_moisture(self.screen.crop(moisture_roi), data, moisture_roi[:2])

        self._render_hourly(data, hourly_rois)

    @simple_panel_renderer()
    def _render_datetime(self, draw, data: DData):
        draw.text((300, 15), f"{data.update_datetime.strftime("%Y-%m-%d %H:%M")}", font=self.DejaVu[24], fill=BLACK, align="center")

    @simple_panel_renderer()
    def _render_current_temperature(self, draw, data: DData):
        draw.text((10, 10), f"{data.curr_temp:.0f}°", font=self.DejaVu[110], fill=BLACK)

    @simple_panel_renderer()
    def _render_clouds(self, draw, data: DData):
        draw.text((10, 10), f"🌣", font=self.DejaVu[110], fill=BLACK)

    @simple_panel_renderer()
    def _render_percipitation(self, draw, data: DData):
        draw.text((10, 10), f"C1", font=self.DejaVu[110], fill=BLACK)

    @simple_panel_renderer()
    def _render_wind(self, draw, data: DData):
        angle_to_arrow = lambda a: ["↑","↗","→","↘","↓","↙","←","↖"][-round(a / 45) % 8]
        angle_to_card = lambda a: ["S","SW","W","NW","N","NE","E","SE"][-round(a / 45) % 8]
        draw.text((50, 10), f"{angle_to_arrow(data.curr_wind_direction)}", font=self.DejaVu[64], fill=BLACK)
        draw.text((50, 100), f"{angle_to_card(data.curr_wind_direction)}", font=self.DejaVu[64], fill=BLACK)

    @simple_panel_renderer()
    def _render_moisture(self, draw, data: DData):
        draw.text((10, 10), f"80%", font=self.DejaVu[64], fill=BLACK)
        draw.text((10, 140), f"Moisture", font=self.DejaVu[22], fill=BLACK)


    def _render_hourly(self, data: DData, rois: list[RRoi]):

        for i, roi in enumerate(rois):
            hour = (data.update_datetime.hour + i + 1) % 24

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
                f"{hour:02d}:00",
                font=self.DejaVu[40],
                fill=BLACK,
            )
            draw.circle((roi_image.width // 2, 60), 40)
            draw.text(
                (50, roi_image.height//2),
                f"{random.randint(-10, 10)}°",
                font=self.DejaVu[40],
                fill=BLACK,
                align='center'
            )

            # paste back
            self.screen.paste(roi_image, (roi.left, roi.upper))

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
