import ctypes
from ctypes import byref
from time import sleep

lib = ctypes.WinDLL("PCIe16Interface")
lib.Constructor(1)
imsize = lib.GetImageSize(0)

imtype = ctypes.c_uint16 * (imsize * imsize)
cal = imtype()
seq = (imtype * 3)()

lib.LoadLUTFile(0, 'linear.lut')

lib.ReadTIFF('white.tiff', byref(cal), imsize, imsize)
lib.WriteCal(0, 1, cal)

lib.ReadTIFF('16AStigx.tiff', byref(seq[0]), imsize, imsize)
lib.ReadTIFF('StripePer16.TIFF', byref(seq[1]), imsize, imsize)
lib.ReadTIFF('16Comax.tiff', byref(seq[1]), imsize, imsize)

lib.WriteImage(0, byref(seq))

lib.SLMPower(0, True)

sleep(5)

lib.LoadSequence(0, seq, 3)
lib.StartSequence()