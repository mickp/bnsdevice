#import depot
#import device
# handlers?

import ctypes

CLASS_NAME = "BNSDevice"

class BNSDevice(object):
	# === BNS Interface.dll functions ===
	# ==== Documented ====
	# int Constructor (int LCType={0:FLC;1:Nematic})
	# void Deconstructor ()
	# void ReadTIFF (const char* FilePath, unsigned short* ImageData, unsigned int ScaleWidth, unsigned int ScaleHeight) 
	# void WriteImage (int Board, unsigned short* Image)
	# void LoadLUTFile (int Board, char* LUTFileName)
	# void LoadSequence (int Board, unsigned short* Image, int NumberOfImages)
	# void SetSequencingRate (double FrameRate)
	# void StartSequence ()
	# void StopSequence ()
	# bool GetSLMPower (int Board)
	# void SLMPower (int Board, bool PowerOn)
	# void WriteCal (int Board, CAL_TYPE Caltype={WFC;NUC}, unsigned char* Image )
	# int ComputeTF (float FrameRate)
	# void SetTrueFrames (int Board, int TrueFrames)
	#
	# ==== Undocumented ====
	# GetInternalTemp
	# GetTIFFInfo
	# GetCurSeqImage
	# GetImageSize
	


	def _init__(self):
		#device.Device.__init__(self)
		
		# path to dll
		self.libraryPath = "BNSPCIe16Board.dll"
		
		# loaded library instance
		self.library = None
		
		# Boolean showing initialization status.
		self.haveBNS = False
		
	def initialize(self):
		try:
			self.library = ctypes.cdll.LoadLibrary(self.libraryPath)
		except Exception e:
			message = "The SLM is not available: %s" % e
			caption = "SLM error"



			
	
		