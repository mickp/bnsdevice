import numpy
from numpy import arange, array, meshgrid, cos, sin, deg2rad, pi
import matplotlib.pyplot as plt

class SIMPattern3D():
	def __init__(self):
		self.angles = array([0,60,120])
		self.phases = [0, 72, 144, 216, 288]
		self.pixelPitch = 15e-6
		self.pixels = 512
		self.wavelength = 532
		self.theta = 1
		self.phaseThenAngle = True
		
		self.patterns = []
		for i in range(0, len(self.angles) * len(self.phases)):
			self.patterns.append(numpy.zeros((self.pixels, self.pixels)))
			
			
	def updatePatterns(self, angleOffset=None, wavelength=None, theta=None, phaseThenAngle=None):
		
		# The pattern-generating function --- defined here so it may 
		# be used in either phase- or angle-first loops, later.
		def patternfunc():
			return numpy.round( mp2 * 2 / (2 * pi) * (127.5 + 127.5 * cos ((2 * pi * ( cos(deg2rad(angle)) * k + sin(deg2rad(angle)) * l)) / pp + deg2rad(phase))))
		
		# Pattern ordering, angles and phases.
		phaseThenAngle = phaseThenAngle or self.phaseThenAngle
		phases = self.phases
		if angleOffset is not None:
			angles = self.angles + angleOffset
		else:
			angles = self.angles
		
		# Optical parameters - desired diffraction angle and incident wavelength.
		theta = theta or self.theta
		wavelength = wavelength or self.wavelength
		
		
		# Pixels per period, from diffraction equation grating_pitch * sin(theta) = order * wavelength
		# Make sure wavelength is in nm.
		if wavelength > 100:
			wavelength *= 1e-9		
		pp = wavelength / (self.pixelPitch * sin(deg2rad(theta)))
		
		# Scaling factor to balance m=0,+/-1 orders
		mp2 = 1.5
		
		# Iterator over self.patterns
		i = 0
		
		indices = arange(self.pixels)
		k,l = meshgrid(indices,indices)
		
		if phaseThenAngle:
			for angle in angles:
				for phase in phases:
					self.patterns[i] = patternfunc()
					i += 1		
		else:
			for phase in phases:
				for angle in angles:
					self.patterns[i] = patternfunc()
					i += 1		
			
	
	