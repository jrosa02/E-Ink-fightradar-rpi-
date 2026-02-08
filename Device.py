#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os
picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'pic')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

import logging
from e_Paper.RaspberryPi_JetsonNano.python.lib.waveshare_epd import epd7in5_V2
from PIL import Image,ImageDraw,ImageFont


class DeviceRendering():
    def __init__(self) -> None:
        logging.info("epd7in5_V2")
        epd = epd7in5_V2.EPD()
        
        logging.info("init and Clear")
        epd.init()
        epd.Clear()