#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os
import copy
import numpy as np
import matplotlib.pyplot as plt

import logging
from PIL import Image,ImageDraw,ImageColor, ImageFont
from DataFetch import DData

EDP7IN5_SHAPE = (800, 480)

class ScreenRender():
    def __init__(self, shape=EDP7IN5_SHAPE) -> None: 
        self.const_background = self._init_background(shape)
        self.screen = copy.copy(self.const_background)

        self.font24 = ImageFont.load_default(size=24)
        self.font18 = ImageFont.load_default(size=18)

    def _init_background(self, shape):
        return Image.new('1', shape, 255)
    
    def render_data(self, data: DData):
        """
        Main function to render all modules.
        """
        # Define ROIs: (left, upper, right, lower)
        header_roi = (0, 0, 800, 60)
        temp_roi = (0, 60, 440, 120)
        wind_roi = (440, 60, 800, 120)

        # Render each module
        self._render_header(self.screen.crop(header_roi), data, header_roi[:2])
        self._render_temperature(self.screen.crop(temp_roi), data, temp_roi[:2])
        self._render_wind(self.screen.crop(wind_roi), data, wind_roi[:2])

    def _render_header(self, roi_image, data: DData, offset):
        """
        Render the top header module.
        roi_image: cropped Image instance (will paste back)
        offset: top-left corner of the ROI relative to full image
        """
        draw = ImageDraw.Draw(roi_image)
        BLACK = 0

        draw.rectangle([0, 0, roi_image.width-1, roi_image.height-1], outline=BLACK, fill=1)
        draw.text((10, 10), f"Update: {data.update_datetime}", font=self.font24, fill=BLACK)
        draw.text((440, 10), f"Forecast Time: {data.forecast_datetime}", font=self.font24, fill=BLACK)

        # Paste back the modified ROI
        self.screen.paste(roi_image, offset)

    def _render_temperature(self, roi_image, data: DData, offset):
        draw = ImageDraw.Draw(roi_image)
        BLACK = 0

        draw.rectangle([0, 0, roi_image.width-1, roi_image.height-1], outline=BLACK, fill=1)
        draw.text((10, 10), f"Temp: {data.curr_temp} °C", font=self.font18, fill=BLACK)

        self.screen.paste(roi_image, offset)

    def _render_wind(self, roi_image, data: DData, offset):
        draw = ImageDraw.Draw(roi_image)
        BLACK = 0

        draw.rectangle([0, 0, roi_image.width-1, roi_image.height-1], outline=BLACK, fill=1)
        draw.text((10, 10), f"Wind Speed: {data.curr_wind_speed} m/s", font=self.font18, fill=BLACK)
        draw.text((10, 35), f"Wind Dir: {data.curr_wind_direction}", font=self.font18, fill=BLACK)

        self.screen.paste(roi_image, offset)

    def reset_screen(self):
        self.screen = copy.copy(self.const_background)

    def show_image(self):
        #PIL
        self.screen.show()

    def __call__(self, ddata:DData):
        self.reset_screen()
        self.render_data(ddata)
        return self.get_outputimage()

    def get_outputimage(self):
        return copy.copy(self.screen)
    
if __name__ == "__main__":
    imr = ScreenRender()
    imr.render_data(DData(1, 2, 3, 4))
    imr.show_image()