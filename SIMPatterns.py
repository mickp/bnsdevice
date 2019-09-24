""" slm.py - python module to control spatial light modulator """

import numpy
from numpy import arange, array, meshgrid, cos, sin, deg2rad, pi
# import matplotlib.pyplot as plt

class SIMPattern3D():
    def __init__(self):
        self.angles = array([0, 60, 120])
        self.phases = [0, 72, 144, 216, 288]
        self.pixel_pitch = 15e-6
        self.pixels = 512
        self.wavelength = 532
        self.theta = 1
        self.phase_then_angle = True

        self.patterns = []
        for i in range(0, len(self.angles) * len(self.phases)):
            self.patterns.append(numpy.zeros((self.pixels, self.pixels)))


    def update_patterns(self, angle_offset=None, wavelength=None,
                        theta=None, phase_then_angle=None):

        ## The pattern-generating function --- defined here so it may
        # be used in either phase- or angle-first loops, later.
        def patternfunc(k, l, theta_rad, mp2):
            return numpy.round(
                mp2 * 2 / (2 * pi) *
                (
                    127.5 + 127.5 *
                    cos((2 * pi * (cos(theta_rad) * k + sin(theta_rad) * l)) /
                    pp + deg2rad(phase)
                )))

        ## Pattern ordering, angles and phases.
        phase_then_angle = phase_then_angle or self.phase_then_angle
        phases = self.phases
        if angle_offset     is not None:
            angles = self.angles + angle_offset
        else:
            angles = self.angles

        ## Optical parameters - desired diffraction angle and incident
        # wavelength.
        theta = theta or self.theta
        wavelength = wavelength or self.wavelength

        ## Pixels per period, from diffraction equation
        #   grating_pitch * sin(theta) = order * wavelength
        # Make sure wavelength is in nm.
        if wavelength > 100:
            wavelength *= 1e-9
        pp = wavelength / (self.pixel_pitch * sin(deg2rad(theta)))

        ## Scaling factor to balance m=0,+/-1 orders
        mp2 = 1000*3.14159

        ## Iterator over self.patterns
        i = 0

        indices = arange(self.pixels)
        k, l = meshgrid(indices, indices)

        if phase_then_angle:
            for angle in angles:
                for phase in phases:
                    self.patterns[i] = patternfunc(k, l, deg2rad(angle), mp2)
                    i += 1
        else:
            for phase in phases:
                for angle in angles:
                    self.patterns[i] = patternfunc(k, l, deg2rad(angle), mp2)
                    i += 1
        print(i)
       # print (self.patterns.shape())
        print (self.patterns[i-1].min())
        print (self.patterns[i-1].max())
