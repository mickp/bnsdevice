import ctypes
from ctypes import c_int, c_bool, c_double, c_short, c_char, windll

CLASS_NAME = "BNSDevice"

class BNSDevice(object):
	# === BNS Interface.dll functions ===
	# + indicates equivalent python implementation here
	# o indicates calls from non-equivalent python code here
	#
	# ==== Documented ====
	# + int Constructor (int LCType={0:FLC;1:Nematic})
	# + void Deconstructor ()
	#   void ReadTIFF (const char* FilePath, unsigned short* ImageData, unsigned int ScaleWidth, unsigned int ScaleHeight) 
	# + void WriteImage (int Board, unsigned short* Image)
	# + void LoadLUTFile (int Board, char* LUTFileName)
	# o void LoadSequence (int Board, unsigned short* Image, int NumberOfImages)
	# + void SetSequencingRate (double FrameRate)
	# + void StartSequence ()
	# + void StopSequence ()
	# + bool GetSLMPower (int Board)
	# + void SLMPower (int Board, bool PowerOn)
	# + void WriteCal (int Board, CAL_TYPE Caltype={WFC;NUC}, unsigned char* Image )
	#   int ComputeTF (float FrameRate)
	# + void SetTrueFrames (int Board, int TrueFrames)
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


	# decorator definition for methods that require an SLM		
	def requires_slm(func):
		def wrapper(self, *args, **kwargs):
			if self.haveSLM == False:
				raise Exception("SLM is not initialized.")
			else:
				return func(self, *args, **kwargs)
		return wrapper


	def initialize(self):
		try:
			# If library has been opened, need to force unloading it.#
			# Otherwise, the DLL can open an error window about having already
			# initialized another DLL, which we won't see on a remote machine.
			if self.lib:
				while(windll.kernel32.FreeLibrary(self.lib._handle)):
					# Keep calling FreeLibrary until we really close the library.
					pass
			
			# (re)open the DLL
			self.lib = ctypes.WinDLL(self.libPath)
			
			# Initlialize the library, looking for nematic SLMs.
			n = self.lib.Constructor(c_int(1)) 
			if n == 0:
				raise Exception("No SLM device found.")
			elif n > 1:
				raise Exception("More than one SLM device found. This module can only handle one device.")
		except Exception as e:
			raise
		else:
			self.haveSLM = True

	
	# Don't call this unless an SLM was initialised:  if you do, the next call can
	# open that damned dialog box from some other library down the chain.
	@requires_slm
	def cleanup(self):
		try:
			self.lib.Deconstructor()
		except:
			pass
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
		# images = (c_short * sum(len(image) for image in imageList))(*sum(imageList, []))
		images = (c_short * sum(len(image) for image in imageList))(*imageList)

		# Now pass this by reference to the DLL function.
		# LoadSequence (int Board, unsigned short* Image, int NumberOfImages)
		self.lib.LoadSequence( c_int(0), ctypes.byref(images), c_int(len(imageList)))


	@requires_slm
	def write_cal(self, type, calImage):
		# void WriteCal (int Board, CAL_TYPE Caltype={WFC;NUC}, unsigned char* Image )
		
		# Not sure what type to pass the  CAL_TYPE as ... this is an ENUM, so could be
		# compiler / platform dependent.
		# 0 = WFC = wavefront correction
		# 1 = NUC = non-uniformity correction.

		# Image is a 1D array containing values from the 2D image.
		image = (c_char * len(image))(*calImage)

		self.lib.WriteCal(c_int(0), c_int(type), ctypes.byref(image))

	
	@requires_slm
	def load_lut(self, filename):
		self.lib.LoadLUTFile(c_int(board), ctypes.byref(c_char * len(filename))(*filename))


	@requires_slm
	def set_true_frames(self, trueFrames):
		self.lib.SetTrueFrames(c_int(0), c_int(trueFrames))


	def flatten_image(self, image):
		if len(image) != image.size:
			flatImage = [inner
			                 for outer in image
			                     for inner in outer
			            ]
			return flatImage
		else:
			return image