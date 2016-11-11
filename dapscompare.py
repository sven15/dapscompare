#!/usr/bin/env python3

import multiprocessing
import threading
import time
import os
import queue
import sys
from subprocess import check_output, Popen, PIPE
from scipy.misc import *
import numpy
from modules.qtcompare import *
from PyQt4 import QtGui, QtCore
from modules.helpers import *
import json

class myThread (threading.Thread):
	def __init__(self, threadID, name, counter):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.name = name
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
			# create dapscompare target folders
			for dapsfolder in ['/dapscompare-comparison','/dapscompare-reference','/dapscompare-result']:
				if not os.path.exists("./testcases/"+testcase+dapsfolder):
					os.makedirs("./testcases/"+testcase+dapsfolder)
			# compile DC file to either reference or comparison folder, depending on mode
			dapsCompilePDF(testcase)
			if(configSettings.mode == 2):
				runTestsPDF(testcase)
		outputTerminal(self.name+" finished")

def dapsCompilePDF(testcase):
	# create dapscompare target folders
	for dapsfolder in ['/dapscompare-comparison/pdf','/dapscompare-reference/pdf','/dapscompare-result/pdf']:
		if not os.path.exists("./testcases/"+testcase+dapsfolder):
			os.makedirs("./testcases/"+testcase+dapsfolder)
	# find DC files
	for filename in os.listdir("./testcases/"+testcase):
		if(filename[0:2] == "DC"):
			# run daps on dc files and create PDFs
			my_env = os.environ.copy()
			process = Popen(["cd ./testcases/"+testcase+" && /usr/bin/daps --force -d "+filename+" pdf"], env=my_env, shell=True, stdout=PIPE, stderr=PIPE)
			process.wait()
			
			# convert all PDF pages into numbered images and place them in reference or comparison folder
			if(configSettings.mode == 1):
				somestring = "cd ./testcases/"+testcase+" && /usr/bin/convert -density 110 build/*/*.pdf -quality 100 -background white -alpha remove dapscompare-reference/pdf/page.png"
			elif(configSettings.mode == 2):
				somestring = "cd ./testcases/"+testcase+" && /usr/bin/convert -density 110 build/*/*.pdf -quality 100 -background white -alpha remove dapscompare-comparison/pdf/page.png"
			process = Popen([somestring], env=my_env, shell=True, stdout=PIPE, stderr=PIPE)
			process.wait()
	
def runTestsPDF(testcase):
	# run tests on images in reference and comparison folder
	for filename in os.listdir("./testcases/"+testcase+"/dapscompare-comparison/pdf/"):
		referencePath = "./testcases/"+testcase+"/dapscompare-reference/pdf/"+filename
		comparisonPath = "./testcases/"+testcase+"/dapscompare-comparison/pdf/"+filename
		diffPath = "./testcases/"+testcase+"/dapscompare-result/pdf/"+filename
		imgRef = imread(referencePath)
		imgComp = imread(comparisonPath)
		imgDiff = imgRef - imgComp
		global diffCollectionLock, diffCollection
		imsave(diffPath,imgDiff)
		if numpy.count_nonzero(imgDiff) > 0:
			outputTerminal("Image "+"./testcases/"+testcase+"/dapscompare-comparison/pdf/"+filename+" has changed.")
			diffCollectionLock.acquire()
			diffCollection.collection.append([referencePath, comparisonPath, diffPath])
			diffCollectionLock.release()

def outputTerminal(text):
	global outputLock
	outputLock.acquire()
	print (text)
	outputLock.release()      

class MyConfig:
	def __init__(self):
		# set standard values for all other needed parameters
		
		# 1 = build reference
		# 2 = build comparison and run tests (standard)
		# 3 = view results of last run
		# 4 = clean
		self.mode = 0
		
		# usually show GUI after comparison
		self.noGui = False
		
		# first read CLI parameters
		for parameter in sys.argv:
			if parameter == "compare":
				self.mode = 2
			if parameter == "reference":
				self.mode = 1
			if parameter == "view":
				self.mode = 3
			if parameter == "clean":
				self.mode = 4
			if parameter == "--help":
				f = open('README', 'r')
				print(f.read())
				f.close()
				sys.exit()
			if parameter == "--no-gui":
				self.noGui = True

class DiffCollector:
	def __init__(self):
		self.collection = []

def spawnWorkerThreads():
	# get number of available cpus. 
	# we want to compile as many test cases with daps at the same time 
	# as we can
	cpus = multiprocessing.cpu_count()
	print("CPUs: "+str(cpus))
	global foldersLock, outputLock
	foldersLock = threading.Lock()
	threads = []
	outputLock = threading.Lock()

	global folders
	folders = queue.Queue()
		
	for testcase in os.listdir('./testcases'):
		print("Found test case: "+testcase)
		foldersLock.acquire()
		folders.put(testcase)
		foldersLock.release()

	for threadX in range(0,cpus):
		thread = myThread(threadX, "Thread-"+str(threadX), threadX)
		thread.start()
		threads.append(thread)

	# Wait for all threads to complete
	for t in threads:
		t.join()
	print("All threads finished.")
	if configSettings.mode == 2:
		writeFile("./results.json",json.dumps(diffCollection.collection))

def cleanDirectories():
	my_env = os.environ.copy()
	somestring = "rm -r ./testcases/*/build/* && rm -r .testcases/*/dapscompare-*/* && rm results.json"
	process = Popen([somestring], env=my_env, shell=True, stdout=PIPE, stderr=PIPE)

def spawnGui():
	app = QtGui.QApplication(sys.argv)
	if configSettings.mode == 2:
		ex = qtImageCompare(diffCollection.collection)
	if configSettings.mode == 3:
		ex = qtImageCompare()
	sys.exit(app.exec_())
		
def main():
	global configSettings, diffCollection, diffCollectionLock
	configSettings = MyConfig()
	diffCollection = DiffCollector()
	diffCollectionLock = threading.Lock()
	
	if configSettings.mode == 1 or configSettings.mode == 2:
		spawnWorkerThreads()
	
	elif (configSettings.mode == 2 and not configSettings.noGui) or configSettings.mode == 3:
		spawnGui()
		
	elif configSettings.mode == 4:
		cleanDirectories()
		
	else:
		print("Nothing to do. Use --help.")

if __name__ == "__main__":
    main()
