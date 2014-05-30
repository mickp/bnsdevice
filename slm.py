from bnsdummy import BNSDevice
from itertools import chain, product

def loop_in_order(arr1, arr2, arr3, order=[0,1,2]):
	parameters = [arr1, arr2, arr3]

	p0 = parameters[order[0]]
	p1 = parameters[order[1]]
	p2 = parameters[order[2]]

	qlist = product(p0, p1, p2)

	for q in qlist:
		yield (q[order[0]], q[order[1]], q[order[2]])



class StripeSeries(list):
	def __init__(self, pitches=[], phases=[], thetas=[], order=[0,1,2]):
		self.parameters = list(loop_in_order(pitches, phases, thetas, order))


class StripePattern(object):
	def __init__(self, pitch=None, angle=None, phase=None):
		self.pitch = pitch or 1.
		self.angle = angle or 0.
		self.phase = phase or 0.


class SLM(object):
	def __init__(self):
		self.slm = BNSDevice()
		self.pixelPitch = 15e-6
		self.slm.initialize()


	def generate_stripes(self, parameters):
		# pitch, angle, phase
		pass


	def load_images(self):
		pass

	def run(self):
		pass

	def stop(self):
		pass

