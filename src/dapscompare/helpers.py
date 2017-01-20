# The MIT License (MIT)
# 
# Copyright (c) 2016, Sven Seeberg-Elverfeldt <sseebergelverfeldt@suse.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import os
import multiprocessing
import threading
import queue
import sys
import json
import shutil

from scipy.misc import imsave, imread
import numpy as np
from PyQt4 import QtGui, QtCore

def readFile(filePath):
	if(os.path.isfile(filePath)):
		f = open(filePath, 'r')
		content = f.read()
		f.close()
		return content
	else:
		return False


def writeFile(path,content):
	f = open(path,'w')
	f.write(content)
	f.close()


def modeToName(mode):
	if mode == 1:
		return "dapscompare-reference"
	if mode == 2:
		return "dapscompare-comparison"


def hashPath(path):
	import hashlib, os
	SHAhash = hashlib.sha1()
	if not os.path.exists (path):
		return False
	if os.path.isfile(path):
		readFileBlock(path,SHAhash)
	else:
		for root, dirs, files in os.walk(path):
			for names in files:
				filepath = os.path.join(root,names)
				readFileBlock(filepath,SHAhash)
	return SHAhash.hexdigest()


def readFileBlock(filepath,SHAhash):
	with open(filepath, 'rb') as f1:
		while True:
			buf = f1.read(4096)
			if not buf : break
			SHAhash.update(hashlib.sha1(buf).hexdigest())


def registerHash(params,dataCollection):
	import json, hashlib
	# create md5sum of hash
	hashstring = json.dumps(params, sort_keys=True)
	md5 = hashlib.md5(hashstring.encode('utf-8'))
	# add md5sum and string to config and save to file in the end
	dataCollection.lock.acquire()
	dataCollection.depHashes[md5.hexdigest()] = params
	dataCollection.lock.release()
	return md5.hexdigest()


def listFiles(folder):
	result = []
	for item in os.listdir(folder):
		if os.path.isfile(folder+item):
			result.append(item)
	return result


class myWorkThread (QtCore.QThread):
	# worker threads which compile the DC files and compare the results
	def __init__(self, threadID, name, counter):
		QtCore.QThread.__init__(self)
		self.threadID = threadID
		self.name = name
		self.counter = counter

	def __del__(self):
		self.wait()

	def run(self):
		# we want the threads to keep running until the queue of test cases is empty
		while True:
			testcase = ""
			foldersLock.acquire()
			if(folders.empty() == False):
				testcase = folders.get()
			foldersLock.release()
			# finish the thread if queue is empty
			if(testcase == ""):
				break
			print(self.name+" now working on "+testcase)

			cleanDirectories(testcaseSubfolders=['build'], rmConfigs=False, testcase=testcase)
			# compile DC files
			daps(testcase, cfg.dapsParam, cfg.filetypes)

			# render results to images
			runRenderers(testcase)

			if(cfg.mode == 2):
				runTests(testcase)
		print(self.name+" finished")


# prepare for file types and then call the appropriate rendering modules
def runRenderers(testcase):
	for filetype in cfg.filetypes:
		if filetype == 'pdf':
			for renderItem in pdfItems(testcase, cfg, dataCollection):
				renderPdf(renderItem[0], renderItem[1], renderItem[2])
		elif filetype == 'html' and cfg.noGui is False:
			for renderItem in htmlItems(testcase, cfg, dataCollection):
				renderHtml(renderItem[0], renderItem[1], renderItem[2])
		elif filetype == 'single-html' and cfg.noGui is False:
			for renderItem in singleHtmlItems(testcase, cfg, dataCollection):
				renderHtml(renderItem[0], renderItem[1], renderItem[2])
		elif filetype == 'epub' and cfg.noGui is False:
			for renderItem in epubItems(testcase, cfg, dataCollection):
				renderHtml(renderItem[0], renderItem[1], renderItem[2])


def addDiffNumPages(item):
	dataCollection.lock.acquire()
	dataCollection.diffNumPages.append(item)
	dataCollection.lock.release()


def addImgDiffs(item):
	dataCollection.lock.acquire()
	dataCollection.imgDiffs.append(item)
	dataCollection.lock.release()


# diff images of reference and compare run and save result
def runTests(testcase):
	for md5, description in dataCollection.depHashes.items():
		referencePath = testcase+"dapscompare-reference/"+md5+"/"
		comparisonPath = testcase+"dapscompare-comparison/"+md5+"/"
		numRefImgs = len(listFiles(referencePath))
		numComImgs = len(listFiles(comparisonPath))
		if (numRefImgs - numComImgs) != 0 and numRefImgs != 0:
			addDiffNumPages([referencePath, numRefImgs, numComImgs])
			print("Differing number of result images from "+referencePath)
			continue
		cleanDirectories(testcaseSubfolders=['dapscompare-comparison', 'dapscompare-result'], rmConfigs=False, keepDirs=True, testcase=testcase)
		if not os.path.exists(referencePath):
			print("No reference images for "+dataCollection.depHashes[md5])
			continue
		diffFolder = testcase+"dapscompare-result/"+md5+"/"
		if not os.path.exists(diffFolder):
			os.makedirs(diffFolder)

		for filename in os.listdir(referencePath):
			imgRef = imread(referencePath+filename)
			imgComp = imread(comparisonPath+filename)
			try:
				imgDiff = imgRef - imgComp
				if np.count_nonzero(imgDiff) > 0:
					imsave(diffFolder+filename, imgDiff)
					print("Image "+comparisonPath+filename+" has changed.")
					addImgDiffs([referencePath+filename, comparisonPath+filename, diffFolder+filename])
			except:
				addDiffNumPages([referencePath, numRefImgs, numComImgs])


