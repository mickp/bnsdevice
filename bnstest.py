import bnsdevice as bns
import numpy as np
import ctypes
from time import sleep
from numpy import rint, cos, sin, pi

dev = bns.BNSDevice()
dev.initialize()
dev.load_lut('linear.lut')

cal = dev.read_tiff('white.tiff')
dev.write_cal(1, cal)

images = []
images.append(dev.read_tiff('16Astigx.tiff'))
images.append(dev.read_tiff('StripePer16.tiff'))
images.append(dev.read_tiff('16Comax.tiff'))

dev.write_image(images[0])
dev.power = True

sleep(5)

dev.load_sequence(images)
dev.start_sequence()

sleep(5)

ind = np.arange(512)
kk, ll = np.meshgrid(ind, ind)
ndarray_images = []
ndarray_images.append(np.ushort(32767 + ((kk % 32) > 15) * 65535/2))
ndarray_images.append(np.ushort(32767 + (((kk + ll) % 48) > 23 )* 65535/2))
ndarray_images.append(np.ushort(32767 + ((ll % 32) > 15) * 65535/2))

dev.stop_sequence()

dev.write_image(ndarray_images[0])

sleep(5)

dev.load_sequence(ndarray_images)
dev.start_sequence()