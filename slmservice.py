""" Provides access to an SLM device via Pyro. 

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

from bnsdevice import BNSDevice
from itertools import chain, product
import socket, threading
import os, re, numpy
import Pyro4
from PIL import Image
from numpy import arange, cos, sin, pi, rint, meshgrid, zeros
from time import sleep

CONFIG_NAME = 'slm'

class SpatialLightModulator(object):
    def __init__(self):
        self.LUTs = {}
        self.calibs = {}
        self.pixel_pitch = 15.0 # in microns
        self.pixels = (512, 512)

        self._LUTFolder = "LUT_files"
        self._calibrationFolder = "Phase_Calibration_Files"
        self.load_calibration_data()

        self.hardware = BNSDevice()
        self.hardware.initialize()

        self.sequence = []


    def generate_stripe_series(self, patternparms):
        """ Generate a stripe series from the patternparms.

        patternparms is a list of tuples:  (pitch, angle, phase, wavelength),
        where pitch is in microns, and both the angle and phase are specified
        in radians.  
        """
        self.sequence = []
        xindices = arange(self.pixels[0])
        yindices = arange(self.pixels[1])
        kk, ll = meshgrid(xindices, yindices)
        for realpitch, angle, phase, wavelength in patternparms:
            pitch = realpitch / self.pixel_pitch
            pattern = numpy.ushort(
                    rint(32767.5 + 32767.5 * cos(phase +
                    2 * pi * (cos(angle) * kk + sin(angle) * ll) / pitch)))
            self.sequence.append(pattern)
        return len(self.sequence)


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
        return None

    def load_images(self):
        """ Loads images to the device. """
        if not self.sequence:
            raise Exception(
                'No data to load to SLM --- generate sequence then load.')
        elif len(self.sequence) == 1:
            ## single image - does not need reshaping
            try:
                self.hardware.write_image(self.sequence[0])
            except:
                raise
        else:
            try:
                self.hardware.load_sequence([
                    numpy.reshape(pattern, -1).tolist()
                    for pattern in self.sequence])
            except:
                raise
        return None


    def run(self):
        """ Power on and make device respond to triggers. """
        self.hardware.power = True
        self.hardware.start_sequence()
        return None


    def stop(self):
        """ Power off and stop device responding to triggers. """
        self.hardware.stop_sequence()
        self.hardware.power = False
        return None


    def get_temperature(self):
        return self.hardware.temperature


    def get_power(self):
        return self.hardware.power


    def get_current_image_index(self):
        return self.hardware.curr_seq_image



class Server(object):
    def __init__(self):
        self.server = None
        self.daemon_thread = None
        self.config = None
        self.run_flag = True

    def __del__(self):
        self.run_flag = False


    def run(self):
        import readconfig
        config = readconfig.config

        host = config.get(CONFIG_NAME, 'ipAddress')
        port = config.getint(CONFIG_NAME, 'port')

        self.server = SpatialLightModulator()

        daemon = Pyro4.Daemon(port=port, host=host)

        # Start the daemon in a new thread.
        self.daemon_thread = threading.Thread(
            target=Pyro4.Daemon.serveSimple,
            args = ({self.server: 'pyroSLM'},),
            kwargs = {'daemon': daemon, 'ns': False}
            )
        self.daemon_thread.start()

        # Wait until run_flag is set to False.
        while self.run_flag:
            sleep(1)

        # Do any cleanup.
        daemon.shutdown()

        self.daemon_thread.join()


    def stop(self):
        self.run_flag = False


def main():
    server = Server()
    server_thread = threading.Thread(target = server.run)
    server_thread.start()
    try:
        while True:
            sleep(1)
    except (KeyboardInterrupt, SystemExit):
        server.stop()
        server_thread.join()


if __name__ == '__main__':
    main()
