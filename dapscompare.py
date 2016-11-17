#!/usr/bin/env python3

# The MIT License (MIT)
# 
# Copyright (c) 2016, Sven Seeberg-Elverfeldt <sseebergelverfeldt@suse.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import multiprocessing, threading, queue, os, sys, json, string, hashlib, shutil

from scipy.misc import imsave, imread
import numpy as np
from PyQt4 import QtGui, QtCore

from modules.qtcompare import qtImageCompare, toQImage
from modules.renderers import renderHtml, renderPdf
from modules.helpers import readFile, writeFile, modeToName
from modules.daps import daps


class myWorkThread (QtCore.QThread):
# worker threads which compile the DC files and compare the results
	def __init__(self,threadID, name, counter):
		QtCore.QThread.__init__(self)
		self.threadID = threadID
		self.name = name
		self.counter = counter
		
	def __del__(self):
		self.wait()

	def run(self):
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

			# render results to images
			runRenderers(testcase)
					
			if(cfg.mode == 2):
				runTests(testcase)
		outputTerminal(self.name+" finished")

# calls the rendering modules
def runRenderers(testcase):
	for filetype in cfg.filetypes:
		if filetype == 'pdf':
			folderName = testcase+modeToName(cfg.mode)+"/"+registerHash(filetype.upper())
			if not os.path.exists(folderName):
				os.makedirs(folderName)
			myRenderPdf = renderPdf(testcase+"build/*/*.pdf",100,folderName)
		elif filetype == 'html' and cfg.noGui == False:
			for build in os.listdir(testcase+"build"):
				if not build.startswith("."):
					for htmlBuild in os.listdir(testcase+"build/"+build+"/html/"):
						for htmlFile in os.listdir(testcase+"build/"+build+"/html/"+htmlBuild):
							for width in cfg.htmlWidth:
								folderName = testcase+modeToName(cfg.mode)+"/"+registerHash(filetype.upper()+" w:"+str(width)+"px")+"/"
								if not os.path.exists(folderName):
									os.makedirs(folderName)
								myRenderHtml = renderHtml(testcase+"build/"+build+"/html/"+htmlBuild+"/"+htmlFile,width,folderName)
		elif filetype == 'epub':
			pass

def registerHash(somestring):
	# create md5sum of hash
	md5 = hashlib.md5(somestring.encode('utf-8'))
	# add md5sum and string to config and save to file in the end
	dataCollectionLock.acquire()
	dataCollection.depHashes[md5.hexdigest()] = somestring
	dataCollectionLock.release()
	return md5.hexdigest()

# diff images of reference and compare run and save result
def runTests(testcase):
	for md5, descritpion in dataCollection.depHashes.items():
		referencePath = testcase+"dapscompare-reference/"+md5+"/"
		comparisonPath = testcase+"dapscompare-comparison/"+md5+"/"
		if not os.path.exists(referencePath):
			print("No reference images for "+dataCollection.depHashes[md5])
			continue
		diffFolder = testcase+"dapscompare-result/"+md5+"/"
		if not os.path.exists(diffFolder):
			os.makedirs(diffFolder)

		for filename in os.listdir(referencePath):
			imgRef = imread(referencePath+filename)
			imgComp = imread(comparisonPath+filename)
			imgDiff = imgRef - imgComp
			if np.count_nonzero(imgDiff) > 0:
				imsave(diffFolder+filename,imgDiff)
				outputTerminal("Image "+comparisonPath+filename+" has changed.")
				dataCollectionLock.acquire()
				dataCollection.imgDiffs.append([referencePath+filename, comparisonPath+filename, diffFolder+filename])
				dataCollectionLock.release()

def outputTerminal(text):
	global outputLock
	outputLock.acquire()
	print (text)
	outputLock.release()      

