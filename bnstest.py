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
import os
from time import sleep
from numpy import rint, cos, sin, pi, meshgrid


MOD_PATH = os.path.dirname(__file__)
LUT_PATH = os.path.join(MOD_PATH, 'LUT_files')
CAL_PATH = os.path.join(MOD_PATH, 'Phase_Calibration_files')
TEST_PATH = os.path.join(MOD_PATH, 'Test_files')


def generate_stripe_series(patternparms):
    """ Generate a stripe series from the patternparms.

    patternparms is a list of tuples:  (pitch, angle, phase, wavelength),
    where pitch is in microns, and both the angle and phase are specified
    in radians.  
    """
    sequence = []
    xindices = np.arange(512)
    yindices = np.arange(512)
    kk, ll = meshgrid(xindices, yindices)
    for realpitch, angle, phase, wavelength in patternparms:
        pitch = realpitch / 15.0
        # Factor to balance m=0,+/-1 orders.
        mp2 = 1.5 
        pattern = np.ushort(
                rint((mp2 / pi) * 32767.5 + 32767.5 * cos(phase +
                2 * pi * (cos(angle) * kk + sin(angle) * ll) / pitch)))
        # Scale to green LUT range
        pattern *= 16256. / 65535.
        pattern += 49279.
        sequence.append(pattern)
    return sequence


# Load a LUT.
dev = bns.BNSDevice()
dev.initialize()
print "Loadint LUT %s." % os.path.join(LUT_PATH, 'linear.lut')
dev.load_lut(os.path.join(LUT_PATH, 'linear.lut'))

# Set the calibration to flat.
cal = dev.read_tiff(os.path.join(TEST_PATH, 'white.tiff'))
dev.write_cal(1, cal)


# Generate test images from TIFFs.
images = []
test_files = os.listdir(TEST_PATH)
print "Loading test files:"
for f in test_files:
    print "  %s" % f
    images.append(dev.read_tiff(f))


# Numerically-generated test images.
ind = np.arange(512)
kk, ll = np.meshgrid(ind, ind)
ndarray_images = []
ndarray_images.append(np.ushort(32767 + ((kk % 32) > 15) * 65535/2))
ndarray_images.append(np.ushort(32767 + (((kk + ll) % 48) > 23 )* 65535/2))
ndarray_images.append(np.ushort(32767 + ((ll % 32) > 15) * 65535/2))


# Show a single TIFF-derived image for five seconds.
print "Single image from TIFF."
dev.write_image(images[0])
dev.power = True
sleep(5)

# Run the TIFF-derived cycle for five seconds.
print "TIFF series"
dev.load_sequence(images)
dev.start_sequence()
sleep(5)


dev.stop_sequence()

# Show a single numerically-generated image for five seconds.
print "Single image from ndarray."
dev.write_image(ndarray_images[0])

# Run the numerically-generated series for five seconds
print "ndarray series."
dev.load_sequence(ndarray_images)
dev.start_sequence()
sleep(5)
