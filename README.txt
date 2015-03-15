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


===Notes on SLM operation===
write_image takes a 16-bit greyscale image, drops tw LSBs (or divides by 4) 
to give 14-bit data, which is then read in through the LUT.

Phase calibration files are applied to the primary image either additively (WFC - 
wavefront correction) or multiplicatively (NUC - non-uniformity correction), with
resulting values wrapped on the interval 0 to 65535.

===Class prototype===

class BNSDevice(object):
	def __init__(self):

	# === DECORATORS === #
	def requires_slm(func):

	# === PROPERTIES === #
	def curr_seq_image(self): # tested - works
	def power(self): #tested - works
	def power(self, value): #tested - works
        def temperature(self): #tested - works

	# === METHODS === #
	def cleanup(self): #tested
	def flatten_image(self, image):
	def initialize(self): #tested
	def load_lut(self, filename): #tested - no errors
	def load_sequence(self, imageList): #tested - no errors
	def read_tiff(self, filePath, width, height):
	def set_sequencing_framrate(self, frameRate): # tested - no errors
	def set_true_frames(self, trueFrames): #tested - no errors
	def start_sequence(self): # tested - works
	def stop_sequence(self): # tested - works
	def write_cal(self, type, calImage): #tested - no errors
	def write_image(self, image): #tested - works
