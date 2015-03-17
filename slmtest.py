""" Tests the slmservice.SpatialLightModulator class."""
import slmservice
import random
import math
import unittest

rng = random.Random()

def get_random_stripe_parms():
    return (rng.uniform(slm.pixel_pitch, 10. * slm.pixel_pitch), # pitch
            rng.uniform(0., 2 * math.pi), # angle
            rng.uniform(0., 2 * math.pi), # phase
            rng.uniform(0., 1.), # waves
            rng.uniform(400, 650) # wavelength
            )

slm = slmservice.SpatialLightModulator()
stripe_parms_a = get_random_stripe_parms()
stripe_parms_b = get_random_stripe_parms()

assert slm.generate_stripe_sequence([stripe_parms_a]) == 1
assert slm.generate_stripe_sequence([stripe_parms_a, stripe_parms_b]) == 2
slm.load_sequence()

orders = ['pa', 'paw', 'junkpaw', (0,0,0)]
for order in orders:
    try:
        print '\nCalling slm.generate_sim_sequence(\'%s\', 500) ...' % (tuple(order),)
        slm.generate_sim_sequence(tuple(order), 500)
    except Exception as e:
        print '... exception: %s' % e
    else:
        print '... succeeded.'

    try:
        print '\nCalling slm.generate_sim_sequence(\'%s\', [450, 500]) ...' % (tuple(order),)
        slm.generate_sim_sequence(tuple(order), [450, 500])
    except Exception as e:
        print '... exception: %s' % e
    else:
        print '... succeeded.'