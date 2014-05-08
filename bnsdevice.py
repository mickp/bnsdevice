#import depot
#import device
# handlers?

import ctypes

CLASS_NAME = "BNSDevice"

class BNSDevice(object):
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
		
			
	
		