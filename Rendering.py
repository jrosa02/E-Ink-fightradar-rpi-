#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os
import copy
import numpy as np
import matplotlib.pyplot as plt

import logging
from PIL import Image,ImageDraw,ImageColor

class ImageRendering():
    def __init__(self, shape) -> None: 
        self.const_background = self._init_background(shape)
        self.image = copy.copy(self.const_background)
        self.viewer = Viewer()

    def _init_background(self, shape):
        return Image.new('1', shape, 255)

    def draw_basic_planes(self, planes):
        """        
        :param planes: List of position of planes
        """
        draw = ImageDraw.Draw(self.image)

        for plane in planes:
            draw.circle(plane, 8, fill="black")

    def render_basic(self, planes):
        self.image = copy.copy(self.const_background)
        self.draw_basic_planes(planes)

    def show_image(self):
        #PIL
        self.viewer.show_image(self.image)


    def __call__(self):
        pass

    def get_outputimage(self):
        return self.image
    
class Viewer:
    def __init__(self):
        self.fig, self.ax = plt.subplots()
        self.im = None
        plt.ion()  # interactive mode
        plt.show()

    def show_image(self, image):
        if self.im is None:
            self.im = self.ax.imshow(image)
            self.ax.axis("off")
        else:
            self.im.set_data(image)

        self.fig.canvas.draw_idle()
        plt.pause(1)

if __name__ == "__main__":
    viewer = Viewer()
    imr = ImageRendering((880, 576))

    imr.draw_basic_planes([[200, 400], [600, 200]])
    imr.show_image()