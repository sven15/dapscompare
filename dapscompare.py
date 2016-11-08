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
		while(True):
			foldersLock.acquire()
			testcase = ""
			if(folders.empty() == False):
				testcase = folders.get()
			foldersLock.release()
			if(testcase == ""):
				break
			outputTerminal(self.name+" now working on "+testcase)

def outputTerminal(text):
	global outputLock
	outputLock.acquire()
	print (text)
	outputLock.release()      

def main():
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
