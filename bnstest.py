arrayA = range(256)
arrayB = range(256)
list.reverse(arrayB)
LINE0 = sum(map(list, zip(arrayA,arrayB)),[])

A = []
for n in range(512):
	A.extend(LINE0)
B = []
C = []
for n in range(512 * 512):
	B.extend([0])
	C.extend([255])

SERIES = [A,B,C]
WHITE = C
BLACK = B