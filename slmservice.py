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
from numpy import arange, cos, sin, pi, rint, meshgrid, zeros, amax, amin
from time import sleep

CONFIG_NAME = 'slm'
LOG_FORMAT = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
LOG_DATE_FORMAT = '%m-%d %H:%M'
TWO_PI = 2. * pi

#Pyro4.config.SERIALIZERS_ACCEPTED.remove('serpent')
Pyro4.config.SERIALIZERS_ACCEPTED.add('pickle')
#Pyro4.config.SERIALIZER='pickle'
Pyro4.config.REQUIRE_EXPOSE = False

logging.basicConfig(level=logging.INFO,
                    format=LOG_FORMAT,
                    datefmt=LOG_DATE_FORMAT,
                    filename='slmservice.log',
                    filemode='w')


@Pyro4.expose
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
        self.sequence_parameters = []
        ## SIM parameters
        self.sim_phase_offset = 0
        self.sim_angle_offset = TWO_PI / 5.
        self.sim_num_phases = 5
        self.sim_num_angles = 3
        self.sim_diffraction_angle = 0.35 # degrees was 0.5 then .25  
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
        ## Initialize the hardware.
        self.hardware.initialize()


    def get_sequence(self):
        return self.sequence


    def get_sim_sequence(self):
        return self.sequence_parameters


    def set_sim_sequence(self, angle_phase_wavelength):
        """ Generate a SIM sequence from a list of parameters.

        angle_phase_wavelength is a list where each element is a tuple of the 
        form (angle_number, phase_number, wavelength).
        """
        num_phases = 0
        num_angles = 0
        wavelengths = []
        for (angle, phase, wavelength) in angle_phase_wavelength:
            num_phases = max(num_phases, phase + 1)
            num_angles = max(num_angles, angle + 1)
            if wavelength not in wavelengths:
                wavelengths.append(wavelength)

        phases = [self.sim_phase_offset + n * TWO_PI / num_phases
                    for n in range(num_phases)]
        angles = [self.sim_angle_offset + n * TWO_PI / num_angles
                    for n in range(num_angles)]

        ## Calculate line pitches for each wavelength, once.
        # d  = m * wavelength / sin theta
        # 1/1000 since wavelength in nm, pixel pitch in microns.
        pitches = {w: w / (1000. * sin(self.sim_diffraction_angle * TWO_PI / 360.))
                     for w in wavelengths}
        ## Figure out the LUTs we need for each wavelength, once.
        luts = {w: self.get_lut(w) for w in set(wavelengths)}

        # retardation for equal powers in 0 and combined +/-1 orders
        modulation = 65535 * 150. / 360.0

        sequence = []
        for (angle, phase, wavelength) in angle_phase_wavelength:
            pp = pitches[wavelength] / self.pixel_pitch
            th = angles[angle]
            ph = phases[phase]
            # Create a stripe 16-bit pattern
            pattern16 = numpy.ushort(
                rint(
                    (0.5 * modulation) + (0.5 * modulation) * cos(
                        ph + TWO_PI * (cos(th) * self.kk + sin(th) * self.ll)
                        / pp)
                    ))              
            # Lose two LSBs and pass through the LUT for given wavelength.
            pattern = luts[wavelength][pattern16 // 4]
            # Append to the sequence.
            sequence.append(pattern)
        self.sequence_parameters = angle_phase_wavelength
        self.sequence = sequence
        self.load_sequence()


    def dump_sequence(self):
        from matplotlib import pyplot as plt
        for n, im in enumerate(self.sequence):
            fn = ''.join(['-', str(n), '.jpeg'])
            implot = plt.imshow(im)
            implot.set_cmap('gray')
            plt.savefig(fn)
        return (amin(self.sequence), amax(self.sequence))


    def get_lut(self, wavelength):
        """ Returns the LUT closest to wavelength. """
        lut_wavelengths = self.luts.keys()
        nearest = min(lut_wavelengths, key=lambda x: abs(x - wavelength))
        return self.luts[nearest]


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
            # TODO: use the flatness calibration somewhere.
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
                lut_data = numpy.loadtxt(os.path.join(path, f), 
                                         usecols=(1,),
                                         dtype=numpy.ushort)
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


    def set_test_sequence(self):
        """ Generate a series of test images. """
        from PIL import Image, ImageDraw, ImageFont
        sequence = []
        labels = range(15)
        lut = self.get_lut(550)
        imsize = self.pixels
        font = ImageFont.truetype('arial.ttf', imsize[0]/2)
        for c in labels:
            image = Image.new('L', imsize)
            draw = ImageDraw.Draw(image)
            draw.setink(255)
            draw.text((128,0), str(c), font=font)
            pattern16 = numpy.array(image.getdata(), 
                                    dtype=numpy.ushort).reshape(imsize)
            pattern16 *= (65535 * 123.9 / 360) / pattern16.max()
            pattern = lut[pattern16 / 4]
            # Append to the sequence.
            sequence.append(pattern)
        self.sequence_parameters = map(lambda x: (x, 0, 0), labels)
        self.sequence = sequence
        self.load_sequence()

    def get_shape(self):
        """ Return the device shape in pixels. """
        return self.pixels


    def set_custom_sequence(self, wavelengths, patterns):
        """ Generate sequence from given wavelengths and patterns.

        Accepts:
          single wavelength, N patterns;
          N wavelengths, N patterns

        Patterns should be arrays of 16-bit unsigned integers; they will be
        reshaped to the device size, which can be queried with get_shape().
        """
        if type(wavelengths) in [list, tuple]:
            assert len(wavelengths) == len(patterns), \
                "len(wavelengths) != len(patterns)."
        else:
            wavelengths = len(patterns) * [wavelengths]
        # Determine LUT once for each wavelength.
        luts = {w: self.get_lut(w) for w in set(wavelengths)}
        # Generate the sequence.
        self.sequence = []
        for (w, p) in zip(wavelengths, patterns):
            # Cast and reshape provided pattern.
            pattern16 = numpy.array(p, dtype=numpy.ushort).reshape(self.pixels)
            # Lose two LSBs and pass through the LUT for given wavelength.
            pattern = luts[w][pattern16 / 4]
            # Append to the sequence.
            self.sequence.append(pattern)
        # Load sequence to the hardware.
        self.load_sequence()


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


    def get_is_enabled(self):
        return self.hardware.power


    def get_power(self):
        return self.hardware.power


    def get_sequence_index(self):
        index = self.hardware.curr_seq_image
        # Index is actually that of the image that will be displayed
        # on the next trigger.
        return index - 1 if index > 0 else len(self.sequence) - 1


    def get_sim_diffraction_angle(self):
        return self.sim_diffraction_angle


    def set_sim_diffraction_angle(self, angle):
        self.sim_diffraction_angle = float(angle)


    def single_frame(self, index):
        self.hardware.stop_sequence()
        self.hardware.write_image(self.sequence[index])


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
