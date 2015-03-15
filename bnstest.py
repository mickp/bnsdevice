""" Tests for bnsdevice.

Copyright 2014-2015 Mick Phillips (mick.phillips at gmail dot com)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import bnsdevice as bns
import numpy as np
import ctypes
from time import sleep
from numpy import rint, cos, sin, pi

dev = bns.BNSDevice()
dev.initialize()
dev.load_lut('linear.lut')

cal = dev.read_tiff('white.tiff')
dev.write_cal(1, cal)

images = []
images.append(dev.read_tiff('16Astigx.tiff'))
images.append(dev.read_tiff('StripePer16.tiff'))
images.append(dev.read_tiff('16Comax.tiff'))

dev.write_image(images[0])
dev.power = True

sleep(5)

dev.load_sequence(images)
dev.start_sequence()

sleep(5)

ind = np.arange(512)
kk, ll = np.meshgrid(ind, ind)
ndarray_images = []
ndarray_images.append(np.ushort(32767 + ((kk % 32) > 15) * 65535/2))
ndarray_images.append(np.ushort(32767 + (((kk + ll) % 48) > 23 )* 65535/2))
ndarray_images.append(np.ushort(32767 + ((ll % 32) > 15) * 65535/2))

dev.stop_sequence()

dev.write_image(ndarray_images[0])

sleep(5)

dev.load_sequence(ndarray_images)
dev.start_sequence()