import bnsdevice as bns
from time import sleep

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
