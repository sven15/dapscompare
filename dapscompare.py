#!/usr/bin/env python3

import multiprocessing
import threading
import os
import queue
import sys
from subprocess import check_output, Popen, PIPE
from scipy.misc import *
import numpy
from modules.qtcompare import qtImageCompare, toQImage
from modules.renderHTML import renderHTML
from modules.renderPDF import renderPDF
from modules.helpers import *
from modules.daps import daps
from PyQt4 import QtGui, QtCore
import json

class myGuiThread(QtCore.QThread):
	def __init__(self):
		QtCore.QThread.__init__(self)
		self.finished = False
	def __del__(self):
		self.wait()

	def run(self):	
		global app
		app = QtGui.QApplication(sys.argv)
		
	def renderHtml():
		qWebWorkers[self.counter].render("file://"+testcase+"build/"+build+"/html/"+build+"/"+filename,1280,testcase+modeToName(cfg.mode)+"/"+filetype)
		
class myWorkThread (QtCore.QThread):
	def __init__(self,threadID, name, counter):
		QtCore.QThread.__init__(self)
		self.threadID = threadID
		self.name = name
		self.counter = counter
		
	def __del__(self):
		self.wait()

	def run(self):
		outputTerminal("Starting "+self.name)
		global foldersLock, folders
		# we want the threads to keep running until the queue of test cases is empty
		while(True):
			testcase = ""
			foldersLock.acquire()
			if(folders.empty() == False):
				testcase = folders.get()
			foldersLock.release()
			# finish the thread if queue is empty
			if(testcase == ""):
				break
			outputTerminal(self.name+" now working on "+testcase)
			
			# compile DC files
			daps(testcase,cfg.dapsParam,cfg.filetypes)
			for build in os.listdir(testcase+"build"):
				if(os.path.isdir(testcase+"build") and not build.startswith(".")):
					# render results to images
					for filetype in cfg.filetypes:
						if filetype == 'pdf':
							for filename in os.listdir(testcase+"build/"+build):
								if(filename.endswith == ".pdf"):
									myRenderPdf = renderPDF(testcase+"build/"+build+"/"+filename,1280,testcase+modeToName(cfg.mode)+"/"+filetype)
						elif filetype == 'html':
							for filename in os.listdir(testcase+"build/"+build+"/html/"+build+"/"):
								if(filename.endswith(".html")):
									myRenderHtml = renderHTML("file://"+testcase+"build/"+build+"/html/"+build+"/"+filename,1280,testcase+modeToName(cfg.mode)+"/"+filetype)
									while myRenderHtml.isFinished() == False:
										pass
									print("file://"+testcase+"build/"+build+"/html/"+build+"/"+filename,1280,testcase+modeToName(cfg.mode)+"/"+filetype+" finished")
						elif filetype == 'epub':
							pass
					
			if(cfg.mode == 2):
				runTestsPDF(testcase)
		outputTerminal(self.name+" finished")
	
def runTestsPDF(testcase):
	for filetype in cfg.filetypes:
		referencePath = testcase+"dapscompare-reference/"+filetype+"/"
		comparisonPath = testcase+"dapscompare-comparison/"+filetype+"/"
		diffPath = testcase+"dapscompare-result/"+filetype+"/"
		for filename in os.listdir(referencePath):
			imgRef = imread(referencePath+filename)
			imgComp = imread(comparisonPath+filename)
			imgDiff = imgRef - imgComp
			global diffCollectionLock, diffCollection
			if numpy.count_nonzero(imgDiff) > 0:
				imsave(diffPath+"/"+filename,imgDiff)
				outputTerminal("Image "+cfg.directory+""+testcase+"dapscompare-comparison/pdf/"+filename+" has changed.")
				diffCollectionLock.acquire()
				diffCollection.collection.append([referencePath+filename, comparisonPath+filename, diffPath+filename])
				diffCollectionLock.release()

def outputTerminal(text):
	global outputLock
	outputLock.acquire()
	print (text)
	outputLock.release()      

