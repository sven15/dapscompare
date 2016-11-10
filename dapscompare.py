#!/usr/bin/env python3

import multiprocessing
import threading
import time
import os
import queue
import sys
from subprocess import check_output, Popen, PIPE
from scipy.misc import *

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
	# find DC files
	for filename in os.listdir("./testcases/"+testcase):
		if(filename[0:2] == "DC"):
			# run daps on dc files and create PDFs
			my_env = os.environ.copy()
			process = Popen(["cd ./testcases/"+testcase+" && /usr/bin/daps -d "+filename+" pdf"], env=my_env, shell=True, stdout=PIPE, stderr=PIPE)
			process.wait()
			
			# convert all PDF pages into numbered images and place them in reference or comparison folder
			global mode
			if(mode == 1):
				somestring = "cd ./testcases/"+testcase+" && /usr/bin/convert build/*/*.pdf dapscompare-reference/page.png"
			elif(mode == 2):
				somestring = "cd ./testcases/"+testcase+" && /usr/bin/convert build/*/*.pdf dapscompare-comparison/page.png"
			process = Popen([somestring], env=my_env, shell=True, stdout=PIPE, stderr=PIPE)
			process.wait()
	
def runTests(testcase):
	# run tests on images in reference and comparison folder
	print("./testcases/"+testcase+"/dapscompare-comparison/")
	for filename in os.listdir("./testcases/"+testcase+"/dapscompare-comparison/"):
		image1 = imread("./testcases/"+testcase+"/dapscompare-reference/"+filename)
		image2 = imread("./testcases/"+testcase+"/dapscompare-comparison/"+filename)
		image3 = image1 - image2

		imsave("./testcases/"+testcase+"/dapscompare-result/"+filename,image3)
	

def outputTerminal(text):
	global outputLock
	outputLock.acquire()
	print (text)
	outputLock.release()      

def cli_interpreter():
	for parameter in sys.argv:
		if parameter == "compare":
			global mode
			mode = 2
		if parameter == "reference":
			global mode
			mode = 1

def main():
	global mode
	# 1 = build reference
	# 2 = build comparison and run tests
	mode = 2
	
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
	print ("Exiting Main Thread")

if __name__ == "__main__":
    main()
