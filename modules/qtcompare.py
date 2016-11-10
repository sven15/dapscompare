from PyQt4 import QtGui, QtCore
import numpy
import sys

class qtImageCompare(QtGui.QMainWindow):
	# list images format list of triple reference image path, comparison image path, difference map image path 
	# [['reference path', 'comparison path', 'diffmap path'], ['reference path', 'comparison path', 'diffmap path'], [...] ...]
	def __init__(self,imagesList):
		super(qtImageCompare, self).__init__()
		self.initUI(imagesList)
        
	def initUI(self,imagesList):
		self.imagesList = imagesList
		self.imagePos = 0
		self.screenShape = QtGui.QDesktopWidget().screenGeometry()
		#self.resize(self.screenShape.width(), self.screenShape.height())
		self.resize(800,600)

		# Left image (reference)
		self.leftImage = QtGui.QLabel(self)
		self.leftImage.installEventFilter(self)
		self.leftImage.setAlignment(QtCore.Qt.AlignCenter)
		
		# Right image (comparison)
		self.rightImage = QtGui.QLabel(self)
		self.rightImage.installEventFilter(self)
		self.rightImage.setAlignment(QtCore.Qt.AlignCenter)
		
		# Next button
		self.btnNext = QtGui.QPushButton('Next', self)
		self.btnNext.clicked.connect(self.nextImage)
		
		# Previous button
		self.btnPrev = QtGui.QPushButton('Previous', self)
		self.btnPrev.clicked.connect(self.prevImage)
		
		# load initial images
		self.loadImage(imagesList[self.imagePos])
		
		self.show()
	
	@QtCore.pyqtSlot()
	def nextImage(self):
		self.imagePos = self.imagePos
		self.loadImage(self.imagesList[self.imagePos])
	
	@QtCore.pyqtSlot()
	def prevImage(self):
		self.imagePos = self.imagePos
		self.loadImage(self.imagesList[self.imagePos])
		
	def loadImage(self,path):
		self.pixmapLeft = QtGui.QPixmap(path[0])
		self.pixmapRight = QtGui.QPixmap(path[1])

		self.leftImage.setPixmap(self.pixmapLeft)
		self.rightImage.setPixmap(self.pixmapRight)
		
		self.calcPositions()
		
		#QtGui.QMessageBox.information(self,"asdf",str(width))
		

		self.rightImage.setPixmap(self.pixmapRight.scaled(
			self.rightImage.width(), self.rightImage.height(),
			QtCore.Qt.KeepAspectRatio,QtCore.Qt.SmoothTransformation))
		self.leftImage.setPixmap(self.pixmapLeft.scaled(
			self.leftImage.width(), self.leftImage.height(),
			QtCore.Qt.KeepAspectRatio,QtCore.Qt.SmoothTransformation))
		#self.show()

	def calcPositions(self):
		width = self.width()
		height = self.height()
		self.leftImage.move(0,0)
		self.leftImage.resize(width/2,height-70)
		self.rightImage.move(int(width/2)+1,0)
		self.rightImage.resize(width/2,height-70)
		self.btnNext.move(width - 120, height - 50)
		self.btnPrev.move(width - 240, height - 50)
		
	def resizeEvent(self,resizeEvent):
		self.calcPositions()
		
	def eventFilter(self, widget, event):
		if (event.type() == QtCore.QEvent.Resize and widget is self.leftImage):
			self.leftImage.setPixmap(self.pixmapLeft.scaled(
				self.leftImage.width(), self.leftImage.height(),
				QtCore.Qt.KeepAspectRatio,QtCore.Qt.SmoothTransformation))
		if (event.type() == QtCore.QEvent.Resize and widget is self.rightImage):
			self.rightImage.setPixmap(self.pixmapRight.scaled(
				self.rightImage.width(), self.rightImage.height(),
				QtCore.Qt.KeepAspectRatio,QtCore.Qt.SmoothTransformation))
		return QtGui.QMainWindow.eventFilter(self, widget, event)
		
def main():
	app = QtGui.QApplication(sys.argv)
	ex = qtImageCompare([['../testcases/hitchhiker/dapscompare-reference/page-1.png','../testcases/hitchhiker/dapscompare-comparison/page-1.png','../testcases/hitchhiker/dapscompare-result/page-1.png']])
	sys.exit(app.exec_())

if __name__ == '__main__':
	main()
