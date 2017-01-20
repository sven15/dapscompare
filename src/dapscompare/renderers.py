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
from subprocess import check_output, Popen, PIPE
from .helpers import modeToName, registerHash

def renderHtml(pathHtml,pageWidth,pathPng):
	# convert all PDF pages into numbered images and place them in reference or comparison folder
	head, tail = os.path.split(pathHtml)
	somestring = os.path.join(os.path.dirname(os.path.realpath(__file__)), "html2png.py")+" "+pathHtml+" "+os.path.join(pathPng, tail+".png")+" "+str(pageWidth)
	my_env = os.environ.copy()
	process = Popen([somestring], env=my_env, shell=True, stdout=PIPE, stderr=PIPE)
	process.wait()

def renderPdf(pathPdf,pageWidth,pathPng):
	# convert all PDF pages into numbered images and place them in reference or comparison folder
	somestring = "/usr/bin/convert -density 110 "+pathPdf+" -quality 100 -background white -alpha remove "+pathPng+"/page-%03d.png"
	my_env = os.environ.copy()
	process = Popen([somestring], env=my_env, shell=True, stdout=PIPE, stderr=PIPE)
	process.wait()

# slower performance than native imagemagick / convert command
def renderPdfWand(pathPdf, pathPngDir):
	all_pages = Image(filename=pathPdf , resolution=100)        # PDF will have several pages.
	for x, page in enumerate(all_pages.sequence):    # Just work on first page
		with Image(page) as i:
			i.format = 'png'
			i.background_color = Color('white')
			i.alpha_channel = 'remove'
			#i.alpha_channel = False
			#i.save(filename=pathPngDir+'/page-%s.png' % x)
			i.save(filename=pathPngDir+'/page-%03d.png')

#find the PDF files in build folder and convert to png
def pdfItems(testcase,cfg,dataCollection):
	folderName = testcase+modeToName(cfg.mode)+"/"+registerHash({'Type': 'pdf'},dataCollection)
	if not os.path.exists(folderName):
		os.makedirs(folderName)
	yield (testcase+"build/*/*.pdf",100,folderName)

#find HTML files in build folder and convert to png
def htmlItems(testcase,cfg,dataCollection):
	for build in os.listdir(testcase+"build"):
		if not build.startswith("."):
			for htmlBuild in os.listdir(testcase+"build/"+build+"/html/"):
				for htmlFile in os.listdir(testcase+"build/"+build+"/html/"+htmlBuild):
					for width in cfg.htmlWidth:
						folderName = testcase+modeToName(cfg.mode)+"/"+registerHash({'Type': 'html', 'Width': str(width), 'File Name': htmlBuild+htmlFile},dataCollection)+"/"
						if not os.path.exists(folderName):
							os.makedirs(folderName)
						if not os.path.islink(testcase+"build/"+build+"/html/"+htmlBuild+"/"+htmlFile):
							yield (testcase+"build/"+build+"/html/"+htmlBuild+"/"+htmlFile,width,folderName)

#find Single HTML files in build folder and convert to png
def singleHtmlItems(testcase,cfg,dataCollection):
	for build in os.listdir(testcase+"build"):
		if not build.startswith("."):
			for htmlBuild in os.listdir(testcase+"build/"+build+"/single-html/"):
				for htmlFile in os.listdir(testcase+"build/"+build+"/single-html/"+htmlBuild):
					for width in cfg.htmlWidth:
						folderName = testcase+modeToName(cfg.mode)+"/"+registerHash({'Type': 'single-html', 'Width': str(width), 'File Name': htmlBuild+htmlFile},dataCollection)+"/"
						if not os.path.exists(folderName):
							os.makedirs(folderName)
						if not os.path.islink(testcase+"build/"+build+"/single-html/"+htmlBuild+"/"+htmlFile):
							yield (testcase+"build/"+build+"/single-html/"+htmlBuild+"/"+htmlFile,width,folderName)

#find EPUB files in build folder and convert to png
def epubItems(testcase,cfg,dataCollection):
	import zipfile
	for build in os.listdir(testcase+"build"):
		if not build.startswith("."):
			for epub in os.listdir(testcase+"build/"+build+"/"):
				if epub.endswith(".epub"):
					os.makedirs(testcase+"build/"+build+"/"+epub[0:-5]+"/")
					with zipfile.ZipFile(testcase+"build/"+build+"/"+epub, 'r') as zip_ref:
						zip_ref.extractall(testcase+"build/"+build+"/"+epub[0:-5]+"/")
					for htmlFile in os.listdir(testcase+"build/"+build+"/"+epub[0:-5]+"/OEBPS/"):
						for width in cfg.htmlWidth:
							folderName = testcase+modeToName(cfg.mode)+"/"+registerHash({'Type': 'epub', 'Width': str(width), 'File Name': epub},dataCollection)+"/"
							if not os.path.exists(folderName):
								os.makedirs(folderName)
							if not os.path.islink(testcase+"build/"+build+"/"+epub[0:-5]+"/OEBPS/"+htmlFile):
								yield (testcase+"build/"+build+"/"+epub[0:-5]+"/OEBPS/"+htmlFile,width,folderName)
