#!/usr/bin/env python3

import multiprocessing
import scipy
import threading
import time
import os
import queue

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
			if(mode == 2):
				runTests(testcase)

def dapsCompile(testcase):
	pass
	# find DC files
	# run daps on dc files and create PDFs
	# convert all PDF pages into numberd images and place them in reference or comparison folder
	
def runTests(testcase):
	pass
	# run tests on images in reference and comparison folder

def outputTerminal(text):
	global outputLock
	outputLock.acquire()
	print (text)
	outputLock.release()      

def main():
	global mode
	# 1 = build reference
	# 2 = build comparison and run tests
	mode = 1
	
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
	print ("Exiting Main Thread")

if __name__ == "__main__":
    main()
