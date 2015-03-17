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
import logging
import socket, threading
import os, re, numpy
import Pyro4
from PIL import Image
from numpy import arange, cos, sin, pi, rint, meshgrid, zeros
from time import sleep

CONFIG_NAME = 'slm'
LOG_FORMAT = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
LOG_DATE_FORMAT = '%m-%d %H:%M'

logging.basicConfig(level=logging.INFO,
                    format=LOG_FORMAT,
                    datefmt=LOG_DATE_FORMAT,
                    filename='slmservice.log',
                    filemode='w')


class SpatialLightModulator(object):
    def __init__(self):
        # Logging
        loggerName = '.'.join([__name__, self.__class__.__name__])
        self.logger = logging.getLogger(loggerName)
        ## SLM geometry
        # Physical pitch in microns
        self.pixel_pitch = 15.0
        # SLM size in pixels
        self.pixels = (512, 512)
        # Might as well evaluate image indices only once
        x_range = arange(self.pixels[0])
        y_range = arange(self.pixels[1])
        self.kk, self.ll = meshgrid(x_range, y_range)
        ## Image sequence
        self.sequence = []
        ## Look-up tables and calibration data
        # Paths
        self._LUTFolder = "LUT_files"
        self._calibrationFolder = "Phase_Calibration_Files"
        # Mapped by wavelength
        self.luts = {}
        self.calibs = {}
        # Load calib. data and LUT files
        self.load_calibration_data()
        ## Connect to the hardware.
        self.hardware = BNSDevice()     
        self.hardware.initialize()


    def load_calibration_data(self):
        """ Loads any calibration data found below module path. """
        # module path
        modpath = os.path.dirname(__file__)
        # filename format
        pattern = r'(slm)?(?P<serial>[0-9]+)[_](at(?P<wavelength>[0-9]+))'

        ## Find calibration files
        path = os.path.join(modpath, self._calibrationFolder)
        if os.path.exists(path):
            files = os.listdir(path)
            matches = [re.match(pattern, f) for f in files]
        else:
            files = []
            matches = []

        ## Load any calibration files
        self.logger.info('Loading calibration files:')
        for f, match in zip(files, matches):
            if not match:
                # Not a calibration file.
                self.logger.warning('\tignoring %s' % f)
                continue
            try:
                im = Image.open(os.path.join(path, f))
            except IOError:
                self.logger.error('\tcould not open %s' % f)
                continue
            except:
                raise

            if im.size == self.pixels:
                try:
                    calib_data = numpy.array(im)
                except:
                    # Not a calibration file.
                    continue

            wavelength = int(match.groupdict()['wavelength'])
            self.calibs[wavelength] = calib_data
            self.logger.info("\tloaded data from %s." % f)

        ## Find lookup table files.        
        path = os.path.join(modpath, self._LUTFolder)
        if os.path.exists(path):
            files = os.listdir(path)
            matches = [re.match(pattern, f) for f in files]
        else:
            files = []
            matches = []

        self.logger.info('Loading LUT files:')
        for f, match in zip(files, matches):
            if not match:
                # This is not a LUT file.
                self.logger.warning('\tignoring %s' % f)
                continue

            try:
                # Load the second column of the LUT into an ndarray.
                lut_data = numpy.loadtxt(os.path.join(path, f), usecols=(1,))
            except (IOError):
                self.logger.error('\tcould not open %s' % f)
                continue
            except:
                raise

            wavelength = int(match.groupdict()['wavelength'])
            self.luts[wavelength] = lut_data
            self.logger.info("\tloaded data from %s" % f)

        return None


    def load_sequence(self):
        """ Loads images to the device. """
        if not self.sequence:
            raise Exception(
                'No data to load to SLM --- generate sequence then load.')
        else:
            self.hardware.load_sequence(self.sequence)
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
