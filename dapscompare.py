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
			# compile DC file to either reference or comparison folder, depending on mode
			dapsCompile(testcase)
			if(configSettings.mode == 2):
				runTests(testcase)

def dapsCompile(testcase):
	# find DC files
	for filename in os.listdir("./testcases/"+testcase):
		if(filename[0:2] == "DC"):
			# run daps on dc files and create PDFs
			my_env = os.environ.copy()
			process = Popen(["cd ./testcases/"+testcase+" && /usr/bin/daps -d "+filename+" pdf"], env=my_env, shell=True, stdout=PIPE, stderr=PIPE)
			process.wait()
			
			# convert all PDF pages into numbered images and place them in reference or comparison folder
			if(configSettings.mode == 1):
				somestring = "cd ./testcases/"+testcase+" && /usr/bin/convert -density 150 build/*/*.pdf -quality 100 -background white -alpha remove dapscompare-reference/page.png"
			elif(configSettings.mode == 2):
				somestring = "cd ./testcases/"+testcase+" && /usr/bin/convert -density 150 build/*/*.pdf -quality 100 -background white -alpha remove dapscompare-comparison/page.png"
			process = Popen([somestring], env=my_env, shell=True, stdout=PIPE, stderr=PIPE)
			process.wait()
	
def runTests(testcase):
	# run tests on images in reference and comparison folder
	for filename in os.listdir("./testcases/"+testcase+"/dapscompare-comparison/"):
		referencePath = "./testcases/"+testcase+"/dapscompare-reference/"+filename
		comparisonPath = "./testcases/"+testcase+"/dapscompare-comparison/"+filename
		diffPath = "./testcases/"+testcase+"/dapscompare-result/"+filename
		imgRef = imread(referencePath)
		imgComp = imread(comparisonPath)
		imgDiff = imgRef - imgComp
		global diffCollectionLock, diffCollection
		imsave(diffPath,imgDiff)
		if numpy.count_nonzero(imgDiff) > 0:
			outputTerminal("Image "+"./testcases/"+testcase+"/dapscompare-comparison/"+filename+" has changed.")
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
		# 1 = build reference
		# 2 = build comparison and run tests
		self.mode = 2

		# show all changes in qt interface
		self.visual = False

class DiffCollector:
	def __init__(self):
		self.collection = []

def cli_interpreter():
	for parameter in sys.argv:
		if parameter == "compare":
			configSettings.mode = 2
		if parameter == "reference":
			configSettings.mode = 1
		if parameter == "--help":
			f = open('MANUAL', 'r')
			print(f.read())
			f.close()
			sys.exit()
		if parameter == "--visual":
			configSettings.visual = True

def main():
	global configSettings, diffCollection, diffCollectionLock
	configSettings = MyConfig()
	diffCollection = DiffCollector()
	diffCollectionLock = threading.Lock()
	
	cli_interpreter()
	
	
		
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
	#print ("Exiting Main Thread")
	if configSettings.visual and configSettings.mode:
		app = QtGui.QApplication(sys.argv)
		ex = qtImageCompare(diffCollection.collection)
		sys.exit(app.exec_())

if __name__ == "__main__":
    main()
