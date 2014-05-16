arrayA = range(256)
arrayB = range(256)
list.reverse(arrayB)
LINE0 = sum(map(list, zip(arrayA,arrayB)),[])
INTERLACED = []

LUTPATH = "C:/BLINK_PCIe/LUT_Files/"
LUT635 = LUTPATH + "slm2635_635.lut"
LUTLINEAR = LUTPATH + "Linear.LUT"

for n in range(512):
	INTERLACED.extend(LINE0)
BLACK = []
WHITE = []
for n in range(512 * 512):
	BLACK.extend([0])
	WHITE.extend([16383])

STRIPES=[]
for n in range(512):
	hi = 16384
	STRIPES.extend((512/8) * [0,0,hi,hi,0,0,hi,hi])
	
SERIES = [INTERLACED,BLACK,STRIPES,WHITE]
