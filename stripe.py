import numpy as np
import os
from numpy import rint, cos, sin, pi, meshgrid, arange

from operator import itemgetter

## Read in the LUTS
LUT_FILES = {405: 'slm7070_at405_P16.lut',
             532: 'slm7070_at532_P16.lut',
             635: 'slm7070_at635_P16.lut'}
LUTS = {}
for wl, f in LUT_FILES.iteritems():
    fh = open(os.path.join('LUT_files',f), 'r')
    thisLUT = np.array([int(line.split()[1]) for line in fh])
    LUTS.update({wl: thisLUT})

def whichLUT(wl):
    lutwls = LUTS.keys()
    differences = [abs(wl - lutwl) for lutwl in lutwls]
    return lutwls[min(enumerate(differences), key=itemgetter(1))[0]]


def generate_stripe_series(patternparms):
    """ Generate a stripe series from the patternparms.

    patternparms is a list of tuples:  (pitch, angle, phase, wavelength),
    where pitch is in microns, and both the angle and phase are specified
    in radians.  
    """
    xindices = np.arange(512)
    yindices = np.arange(512)
    kk, ll = meshgrid(xindices, yindices)
    sequence = []
    for realpitch, angle, phase, waves, wavelength in patternparms:
        pitch = realpitch / 15.0
        modulation = waves * (2**16)
        lut = LUTS[whichLUT(wavelength)]
        pattern16 = np.ushort(
                rint(32768. + (modulation / 2) * cos(
                    phase + 2 * pi * (kk * cos(angle) + ll * sin(angle)) / pitch)
                    ))
        pattern = lut[pattern16/4]
        sequence.append(pattern)
    return sequence


def generate_old_series(patternparms):
    """ Generate a stripe series from the patternparms.

    patternparms is a list of tuples:  (pitch, angle, phase, wavelength),
    where pitch is in microns, and both the angle and phase are specified
    in radians.  
    """
    xindices = np.arange(512)
    yindices = np.arange(512)
    kk, ll = meshgrid(xindices, yindices)
    sequence = []
    mp2 = 1.5 
    for realpitch, angle, phase, waves, wavelength in patternparms:
        pitch = realpitch / 15.0
        pattern = np.ushort(
                rint((mp2 / pi) * (32767.5 + 32767.5 * (mp2 / pi) * cos(
                    phase + 2. * pi * (kk * cos(angle) + ll * sin(angle)) / pitch)
                    ))
                )
        # Scale to green LUT range
        pattern *= (16256. / 65536.)
        pattern += 49279
        sequence.append(pattern)
    return sequence