class MyConfig:
	def __init__(self):
		# set standard values for all other needed parameters
		self.directory = os.getcwd()+"/"
		
		# 1 = build reference
		# 2 = build comparison and run tests (standard)
		# 3 = view results of last run
		# 4 = clean
		self.mode = 0
		
		# usually show GUI after comparison
		self.noGui = False
		
		self.filetypes = ['pdf','html']
		
		self.dapsParam = "--force"
		
		# first read CLI parameters
		for parameter in sys.argv:
			if parameter == "compare":
				self.mode = 2
			elif parameter == "reference":
				self.mode = 1
			elif parameter == "view":
				self.mode = 3
			elif parameter == "clean":
				self.mode = 4
			elif parameter == "--help":
				f = open('README', 'r')
				print(f.read())
				f.close()
				sys.exit()
			elif parameter == "--no-gui":
				self.noGui = True
			elif parameter.startswith("--daps="):
				self.dapsParam = parameter[7:]
			elif parameter.startswith("--testcases="):
				self.directory = parameter[12:]
			elif parameter == "--no-pdf":
				self.filetypes.remove('pdf')
			elif parameter == "--no-html":
				self.filetypes.remove('html')
			elif parameter == "--no-epub":
				self.filetypes.remove('epub')

class DiffCollector:
	def __init__(self):
		self.collection = []

def spawnGui():
	print("Starting Qt GUI")
	if cfg.mode == 2:
		ex = qtImageCompare(cfg.directory, diffCollection.collection)
	if cfg.mode == 3:
		ex = qtImageCompare(cfg.directory)
	sys.exit(app.exec_())

def spawnWorkerThreads():
	# get number of available cpus. 
	# we want to compile as many test cases with daps at the same time 
	# as we can
	cpus = multiprocessing.cpu_count()
	print("CPUs: "+str(cpus))
	global foldersLock, outputLock
	foldersLock = threading.Lock()
	threads = []
	qWebWorkers = []
	outputLock = threading.Lock()

	global folders
	folders = queue.Queue()
		
	for testcase in os.listdir(cfg.directory):
		if(os.path.isdir(cfg.directory+"/"+testcase)):
			print("Found test case: "+testcase)
			foldersLock.acquire()
			folders.put(cfg.directory+testcase+"/")
			foldersLock.release()

	for threadX in range(0,cpus):
		thread = myWorkThread(threadX, "Thread-"+str(threadX), threadX)
		thread.start()
		threads.append(thread)

	# Wait for all threads to complete
	for t in threads:
		t.wait()
	print("All threads finished.")
	
	if cfg.mode == 2:
		writeFile("./results.json",json.dumps(diffCollection.collection))

def cleanDirectories():
	my_env = os.environ.copy()
	somestring = "rm -r "+cfg.directory+"/*/build/* && rm -r "+cfg.directory+"/*/dapscompare-*/* && rm "+cfg.directory+"results.json"
	process = Popen([somestring], env=my_env, shell=True, stdout=PIPE, stderr=PIPE)


		
def main():
	qtcoreapp = QtCore.QCoreApplication.instance()
	global queueHtml, queueHtmlLock
	queueHtml = queue.Queue()
	queueHtmlLock = threading.Lock()
	
	#guiThread = myGuiThread()
	#guiThread.run()
	
	
	global cfg, diffCollection, diffCollectionLock
	cfg = MyConfig()
	diffCollection = DiffCollector()
	diffCollectionLock = threading.Lock()
	
	if cfg.mode == 1 or cfg.mode == 2:
		spawnWorkerThreads()
		#guiThread.finished = True
	
	if (cfg.mode == 2 and cfg.noGui == False) or cfg.mode == 3:
		spawnGui()
		
	if cfg.mode == 4:
		cleanDirectories()
		
	if cfg.mode == 0:
		print("Nothing to do. Use --help.")

if __name__ == "__main__":
    main()
