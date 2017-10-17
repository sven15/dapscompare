# The MIT License (MIT)
# 
# Copyright (c) 2017, Sven Seeberg-Elverfeldt <sseebergelverfeldt@suse.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from subprocess import check_output, Popen, PIPE
import os

class daps:
    def __init__(self, testcase, dapsParam, filetypes = []):
        self.testcase = testcase
        self.filetypes = filetypes
        self.dapsParam = dapsParam

        self.createFolders()

        self.dcFiles = []

        self.findDcFiles()

        self.success = self.compileAllWait()

    def findDcFiles(self):
        for filename in os.listdir(self.testcase):
            if(filename[0:2] == "DC"):
                self.dcFiles.append(self.testcase+filename)

    def createFolders(self):
        # create dapscompare target folders
        for filetype in self.filetypes:
            for targetfolder in ['/dapscompare-comparison/','/dapscompare-reference/','/dapscompare-result/']:
                if not os.path.exists(self.testcase+targetfolder):
                    os.makedirs(self.testcase+targetfolder)

    def compilePdf(self):
        my_env = os.environ.copy()
        for dcFile in self.dcFiles:
            self.procDaps = Popen(["cd "+self.testcase+" && /usr/bin/daps "+self.dapsParam+" -d "+dcFile+" pdf"], env=my_env, shell=True, stdout=PIPE, stderr=PIPE)
            self.procDaps.wait()
            result = str(self.procDaps.returncode)
            return result

    def compileHtml(self):
        my_env = os.environ.copy()
        for dcFile in self.dcFiles:
            self.procHtml = Popen(["cd "+self.testcase+" && /usr/bin/daps "+self.dapsParam+" -d "+dcFile+" html"], env=my_env, shell=True, stdout=PIPE, stderr=PIPE)
            self.procHtml.wait()
            result = str(self.procHtml.returncode)
            return result

    def compileSingleHtml(self):
        my_env = os.environ.copy()
        for dcFile in self.dcFiles:
            self.procHtml = Popen(["cd "+self.testcase+" && /usr/bin/daps "+self.dapsParam+" -d "+dcFile+" html --single"], env=my_env, shell=True, stdout=PIPE, stderr=PIPE)
            self.procHtml.wait()
            result = str(self.procHtml.returncode)
            return result

    def compileEpub(self):
        my_env = os.environ.copy()
        for dcFile in self.dcFiles:
            self.procEpub = Popen(["cd "+self.testcase+" && /usr/bin/daps "+self.dapsParam+" -d "+dcFile+" epub"], env=my_env, shell=True, stdout=PIPE, stderr=PIPE)
            self.procEpub.wait()
            result = str(self.procEpub.returncode)
            return result

    def compileAllWait(self):
        success = []
        if 'pdf' in self.filetypes:
            if self.compilePdf() == "0":
                success.append('pdf')
        if 'html' in self.filetypes:
            if self.compileHtml() == "0":
                success.append('html')
        if 'single-html' in self.filetypes:
            if self.compileSingleHtml() == "0":
                success.append('single-html')
        if 'epub' in self.filetypes:
            if self.compileEpub() == "0":
                success.append('epub')
        return success
