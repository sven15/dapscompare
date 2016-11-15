#!/usr/bin/env python
import sys, signal, os

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtWebKit import QWebPage

# This class renders an image from a website using WebKit
class renderHTML():
	
	# get URL and pixel width as parameters. The width is only approximate
	def __init__(self,pageUrl,pageWidth,pathTarget = False):
		app = QApplication(sys.argv)
		self.qwPage = QWebPage()
		#signal.signal(signal.SIGINT, signal.SIG_DFL)
		self.finished = False
		self.pageUrl = pageUrl
		self.pathTarget = pathTarget+"/"
		print(pageUrl)
		size = QSize()
		size.setWidth(pageWidth)
		self.qwPage.setViewportSize(size)
		print("viewport")
		self.qwPage.connect(self.qwPage, SIGNAL("loadFinished(bool,"+self.thread+")"), self.onLoadFinished)
		print("loaded")
		self.qwPage.mainFrame().load(QUrl(pageUrl))

	# do not call this function. it is called via a signal
	def onLoadFinished(self,result):
		self.qwPage.setViewportSize(self.qwPage.mainFrame().contentsSize())
		# Paint this frame into an image
		self.image = QImage(self.qwPage.viewportSize(), QImage.Format_ARGB32)
		painter = QPainter(self.image)
		self.qwPage.mainFrame().render(painter)
		painter.end()
		head, tail = os.path.split(self.pageUrl)
		print(self.pathTarget+tail+".png")
		self.image.save(self.pathTarget+tail+".png")
	
	# this function returns the finished image. if the image is not finished, it waits for it
	def getImage(self):
		self.wait()
		if self.pathTarget == False:
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
