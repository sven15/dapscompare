# The MIT License (MIT)
# 
# Copyright (c) 2017, Sven Seeberg-Elverfeldt <sseebergelverfeldt@suse.com>
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
from PyQt5 import QtGui, QtCore

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
    result = md5.hexdigest()
    #print(hashstring + " " + result)
    return result


def listFiles(folder):
    result = []
    #print("Listing "+folder)
    for item in os.listdir(folder):
        if os.path.isfile(folder+item):
            result.append(item)
    return result


class myWorkThread (QtCore.QThread):
    # worker threads which compile the DC files and compare the results
    def __init__(self, cfg, dataCollection, folders, foldersLock, threadID, name, counter):
        QtCore.QThread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
        self.cfg = cfg
        self.dataCollection = dataCollection
        self.folders = folders
        self.foldersLock = foldersLock

    def __del__(self):
        self.wait()

    def run(self):
        from .daps import daps
        # we want the threads to keep running until the queue of test cases is empty
        while True:
            testcase = ""
            self.foldersLock.acquire()
            if(self.folders.empty() == False):
                testcase = self.folders.get()
            self.foldersLock.release()
            # finish the thread if queue is empty
            if(testcase == ""):
                break
            if self.cfg.silent == False: print(self.name+" now working on "+testcase)

            cleanDirectories(self.cfg, testcaseSubfolders=['build'], rmConfigs=False, testcase=testcase)

            # compile DC files
            myDaps = daps(testcase, self.cfg.dapsParam, self.cfg.filetypes)
            for filetype in self.cfg.filetypes:
                if filetype not in myDaps.success:
                    if self.cfg.silent == False: print(testcase + " failed to build " + filetype)

            # render results to images
            runRenderers(self.cfg, self.dataCollection, testcase)

            if(self.cfg.mode == 2):
                runTests(self.cfg, self.dataCollection, testcase)
        if self.cfg.silent == False: print(self.name+" finished")


# prepare for file types and then call the appropriate rendering modules
def runRenderers(cfg, dataCollection, testcase):
    from .renderers import pdfItems, renderPdf, htmlItems, singleHtmlItems, epubItems, renderHtml
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


# diff images of reference and compare run and save result
def runTests(cfg, dataCollection, testcase):
    for md5, description in dataCollection.depHashes.items():
        if not description['testcase'] == testcase:
            continue
        referencePath = testcase+"dapscompare-reference/"+md5+"/"
        comparisonPath = testcase+"dapscompare-comparison/"+md5+"/"
        numRefImgs = len(listFiles(referencePath))
        numComImgs = len(listFiles(comparisonPath))
        if (numRefImgs - numComImgs) != 0 and numRefImgs != 0:
            dataCollection.addDiffNumPages([referencePath, numRefImgs, numComImgs])
            continue
        cleanDirectories(cfg, testcaseSubfolders=['dapscompare-comparison', 'dapscompare-result'], rmConfigs=False, keepDirs=True, testcase=testcase)
        if not os.path.exists(referencePath):
            if cfg.silent == False: print("No reference images for "+dataCollection.depHashes[md5])
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
                    dataCollection.addImgDiffs([referencePath+filename, comparisonPath+filename, diffFolder+filename])
            except:
                dataCollection.addDiffNumPages([referencePath, numRefImgs, numComImgs])


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
                self.filetypes = parameter[12:].split(",")
            elif parameter.startswith("--html-width="):
                self.htmlWidth = parameter[13:].split(",")
            elif parameter == "--ignore-conf":
                self.loadConfigBool = False
            elif parameter == "--json":
                self.returnJSON = True
                self.silent = True

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

        self.silent = False
        self.returnJSON = False

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
                if cfg.silent == False: print("Nothing to do.")
                sys.exit()
            self.imgDiffs, self.diffNumPages = json.loads(imagesList)

        # hashes of dependencies like image width and filetype
        self.depHashes = {}
        fileContent = readFile(cfg.directory+cfg.resHashFile)
        if (fileContent is not False and len(fileContent) > 2):
            self.depHashes = json.loads(fileContent)


    def addDiffNumPages(self, item):
        self.lock.acquire()
        self.diffNumPages.append(item)
        self.lock.release()


    def addImgDiffs(self, item):
        self.lock.acquire()
        self.imgDiffs.append(item)
        self.lock.release()

def spawnWorkerThreads(cfg, dataCollection):
    # get number of available cpus.
    # we want to compile as many test cases with daps at the same time
    # as we can

    if cfg.silent == False: print("\n=== Parameters ===\n")

    cpus = multiprocessing.cpu_count()
    #cpus = 1
    if cfg.silent == False: print("Number of CPUs: "+str(cpus))
    if cfg.silent == False: print("Working Directory: "+cfg.directory)
    if cfg.silent == False: print("Building: "+str(cfg.filetypes))

    threads = []

    folders, foldersLock = queueTestcases(cfg)

    if folders.qsize() < cpus:
        cpus = folders.qsize()

    if cfg.silent == False: print("\n=== Creating "+str(cpus)+" Threads ===\n")

    for threadX in range(0, cpus):
        thread = myWorkThread(cfg, dataCollection, folders, foldersLock, threadX, "Thread-"+str(threadX), threadX)
        thread.start()
        threads.append(thread)

    # Wait for all threads to complete
    for t in threads:
        t.wait()
    if cfg.silent == False: print("All threads finished.")
    if cfg.mode == 2:
        writeFile(cfg.directory+cfg.resDiffFile, json.dumps([dataCollection.imgDiffs, dataCollection.diffNumPages], sort_keys=True))
    writeFile(cfg.directory+cfg.resHashFile, json.dumps(dataCollection.depHashes, sort_keys=True))


def queueTestcases(cfg, silent=False):
    folders = queue.Queue()
    foldersLock = threading.Lock()
    if cfg.silent == False: print("\n=== Test Cases ===\n")
    n = 1
    foldersLock.acquire()
    for testcase in findTestcases(cfg):
        if cfg.silent == False:
            print(str(n)+". "+testcase)
            n = n + 1
        folders.put(cfg.directory+testcase+"/")
    foldersLock.release()
    return folders, foldersLock


def findTestcases(cfg):
    for testcase in os.listdir(cfg.directory):
        if(os.path.isdir(cfg.directory+"/"+testcase)):
            yield testcase


def cleanDirectories(cfg, testcaseSubfolders=['dapscompare-reference', 'dapscompare-comparison', 'dapscompare-result', 'build'], rmConfigs=True, testcase=False, keepDirs=False):
    if testcase is False:
        testcases = findTestcases(cfg)
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


def printResults(cfg, dataCollection):
    if cfg.returnJSON == False:
        print("\n=== Changed Images ===\n")
        for item in dataCollection.imgDiffs:
            print(item[0])
        print("\n=== Differing Page Numbers ===\n")
        for item in dataCollection.diffNumPages:
            print(item[0])
    else:
        print(json.dumps(dataCollection.imgDiffs, sort_keys=True))