class MyConfig:
	def __init__(self):

		self.stdValues()

		self.cmdParams()

		if self.loadConfigBool:
			self.loadConfig()

	def cmdParams(self):
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
				from dapscompare import __file__ as dapscomparedir
				f = open(os.path.join(os.path.dirname(os.path.realpath(dapscomparedir)), 'README'), 'r')
				print(f.read())
				f.close()
				sys.exit()
			elif parameter == "--no-gui":
				self.noGui = True
			elif parameter.startswith("--daps="):
				self.dapsParam = parameter[7:]
			elif parameter.startswith("--testcases="):
				self.directory = parameter[12:]
			elif parameter.startswith("--filetypes="):
				self.filetypes = parameter[13:].split(",")
			elif parameter.startswith("--html-width="):
				self.htmlWidth = parameter[13:].split(",")
			elif parameter == "--ignore-conf":
				self.loadConfigBool = False

	def stdValues(self):
		self.resDiffFile = "dapscompare-diff.json"
		self.resHashFile = "dapscompare-hash.json"

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

		if self.noGui:
			self.filetypes = ['pdf']
		else:
			self.filetypes = ['pdf', 'html', 'single-html', 'epub']

		self.htmlWidth = [1280]

		self.dapsParam = "--force"

		self.loadConfigBool = True

	def loadConfig(self):
		content = readFile(self.directory+"/"+self.resHashFile)
		if content:
			self.filetypes = []
			content = json.loads(content)
			for hashsum in content:
				if content[hashsum]['Type'] not in self.filetypes:
					self.filetypes.append(content[hashsum]['Type'])
				if content[hashsum]['Type'] == "html":
					if int(content[hashsum]['Width']) not in self.htmlWidth:
						self.htmlWidth.append(int(content[hashsum]['Width']))


class DataCollector:
	def __init__(self,cfg):

		self.lock = threading.Lock()

		# if reference and comparison differ in number of pictures, store this here
		self.diffNumPages = []

		# compare or reference mode, new empty diff list
		self.imgDiffs = []
		# view mode, load existing diff list
		if cfg.mode == 3:
			imagesList = readFile(cfg.directory+cfg.resDiffFile)
			if imagesList is False:
				print("Nothing to do.")
				sys.exit()
			self.imgDiffs, self.diffNumPages = json.loads(imagesList)

		# hashes of dependencies like image width and filetype
		self.depHashes = {}
		fileContent = readFile(cfg.directory+cfg.resHashFile)
		if (fileContent is not False and len(fileContent) > 2):
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
	global outputLock

	threads = []
	outputLock = threading.Lock()

	queueTestcases()

	if folders.qsize() < cpus:
		cpus = folders.qsize()

	print("\n=== Creating "+str(cpus)+" Threads ===\n")

	for threadX in range(0, cpus):
		thread = myWorkThread(threadX, "Thread-"+str(threadX), threadX)
		thread.start()
		threads.append(thread)

	# Wait for all threads to complete
	for t in threads:
		t.wait()
	print("All threads finished.")
	if cfg.mode == 2:
		writeFile(cfg.directory+cfg.resDiffFile, json.dumps([dataCollection.imgDiffs, dataCollection.diffNumPages]))
	writeFile(cfg.directory+cfg.resHashFile, json.dumps(dataCollection.depHashes))


def queueTestcases(silent=False):
	global folders, foldersLock
	folders = queue.Queue()
	foldersLock = threading.Lock()
	if not silent:
		print("\n=== Test Cases ===\n")
	n = 1
	foldersLock.acquire()
	for testcase in findTestcases():
		if not silent:
			print(str(n)+". "+testcase)
			n = n + 1
		folders.put(cfg.directory+testcase+"/")
	foldersLock.release()


def findTestcases():
	for testcase in os.listdir(cfg.directory):
		if(os.path.isdir(cfg.directory+"/"+testcase)):
			yield testcase


def cleanDirectories(testcaseSubfolders=['dapscompare-reference', 'dapscompare-comparison', 'dapscompare-result', 'build'], rmConfigs=True, testcase=False, keepDirs=False):
	global foldersLock
	if testcase is False:
		testcases = findTestcases()
	else:
		testcases = [testcase]

	for testcase in testcases:
		for subfolder in testcaseSubfolders:
			try:
				if keepDirs:
					shutil.rmtree(testcase+"/"+subfolder+"/*")
				else:
					shutil.rmtree(testcase+"/"+subfolder)
			except:
				pass
	if rmConfigs:
		try:
			os.remove(cfg.directory+cfg.resHashFile)
		except:
			pass
		try:
			os.remove(cfg.directory+cfg.resDiffFile)
		except:
			pass


def spawnGui():
	if cfg.noGui is False:
		print("Starting Qt GUI")
		if len(dataCollection.imgDiffs) > 0 or len(dataCollection.diffNumPages) > 0:
			ex = qtImageCompare(cfg, dataCollection)
			sys.exit(app.exec_())


def printResults():
	print("\n=== Changed Images ===\n")
	for item in dataCollection.imgDiffs:
		print(item[0])
	print("\n=== Differing Page Numbers ===\n")
	for item in dataCollection.diffNumPages:
		print(item[0])
	print()
