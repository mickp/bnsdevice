""" Wrapper around BNS Interface.dll """

from bnsdummy import BNSDevice
from itertools import chain, product
import os, re, numpy
from PIL import Image


class SpatialLightModulator(object):
    def __init__(self):
        self.LUTs = {}
        self.calibs = {}

        self._LUTFolder = "LUT_files"
        self._calibrationFolder = "Phase_Calibration_Files"
        self.load_calibration_data()

        self.hardware = BNSDevice()
        self.pixel_pitch = 15e-6
        self.pixels = (512, 512)
        self.hardware.initialize()

        self.sequence = []


    def generate_stripe_series(self, patternparms):
        """ Generate a stripe series from the patternparms.

        patternparms is a list of tuples:  (pitch, angle, phase),
        where pitch is in microns, and both the angle and phase are specified
        in radians.
        """
        self.sequence = []
        for realpitch, angle, phase in patternparms:
            pitch = realpitch / self.pixel_pitch

      


    def load_calibration_data(self):
        """ Loads any calibration data found below module path. """

        modpath = os.path.dirname(__file__)
        pattern = '(?P<slm>slm)(?P<serial>[0-9]{2,4})_(?P<wavelength>[0-9]{2,4})'

        path = os.path.join(modpath, self._calibrationFolder)
        if os.path.exists(path):
            # load calibration files
            files = os.listdir(path)
            for f in files:
                try:
                    im = Image.open(os.path.join(path, f))
                    if im.size == self.pixels:
                        calib = {}
                        calib['filename'] = f
                        calib['name'] = os.path.splitext(f)[0]
                        calib['data'] = numpy.array(im)

                        match = re.match(pattern, f)
                        if match:
                            calib['wavelength'] = match.group('wavelength')
                            self.calibs[calib['wavelength']] = calib
                        else:
                            calib['wavelength'] = 0
                            self.calibs[calib['name'].lower()] = calib

                except IOError:
                    # couldn't open the image file
                    pass
                except:
                    raise

        path = os.path.join(modpath, self._LUTFolder)
        if os.path.exists(path):
            files = os.listdir(path)
            for f in files:
                try:
                    lut = {}
                    lut['filename'] = f
                    lut['name'] = os.path.splitext(f)[0]
                    lut['data'] = numpy.loadtxt(os.path.join(path, f))

                    match = re.match(pattern, f)
                    if match:
                        lut['wavelength'] = match.group('wavelength')
                        self.LUTs[lut['wavelength']] = lut
                    else:
                        lut['wavelength'] = 0
                        self.LUTs[lut['name'].lower()] = lut
                except IOError:
                    # couldn't open the file
                    pass
                except:
                    raise


    def load_images(self):
        hardware.load_sequence(self.sequence)
        

    def run(self):
        self.hardware.power = True
        self.hardware.start_sequence()


    def stop(self):
        self.hardware.stop_sequence()
        self.hardware.power = False

