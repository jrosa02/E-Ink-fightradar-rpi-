#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os
import abc
import platform
import logging
from PIL import Image
from ScreenRender import EDP7IN5_SHAPE


class ScreenDriver(abc.ABC):
    def __init__(self):
        self.width = EDP7IN5_SHAPE[0]
        self.height = EDP7IN5_SHAPE[1]

    @abc.abstractmethod
    def init(self):
        """Initialize the screen."""
        pass

    @abc.abstractmethod
    def update(self, image: Image.Image):
        """Update the screen with a PIL image."""
        pass

if "armv6l" in platform.uname().machine.lower():
    logging.info("Detected Raspberry Pi platform.")
    libdir = './e-Paper/RaspberryPi_JetsonNano/python/lib'
    if os.path.exists(libdir):
        sys.path.append(libdir)
    from waveshare_epd import epd7in5_V2

    class EpdScreenDriver(ScreenDriver):
        def __init__(self):
            super().__init__()
            self.epd = epd7in5_V2.EPD()
            self.init()

        def init(self):
            logging.info("Initializing e-paper display...")
            self.epd.init()
            self.epd.Clear()

        def update(self, image: Image.Image):
            logging.info("Updating e-paper display...")
            self.epd.display(self.epd.getbuffer(image))
            logging.info("Update done.")


# PC / simulation implementation
else:
    logging.info("Running on non-Raspberry platform: using simulation.")
    import matplotlib.pyplot as plt
    import numpy as np

    class SimScreenDriver(ScreenDriver):
        def __init__(self):
            super().__init__()
            self.fig = None
            # Enable interactive mode so show() doesn't block
            plt.ion() 

        def init(self):
            logging.info("Initializing simulated screen...")

        def update(self, image: Image.Image):
            logging.info("Updating simulated screen (non-blocking)...")
            
            if self.fig is None:
                self.fig, self.ax = plt.subplots()
                self.img_plot = self.ax.imshow(image, cmap='gray')
                plt.show(block=False)
            else:
                # Efficiently update the existing window
                self.img_plot = self.ax.imshow(image, cmap='gray')
            
            # Draw and pause briefly to process window events
            self.fig.canvas.draw()
            self.fig.canvas.flush_events()
            plt.pause(0.1)
                

# Factory function to decide which driver to use at runtime
def get_screen_driver() -> ScreenDriver:
    if "armv6l" in platform.uname().machine.lower():
        logging.info("Detected Raspberry Pi: using e-paper driver")
        return EpdScreenDriver()
    else:
        logging.info("Non-Raspberry platform: using simulated driver")
        return SimScreenDriver()