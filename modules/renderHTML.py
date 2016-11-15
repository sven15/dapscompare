#!/usr/bin/env python
import sys
import signal

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtWebKit import QWebPage

# This class renders an image from a website using WebKit
class renderHTML():
	
	# get URL and pixel width as parameters. The width is only approximate
	def __init__(self,pageUrl,pageWidth,pathTarget = False):
		#signal.signal(signal.SIGINT, signal.SIG_DFL)
		self.finished = False
		self.qwPage = QWebPage()
		size = QSize()
		size.setWidth(pageWidth)
		self.qwPage.setViewportSize(size)
		self.qwPage.connect(self.qwPage, SIGNAL("loadFinished(bool)"), self.onLoadFinished)
		self.qwPage.mainFrame().load(QUrl(pageUrl))

	# do not call this function. it is called via a signal
	def onLoadFinished(self,result):
		# Set the size of the (virtual) browser window
		self.qwPage.setViewportSize(self.qwPage.mainFrame().contentsSize())
		# Paint this frame into an image
		self.image = QImage(self.qwPage.viewportSize(), QImage.Format_ARGB32)
		painter = QPainter(self.image)
		self.qwPage.mainFrame().render(painter)
		painter.end()
		self.finished = True
	
	# this function returns the finished image. if the image is not finished, it waits for it
	def getImage(self):
		self.wait()
		if pathTarget == False:
			return self.image
		else:
			return True

	# is the image already finished? Only necessary if performance is important. it's also possible to check the self.finished property directly
	def isFinished(self):
		return self.finished
	
	# wait until rendering is finished
	def wait(self):
		while self.finished == False:
			pass
		return True
