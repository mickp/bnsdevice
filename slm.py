from bnsdummy import BNSDevice
from itertools import chain, product
import os, re, numpy
from PIL import Image

def loop_in_order(arrayList, order=None):
	"""Iterate over a list of lists in a specified order."""
	if order == None:
		order = range (len (arrayList))

	order.reverse()
	pList = product(*[arrayList[n] for n in order])

	reorder = [order.index(n) for n in range(len(order))]

	for p in pList:
		yield tuple(p[n] for n in reorder)


class StripeSeries(list):
	def __init__(self, pitches=[], phases=[], thetas=[], order=[2,0,1]):
		super(StripeSeries, self).__init__()
		self._pitches = pitches
		self._phases = phases
		self._thetas = thetas
		self.extend(list(loop_in_order ([pitches, phases, thetas], order)))

	def reorder(self, order=[2,0,1]):
		self[:] = list(loop_in_order ([self._pitches, self._phases, self._thetas], order))


class StripePattern(object):
	def __init__(self, pitch=1, angle=0, phase=0):
		pass


class SLM(object):
	def __init__(self):
		self.LUTs = {}
		self.calibs = {}

		self._LUTFolder = "LUT_files"
		self._calibrationFolder = "Phase_Calibration_Files"
		self.load_calibration_data()

		self.hardware = BNSDevice()
		self.pixelPitch = 15e-6
		self.pixels = (512, 512)
		self.hardware.initialize()


	def generate_stripe_series(self, pitches, phases, thetas, order):
		pass


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
		pass


	def run(self):
		self.hardware.power = True
		self.hardware.start_sequence()


	def stop(self):
		self.hardware.stop_sequence()
		self.hardware.power = False

