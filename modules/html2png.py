#!/usr/bin/env python3
import sys, signal, os, time, math

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
		image = QImage(self.qwPage.viewportSize(), QImage.Format_ARGB32)
		painter = QPainter(image)
		self.qwPage.mainFrame().render(painter)
		painter.end()
		targetHeight = self.width * 1.4142
		if image.height() > targetHeight:
			numSplits = math.ceil(image.height() / targetHeight)
			for x in range(0,numSplits):
				start = (x) * targetHeight
				#end = x * targetHeight - 1
				print( 0, int(start), image.width(), targetHeight-1)
				copy = image.copy( 0, int(start), image.width(), targetHeight-1)
				copy.save(self.target[:-4]+"."+str(x)+".png")
		else:
			image.save(self.target)
		sys.exit(0)

app = QApplication(sys.argv)
asdf = html2png(sys.argv[1],sys.argv[2],sys.argv[3])
sys.exit(app.exec_())
