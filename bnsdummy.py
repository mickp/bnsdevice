import ctypes
from ctypes import c_int, c_bool, c_double, c_short, c_char, c_char_p, c_uint, c_ushort, windll

CLASS_NAME = "BNSDevice"

class BNSDevice(object):
    # Implements same interface as the real BNS device, but doesn't try
    # to do anything with the hardware.
    def __init__(self):
        self.libPath = "PCIe16Interface"
        self.lib = ctypes.WinDLL(self.libPath)
        self.haveSLM = False

    # === DECORATORS === #
    def requires_slm(func):
        def wrapper(self, *args, **kwargs):
            if self.haveSLM == False:
                raise Exception("SLM is not initialized.")
            else:
                return func(self, *args, **kwargs)
        return wrapper

    # === PROPERTIES === #
    @property
    @requires_slm
    def curr_seq_image(self): # tested - works
        return 0

    @property
    @requires_slm
    def power(self): #tested - works
        return 0
    @power.setter
    @requires_slm
    def power(self, value): #tested - works
        pass

    @property
    @requires_slm
    def temperature(self): #tested - works
        return 0

    # === METHODS === #
    @requires_slm
    def cleanup(self): #tested
        self.haveSLM = False
    

    def flatten_image(self, image):
        return image

    def initialize(self): #tested
        self.haveSLM = True


    @requires_slm
    def load_lut(self, filename): #tested - no errors
        pass;

    @requires_slm
    def load_sequence(self, imageList): #tested - no errors
        # imageList is a list of images, each of which is a list of integers.
        if len(imageList) < 2:
            raise Exception("load_sequence expects a list of two or more images - it was passed %s images." %len(imageList))
        images = (c_short * sum(len(image) for image in imageList))(*sum(imageList, []))


    def read_tiff(self, filePath, width, height):
        # void ReadTIFF (const char* FilePath, unsigned short* ImageData, unsigned int ScaleWidth, unsigned int ScaleHeight) 
        buffer = (c_ushort * width * height)()
        self.lib.ReadTIFF(c_char_p(filePath), buffer, c_uint(width), c_uint(height))
        return buffer


    @requires_slm
    def set_sequencing_framrate(self, frameRate): # tested - no errors
        pass

    @requires_slm
    def set_true_frames(self, trueFrames): #tested - no errors
        pass

    @requires_slm
    def start_sequence(self): # tested - works
        pass

    @requires_slm
    def stop_sequence(self): # tested - works
        pass

    @requires_slm
    def write_cal(self, type, calImage): #tested - no errors
        image = (c_ushort * len(calImage))(*calImage)


    @requires_slm
    def write_image(self, image): #tested - works
        pass