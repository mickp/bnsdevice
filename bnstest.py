arrayA = range(256)
arrayB = range(256)
list.reverse(arrayB)
LINE0 = sum(map(list, zip(arrayA,arrayB)),[])
hi = 65535
lo = 0

INTERLACED = []

LUTPATH = "C:/BLINK_PCIe/LUT_Files/"
LUT635 = LUTPATH + "slm2635_635.lut"
LUTLINEAR = LUTPATH + "Linear.LUT"

for n in range(512):
	INTERLACED.extend(LINE0)
BLACK = []
WHITE = []
for n in range(512 * 512):
	BLACK.extend([lo])
	WHITE.extend([hi])

VSTRIPES=[]
for n in range(512):
	VSTRIPES.extend((512/8) * [lo,lo,hi,hi,lo,lo,hi,hi])
	
HSTRIPES=[]
for n in range(512/4):
	HSTRIPES.extend(2*512*[lo] + 2*512*[hi])
	
DSTRIPES = []
for n in range((512/6)-1):
	DSTRIPES.extend(3*[lo]+3*[hi])
DSTRIPES.extend((512*512 - len(DSTRIPES)) * [lo])

	
SEQ = [BLACK,WHITE,HSTRIPES,DSTRIPES,VSTRIPES]
