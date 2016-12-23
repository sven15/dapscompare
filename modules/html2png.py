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

import sys, signal, os, time, math

from io import BytesIO
from PIL import Image

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtWebKit import QWebPage

# This class renders an image from a website using WebKit
class html2png():
	
	# get URL and pixel width as parameters. The width is only approximate
	def __init__(self,source,target,width):
		
		self.width = int(width)
		self.target = target
		#self.app = QApplication(sys.argv)
		signal.signal(signal.SIGINT, signal.SIG_DFL)
		self.qwPage = QWebPage()

		size = QSize()
		size.setWidth(int(width))
		self.qwPage.setViewportSize(size)		

		self.qwPage.connect(self.qwPage, SIGNAL("loadFinished(bool)"), self.onLoadFinished)
		self.qwPage.mainFrame().load(QUrl(source))

	# do not call this function. it is called via a signal
	def onLoadFinished(self,result):
		if not result:
			sys.exit(1)

		# Set the size of the (virtual) browser window
		self.qwPage.setViewportSize(self.qwPage.mainFrame().contentsSize())

		# Paint this frame into an image
		image = QImage(self.qwPage.viewportSize(), QImage.Format_RGB32)
		painter = QPainter(image)
		self.qwPage.mainFrame().render(painter)
		painter.end()
		targetHeight = self.width * 1.4142
		if image.height() > targetHeight:
			numSplits = math.ceil(image.height() / targetHeight)
			for x in range(0,numSplits):
				start = (x) * targetHeight
				copy = image.copy( 0, int(start), image.width(), targetHeight-1)
				#copy.save(self.target[:-4]+"."+str(x)+".png")
				self.saveOptPNG(copy,self.target[:-4]+"."+str(x)+".png")
		else:
			#image.save(self.target)
			self.saveOptPNG(image,self.target)
		sys.exit(0)
	
	#optimize QImage PNG with PIL and save
	def saveOptPNG(self,img,path):
		buffer = QBuffer()
		buffer.open(QIODevice.ReadWrite)
		img.save(buffer, "PNG")

		strio = BytesIO()
		strio.write(buffer.data())
		buffer.close()
		strio.seek(0)
		pil_im = Image.open(strio)
		pil_im.save(path, "PNG", optimize=False,compress_level=9)

app = QApplication(sys.argv)
asdf = html2png(sys.argv[1],sys.argv[2],sys.argv[3])
sys.exit(app.exec_())