class MyConfig:
	def __init__(self):
		self.resDiffFile = ".dapscompare-diff.json"
		self.resHashFile = ".dapscompare-hash.json"
		
		# set standard values for all other needed parameters
		self.directory = os.getcwd()+"/"
		
		# 1 = build reference
		# 2 = build comparison and run tests (standard)
		# 3 = view results of last run
		# 4 = clean
		self.mode = 0
		
		# usually show GUI after comparison
		if "DISPLAY" in os.environ:
			self.noGui = False
		else:
			self.noGui = True
		
		if self.noGui == True:
			self.filetypes = ['pdf']
		else:
			self.filetypes = ['pdf','html']
		
		self.dapsParam = "--force"
		
		self.htmlWidth = [1280]
		
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
			elif parameter.startswith("--html-width="):
				self.htmlWidth = parameter[13:].split(",")
			

class DataCollector:
	def __init__(self):
		# compare or reference mode, new empty diff list
		self.imgDiffs = []
		# view mode, load existing diff list
		if cfg.mode == 3:
			imagesList = readFile(cfg.directory+cfg.resDiffFile)
			if imagesList == False:
				print("Nothing to do.")
				sys.exit()
			self.imgDiffs = json.loads(imagesList)
		
		self.depHashes = {}
		# hashes of dependencies like image width and filetype
		fileContent = readFile(cfg.directory+cfg.resHashFile)		
		if (fileContent != False and len(fileContent)>2):
			self.depHashes = json.loads(fileContent)

def spawnWorkerThreads():
	# get number of available cpus. 
	# we want to compile as many test cases with daps at the same time 
	# as we can
	
	print("\n=== Parameters ===\n")
	
	cpus = multiprocessing.cpu_count()
	print("Number of CPUs: "+str(cpus))
	print("Working Directory: "+cfg.directory)
	print("Building: "+str(cfg.filetypes))
	global foldersLock, outputLock
	foldersLock = threading.Lock()
	threads = []
	qWebWorkers = []
	outputLock = threading.Lock()
	
	findTestcases()
	
	if folders.qsize() < cpus:
		cpus = folders.qsize()
	
	print ("\n=== Creating "+str(cpus)+" Threads ===\n")

	for threadX in range(0,cpus):
		thread = myWorkThread(threadX, "Thread-"+str(threadX), threadX)
		thread.start()
		threads.append(thread)

	# Wait for all threads to complete
	for t in threads:
		t.wait()
	print("All threads finished.")
	
	if cfg.mode == 2:
		writeFile(cfg.directory+cfg.resDiffFile,json.dumps(dataCollection.imgDiffs))
	writeFile(cfg.directory+cfg.resHashFile,json.dumps(dataCollection.depHashes))

def findTestcases():
	global folders,foldersLock
	folders = queue.Queue()
	foldersLock = threading.Lock()
	n = 1
	print("\n=== Test Cases ===\n")
	for testcase in os.listdir(cfg.directory):
		if(os.path.isdir(cfg.directory+"/"+testcase)):
			print(str(n)+": "+testcase)
			foldersLock.acquire()
			folders.put(cfg.directory+testcase+"/")
			foldersLock.release()
			n = n + 1
	
def cleanDirectories():
	# replace with in-python code and remove subprocess import
	my_env = os.environ.copy()
	findTestcases()
	testcaseSubfolders = ['dapscompare-reference','dapscompare-comparison','dapscompare-result','build']
	while(True):
		testcase = ""
		foldersLock.acquire()
		if(folders.empty() == False):
			testcase = folders.get()
		foldersLock.release()
		if(testcase == ""):
			break
		print("cleaning "+testcase)
		for subfolder in testcaseSubfolders:
			try:
				shutil.rmtree(testcase+"/"+subfolder)
			except:
				pass
	print("cleaning dapscompare result files")
	try:
		os.remove(cfg.directory+cfg.resHashFile)
	except:
		pass
	try:
		os.remove(cfg.directory+cfg.resDiffFile)	
	except:
		pass

def spawnGui():
	if cfg.noGui == False:
		print("Starting Qt GUI")
		if len(dataCollection.imgDiffs) > 0:
			ex = qtImageCompare(cfg,dataCollection)
			sys.exit(app.exec_())
		
def main():
	global app
	
	if "DISPLAY" in os.environ:
		app = QtGui.QApplication(sys.argv)
	else:
		app = QtCore.QCoreApplication(sys.argv)
		
	global cfg, dataCollection, dataCollectionLock
	cfg = MyConfig()
	dataCollection = DataCollector()
	dataCollectionLock = threading.Lock()
	
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
