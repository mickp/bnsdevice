""" Low-level wrapper around Interface.DLL from BNS.

Copyright 2014-2015 Mick Phillips (mick.phillips at gmail dot com)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import ctypes
import os, sys
import numpy as np
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
    
    ==== Newly documented ====
    + double GetInternalTemp (int Board, TEMPUNITS units);
    + void GetTIFFInfo (const char* FilePath, unsigned int* Width,
                        unsigned int* Height, unsigned short* BPP);
    + int GetCurSeqImage (int Board);
    + int GetImageSize (int Board);  """

    def __init__(self, board=1):
        # Must chdir to module path or DLL can not find its dependencies.
        try:
            modpath = os.path.dirname(__file__)
            os.chdir(modpath)
        except:
            # Probably running from interactive shell
            modpath = ''
        # path to dll
        self.libPath = os.path.join(modpath, "Interface")
                                             #"PCIe16Interface")
        print(self.libPath)
        # loaded library instance
        # Now loaded here so that read_tiff is accessible even if there is no 
        # SLM present.
        self.lib = ctypes.WinDLL(self.libPath)
        print("*******************\n", self.lib, self.lib.Constructor)
        # Boolean showing initialization status.
        self.haveSLM = False
        # Data type to store images.
        self.imagetype = None
        # Board identifier. 1-based in 2019-07 DLL builds (previously 0-based).
        self._board = c_int(board)


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
    def curr_seq_image(self):
        #return self.lib.GetCurSeqImage(self._board)
        # GetCurrSeqImage no longer exists.
        # GetRunStatus is supposed to do the same thing, but it appears
        # to always return zero, or our trigger isn't working.
        return self.lib.GetRunStatus(self._board)


    @requires_slm
    def get_power(self):
        # Subtracting 1 for now. Other functions in interface.dll now seem
        # to index devices from 1 (as per old docs) rather than 0(which is what
        # the old DLL did, contrary to the docs). With one device attached,
        # calling GetSLMPower(1) throws a C++ exception, but calling with 0
        # appears to return the power state as set by SLMPower, so I can only
        # assume that this one function does not use the new numbering scheme.
        return self.lib.GetSLMPower(self._board.value - 1)

    @requires_slm
    def set_power(self, value):
        # SLMPower used to take arguments (board index, power state).
        # It now appears that the first argument is the power state, not
        # the board index. We need documentation for this change.
        #self.lib.SLMPower(self._board, c_bool(value))
        self.lib.SLMPower(c_bool(value))


    @property
    @requires_slm
    def temperature(self):
        return self.lib.GetInternalTemp(self._board, c_int(0))


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
            # Ensure arg. to FreeLibary is wrapped as HMODULE, not Int32.
            from ctypes import wintypes
            ctypes.windll.kernel32.FreeLibrary.argtypes = [wintypes.HMODULE]
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
            self.size = self.lib.GetImageSize(self._board)
            self.imagetype = bnsdatatype * (self.size * self.size)
        # SLM shows nothing without calibration, so set flat WFC.
        white = self.imagetype(*[65535] * self.size * self.size)
        self.write_cal(1, white)



    @requires_slm
    def load_lut(self, filename): #tested - no errors
        ## Warning: opens a dialog if it can't read the LUT file.
        # Should probably check if the LUT file exists and validate it
        # before calling LoadLUTFile.
        self.lib.LoadLUTFile(self._board, c_char_p(filename))


    @requires_slm
    def load_sequence(self, imageList): #tested - no errors
        # imageList is a list of images, each of which is a list of integers.
        if len(imageList) < 2:
            raise Exception("load_sequence expects a list of two or more "\
                            "images - it was passed %s images." 
                            % len(imageList))

        if all([type(image) is self.imagetype for image in imageList]):
            # Data is fine as it is.
            pass            
        else:
            # Some images need converting.
            flatImages = []
            for image in imageList:
                if type(image) is np.ndarray:
                    flatImages.append(self.imagetype(*image.flatten()))
                else:
                    flatImages.append(self.imagetype(*image))
            imageList = flatImages

        # Make a contiguous array.
        sequence = (self.imagetype * len(imageList))(*imageList)
        # LoadSequence (int Board, unsigned short* Image, int NumberOfImages)
        self.lib.LoadSequence(self._board, ctypes.byref(sequence),
                              c_int(len(imageList)))


    def read_tiff(self, filePath):
        ## void ReadTIFF (const char* FilePath, unsigned short* ImageData,
        #                unsigned int ScaleWidth, unsigned int ScaleHeight) 
        buffer = self.imagetype()
        self.lib.ReadTIFF(c_char_p(filePath), buffer, 
                          self.size, self.size)
        return buffer


    @requires_slm
    def set_sequencing_framrate(self, frameRate): # tested - no errors
        ## Note - probably requires internal-triggering DLL,
        # rather than that set up for external triggering.
        self.lib.SetSequencingRate( c_double(frameRate) )


    @requires_slm
    def set_true_frames(self, trueFrames): #tested - no errors
        self.lib.SetTrueFrames(self._board, c_int(trueFrames))


    @requires_slm
    def start_sequence(self):
        self.lib.StartSequence()


    @requires_slm
    def stop_sequence(self): 
        self.lib.StopSequence()


    @requires_slm
    def write_cal(self, caltype, calImage): #tested - no errors
        ## void WriteCal(int Board, CAL_TYPE Caltype={WFC;NUC},
        #               unsigned char* Image)
        
        ## Not sure what type to pass the  CAL_TYPE as ... this is an ENUM, so
        # could be compiler / platform dependent.
        # 1 = WFC = wavefront correction
        # 0 = NUC = non-uniformity correction.

        # 2019-09 - It seems that WriteCal no longer takes a 'type' argument.
        # We need documentation for this change.

        ## Image is a 1D array containing values from the 2D image.
        # image = (c_char * len(calImage))(*calImage)
        # Doesn't seem to like c_char, which doesn't make sense anyway, as
        # the calibration files are 16-bit.
        # Header file states it's an unsigned short.
        
        image = self.imagetype(*calImage)
        # Removing caltype argument for now.
        # TODO: ask for documentation for change and fix accordingly.
        self.lib.WriteCal(self._board, ctypes.byref(image))


    @requires_slm
    def write_image(self, image):
    ## void WriteImage (int Board, unsigned short* Image)
        if type(image) is self.imagetype:
            self.lib.WriteImage(self._board,
                                ctypes.byref(self.imagetype(*image)))
        elif type(image) is np.ndarray:
            self.lib.WriteImage(0, self.imagetype(*image.flatten()))
        else:
            raise Exception('Unable to convert image.')
