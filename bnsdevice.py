""" Low-level wrapper around Interface.DLL from BNS.

Copyright Mick Phillips, 2014 <mick.phillips at gmail.com>.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import ctypes
import os, sys
from ctypes import c_int, c_bool, c_double, c_short
from ctypes import c_char, c_char_p, c_uint, c_ushort, windll

CLASS_NAME = "BNSDevice"

bnsdatatype = ctypes.c_uint16

class BNSDevice(object):
    """ Enables calls to functions in BNS's Interface.dll.

    === BNS Interface.dll functions ===
    + indicates equivalent python implementation here
    o indicates calls from non-equivalent python code here
    
    ==== Documented ====
    + int Constructor (int LCType={0:FLC;1:Nematic})
    + void Deconstructor ()
    + void ReadTIFF (const char* FilePath, unsigned short* ImageData,
                     unsigned int ScaleWidth, unsigned int ScaleHeight) 
    + void WriteImage (int Board, unsigned short* Image)
    + void LoadLUTFile (int Board, char* LUTFileName)
    o void LoadSequence (int Board, unsigned short* Image, int NumberOfImages)
    + void SetSequencingRate (double FrameRate)
    + void StartSequence ()
    + void StopSequence ()
    + bool GetSLMPower (int Board)
    + void SLMPower (int Board, bool PowerOn)
    + void WriteCal (int Board, CAL_TYPE Caltype={WFC;NUC},
                     unsigned char* Image)
      int ComputeTF (float FrameRate)
    + void SetTrueFrames (int Board, int TrueFrames)
    
    ==== Undocumented ====
    + GetInternalTemp
      GetTIFFInfo
    + GetCurSeqImage
      GetImageSize
    
    ==== Notes ====
    The BNS documentation states that int Board is a 1-based index, but it
    would appear to be 0-based:  if I address board 1 with Board=1, I get an msc
    error; using Board=0 seems to work just fine.
    """

    def __init__(self):
        # Must chdir to module path or DLL can not find its dependencies.
        try:
            modpath = os.path.dirname(__file__)
            os.chdir(modpath)
        except:
            # Probably running from interactive shell
            modpath = ''
        # path to dll
        self.libPath = os.path.join(modpath, "PCIe16Interface")
        # loaded library instance
        # Now loaded here so that read_tiff is accessible even if there is no 
        # SLM present.
        self.lib = ctypes.WinDLL(self.libPath)
        # Boolean showing initialization status.
        self.haveSLM = False
        # Data type to store images.
        self.imagetype = None

    ## === DECORATORS === #
    # decorator definition for methods that require an SLM      
    def requires_slm(func):
        def wrapper(self, *args, **kwargs):
            if self.haveSLM == False:
                raise Exception("SLM is not initialized.")
            else:
                return func(self, *args, **kwargs)
        return wrapper

    ## === PROPERTIES === #
    @property
    @requires_slm
    def curr_seq_image(self): # tested - works
        return self.lib.GetCurSeqImage(c_int(0))


    @property
    @requires_slm
    def power(self): #tested - works
        return self.lib.GetSLMPower(c_int(0))
    @power.setter
    @requires_slm
    def power(self, value): #tested - works
        self.lib.SLMPower(c_int(0), c_bool(value))


    @property
    @requires_slm
    def temperature(self): #tested - works
        return self.lib.GetInternalTemp(c_int(0))


    ## === METHODS === #

    ## Don't call this unless an SLM was initialised:  if you do, the next call
    # can open a dialog box from some other library down the chain.
    @requires_slm
    def cleanup(self): #tested
        try:
            self.lib.Deconstructor()
        except:
            pass
        self.haveSLM = False


    def initialize(self): #tested
        ## Need to unload and reload the DLL here.
        # Otherwise, the DLL can open an error window about having already
        # initialized another DLL, which we won't see on a remote machine.
        if self.lib:
            while(windll.kernel32.FreeLibrary(self.lib._handle)):
                # Keep calling FreeLibrary until library is really closed.
                pass
        try:      
            # re-open the DLL
            self.lib = ctypes.WinDLL(self.libPath)
        except:
            raise
        
        # Initlialize the library, looking for nematic SLMs.
        n = self.lib.Constructor(c_int(1)) 
        if n == 0:
            raise Exception("No SLM device found.")
        elif n > 1:
            raise Exception("More than one SLM device found. This module "\
                            "can only handle one device.")
        else:
            self.haveSLM = True
            self.size = self.lib.GetImageSize(0)
            self.imagetype = bnsdatatype * (self.size * self.size)


    @requires_slm
    def load_lut(self, filename): #tested - no errors
        ## Warning: opens a dialog if it can't read the LUT file.
        # Should probably check if the LUT file exists and validate it
        # before calling LoadLUTFile.
        self.lib.LoadLUTFile(c_int(0), c_char_p(filename))


    @requires_slm
    def load_sequence(self, imageList): #tested - no errors
        # imageList is a list of images, each of which is a list of integers.
        if len(imageList) < 2:
            raise Exception("load_sequence expects a list of two or more "\
                            "images - it was passed %s images." 
                            % len(imageList))

        ## Need to make a 1D array of shorts containing the image data.

        ## Turn imageList into a single list, 
        # then make that into an array of c_shorts.
        # (c_short * length)(*array)
        images = (c_short * sum(
                  len(image) for image in imageList))(*sum(imageList, []))

        ## Now pass this by reference to the DLL function.
        # LoadSequence (int Board, unsigned short* Image, int NumberOfImages)
        self.lib.LoadSequence(c_int(0), ctypes.byref(images), 
                              c_int(len(imageList)))


    def read_tiff(self, filePath, width, height):
        ## void ReadTIFF (const char* FilePath, unsigned short* ImageData,
        #                unsigned int ScaleWidth, unsigned int ScaleHeight) 
        buffer = (c_ushort * width * height)()
        self.lib.ReadTIFF(c_char_p(filePath), buffer, 
                          c_uint(width), c_uint(height))
        return buffer


    @requires_slm
    def set_sequencing_framrate(self, frameRate): # tested - no errors
        ## Note - probably requires internal-triggering DLL,
        # rather than that set up for external triggering.
        self.lib.SetSequencingRate( c_double(frameRate) )


    @requires_slm
    def set_true_frames(self, trueFrames): #tested - no errors
        self.lib.SetTrueFrames(c_int(0), c_int(trueFrames))


    @requires_slm
    def start_sequence(self): # tested - works
        self.lib.StartSequence()


    @requires_slm
    def stop_sequence(self): # tested - works
        self.lib.StopSequence()


    @requires_slm
    def write_cal(self, type, calImage): #tested - no errors
        ## void WriteCal(int Board, CAL_TYPE Caltype={WFC;NUC},
        #               unsigned char* Image)
        
        ## Not sure what type to pass the  CAL_TYPE as ... this is an ENUM, so
        # could be compiler / platform dependent.
        # 1 = WFC = wavefront correction
        # 0 = NUC = non-uniformity correction.

        ## Image is a 1D array containing values from the 2D image.
        # image = (c_char * len(calImage))(*calImage)
        # Doesn't seem to like c_char, which doesn't make sense anyway, as
        # the calibration files are 16-bit.
        # Header file states it's an unsigned short.
        image = (c_ushort * len(calImage))(*calImage)
        self.lib.WriteCal(c_int(0), c_int(type), ctypes.byref(image))


    @requires_slm
    def write_image(self, image): #tested - works
    ## void WriteImage (int Board, unsigned short* Image)
        self.lib.WriteImage(c_int(0), 
                            ctypes.byref((c_short * len(image))(*image)))
