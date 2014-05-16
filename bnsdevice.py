#import depot
#import device
# handlers?

import ctypes
from ctypes import c_int, c_bool, c_double, c_short

CLASS_NAME = "BNSDevice"

class BNSDevice(object):
	# === BNS Interface.dll functions ===
	# + indicates implemented here
	# ==== Documented ====
	# + int Constructor (int LCType={0:FLC;1:Nematic})
	# + void Deconstructor ()
	#   void ReadTIFF (const char* FilePath, unsigned short* ImageData, unsigned int ScaleWidth, unsigned int ScaleHeight) 
	#   void WriteImage (int Board, unsigned short* Image)
	#   void LoadLUTFile (int Board, char* LUTFileName)
	#   void LoadSequence (int Board, unsigned short* Image, int NumberOfImages)
	# + void SetSequencingRate (double FrameRate)
	# + void StartSequence ()
	# + void StopSequence ()
	# + bool GetSLMPower (int Board)
	# + vvoid SLMPower (int Board, bool PowerOn)
	#   void WriteCal (int Board, CAL_TYPE Caltype={WFC;NUC}, unsigned char* Image )
	#   int ComputeTF (float FrameRate)
	#   void SetTrueFrames (int Board, int TrueFrames)
	#
	# ==== Undocumented ====
	# + GetInternalTemp
	#   GetTIFFInfo
	#   GetCurSeqImage
	#   GetImageSize
	#
	#==== Notes ====
	# The BNS documentation states that int Board is a 1-based index, but it would appear to be 0-based:
	# if I address board 1 with Board=1, I get an msc error; using Board=0 seems to work just fine.
	

	def __init__(self):
		# path to dll
		self.libPath = "PCIe16Interface"
		
		# loaded library instance
		self.lib = None
		
		# Boolean showing initialization status.
		self.haveSLM = False
		
	def requires_slm(func):
		def wrapper(self, *args, **kwargs):
			if self.haveSLM == False:
				raise Exception("SLM is not initialized.")
			else:
				return func(self, *args, **kwargs)
		return wrapper


	def initialize(self):
		try:
			self.lib = ctypes.WinDLL(self.libPath)
			n = self.lib.Constructor(c_int(1)) # Initlialize the library, looking for nematic SLMs.
			if n == 0:
				raise Exception("No SLM device found.")
			elif n > 1:
				raise Exception("More than one SLM device found. This module can only handle one device.")
		except Exception as e:
			message = e.message or "There was a problem with the SLM: %s" % e
			caption = "SLM error"
			try:
				self.lib.Deconstructor() # Call the DLL deconstructor.
			except:
				pass
		else:
			self.haveSLM = True

	
	def cleanup(self):
		try:
			self.lib.Deconstructor()
		except:
			pass
		self.lib = None
		self.haveSLM = False

	@property
	@requires_slm
	def temperature(self):
	    return self.lib.GetInternalTemp(c_int(0))
	
	
	@property
	@requires_slm
	def power(self):
	    return self.lib.GetSLMPower(c_int(0))
	@power.setter
	@requires_slm
	def power(self, value):
	    self.lib.SLMPower(c_int(0), c_bool(value))

	@requires_slm
	def start_sequence(self):
		self.lib.StartSequence()

	@requires_slm
	def stop_sequence(self):
		self.lib.StopSequence()

	@requires_slm
	def set_sequencing_framrate(self, frameRate):
		# note - probably requires internal-triggering DLL,
		# rather than that set up for external triggering.
		self.lib.SetSequencingRate( c_double(frameRate) )

	@requires_slm
	def load_sequence(self, imageList):
		# imageList is a list of images, each of which is a list of integers.
		if len(imageList < 2):
			raise Exception("load_sequence expects a list of two or more images - it was passed %s images." %len(imageList))


		# Need to make a 1D array of shorts containing the image data.
		
		# Turn imageList into a single list, then make that into an array of c_shorts.
		# (c_short * length)(*array)
		images = (c_short * sum(len(image) for image in imageList))(*sum(imageList, []))

		# Now pass this by reference to the DLL function.
		# LoadSequence (int Board, unsigned short* Image, int NumberOfImages)
		self.lib.LoadSequence( c_int(0), ctypes.byref(c), c_int(len(imageList)))