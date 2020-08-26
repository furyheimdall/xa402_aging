# Parse logs from aging log

import os
import sys
import numpy as np
import matplotlib
if __name__ == "__main__":
	if os.environ.get('DISPLAY','') == '':
		print('no display found. Using non-interactive Agg backend')
		matplotlib.use('Agg')
else:
	matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import (MultipleLocator, FormatStrFormatter,AutoMinorLocator)

def setup_plot(plt, axs, titleName, xLabelName, yLabelName, lineColor, data):
	axs.clear()
	axs.set_title(titleName)
	axs.set_xlabel(xLabelName)
	axs.set_ylabel(yLabelName)
	axs.grid(True)
	#print(data)
	if len(np.array(data)) == 0:
		nLocator = 5
	else:
		nLocator = max(np.array(data)) - min(np.array(data))
	if nLocator > 15 :
		nLocator = 15
	if nLocator == 0 :
		nLocator = 3
	if nLocator < 0 :
		return
	axs.yaxis.set_major_locator(plt.MaxNLocator(nLocator))
	line = axs.plot(data)
	plt.setp(line, linewidth=0.5, color=lineColor)
	
def draw_plot():
	
	define_chart = dict()
	# [data, title_name, x-axis name, y-axis name, line color]
	define_chart[0] = [javaHeap, 'Memory consumption (JAVA)', 'Time', 'Heap(KB)', 'r']
	define_chart[1] = [nativeHeap, 'Memory consumption (Native)', 'Time', 'Heap(KB)', 'b']
	define_chart[2] = [binderSystem, 'Binder consumption (System)', 'Time', 'The number of Binder', 'g']
	define_chart[3] = [binderTotal, 'Binder consumption (Total)', 'Time', 'The number of Binder', 'y']
	define_chart[4] = [logdHeap, 'LogD NativeHeap consumption', 'Time', 'Heap(KB)', 'gray']
	define_chart[5] = [bmemHeap, 'BMEM consumption % (PEAK)', 'Time', 'Ratio(%)', 'gray']
	define_chart[6] = [logServiceCpu, 'LogService CPU usage', 'Time', 'Usage', 'gray']
		
	fig, axs = plt.subplots(len(define_chart), 1)
	fig.set_figwidth(10)
	fig.set_figheight(len(define_chart)*3)

	for k in define_chart.keys():
		setup_plot(plt, axs[k], define_chart[k][1], define_chart[k][2], define_chart[k][3], define_chart[k][4], define_chart[k][0])
	fig.tight_layout()
	plt.savefig('graph.png', dpi=150)
	if __name__ == "__main__":
		plt.show()
		
def lineParse(line):
	splitLine = line.split(':')
	try:
		if len(splitLine) > 1:
			if splitLine[0] == 'Java Heap':
				javaHeap.append(int(splitLine[1]))
			if splitLine[0] == 'Native Heap':
				nativeHeap.append(int(splitLine[1]))
			if splitLine[0] == 'Binder total ':
				binderTotal.append(int(splitLine[1]))
			if splitLine[0] == 'Binder related to system server ':
				binderSystem.append(int(splitLine[1]))
			if splitLine[0] == 'Logd NatvHeap':
				logdHeap.append(int(splitLine[1]))
			if splitLine[0] == 'Bmem Peak':
				bmemHeap.append(int(splitLine[1]))
			if splitLine[0] == 'LogService CPU':
				logServiceCpu.append(float(splitLine[1]))
	except ValueError:
		pass
		#ignore
			
def readFile(inputFile):
	javaHeap.clear()
	nativeHeap.clear()
	binderTotal.clear()
	binderSystem.clear()
	logdHeap.clear()
	bmemHeap.clear()
	logServiceCpu.clear()
	with open(inputFile,encoding='UTF-8') as f:
		fileContent = f.readlines()
		fileContent = [x.strip() for x in fileContent]
		
		for line in fileContent:
			lineParse(line)

def generate_plot(inputFile):
	readFile(inputFile)
	draw_plot()

def cleanup_plot():
	plt.clf()
	plt.cla()
	plt.close()
							
nativeHeap=[]
javaHeap=[]
binderTotal=[]
binderSystem=[]
logdHeap=[]
bmemHeap=[]
logServiceCpu=[]


'''
generate_plot("memlog.txt")
'''
if __name__ == "__main__":
	generate_plot(sys.argv[1])
