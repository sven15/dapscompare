# The MIT License (MIT)
# 
# Copyright (c) 2017, Sven Seeberg-Elverfeldt <sseebergelverfeldt@suse.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from PyQt4 import QtGui, QtCore
import numpy as np
import sys
from scipy.misc import *
from .helpers import *
from PIL import ImageDraw, Image
from scipy.cluster.vq import kmeans2, whiten, kmeans
import json
import shutil
import time

gray_color_table = [QtGui.qRgb(i, i, i) for i in range(256)]


def spawnGui(app, cfg, dataCollection):
    from .qtcompare import qtImageCompare
    if cfg.noGui is False:
        if cfg.silent == False: print("Starting Qt GUI")
        if len(dataCollection.imgDiffs) > 0 or len(dataCollection.diffNumPages) > 0:
            ex = qtImageCompare(cfg, dataCollection)
            sys.exit(app.exec_())


def toQImage(im, copy=False):
    if im is None:
        return QtGui.QImage()

    if im.dtype == np.uint8:
        if len(im.shape) == 2:
            qim = QtGui.QImage(im.data, im.shape[1], im.shape[0], im.strides[0], QtGui.QImage.Format_Indexed8)
            qim.setColorTable(gray_color_table)
            return qim.copy() if copy else qim

        elif len(im.shape) == 3:
            if im.shape[2] == 3:
                qim = QtGui.QImage(im.data, im.shape[1], im.shape[0], im.strides[0], QtGui.QImage.Format_RGB888);
                return qim.copy() if copy else qim
            elif im.shape[2] == 4:
                qim = QtGui.QImage(im.data, im.shape[1], im.shape[0], im.strides[0], QtGui.QImage.Format_ARGB32);
                return qim.copy() if copy else qim

    raise NotImplementedException

class qtImageCompare(QtGui.QMainWindow):
    # list images format list of triple reference image path, comparison image path, difference map image path 
    # [['reference path', 'comparison path', 'diffmap path'], ['reference path', 'comparison path', 'diffmap path'], [...] ...]
    def __init__(self, cfg, dta):
        super(qtImageCompare, self).__init__()
        self.initUI(cfg,dta)
        
    def initUI(self,cfg,dta):
        self.viewDirectory = cfg.directory
        self.cfg = cfg
        imagesList = dta.imgDiffs
        self.depHashes = dta.depHashes
        self.imagesList = sorted(imagesList, key=lambda imagesList: imagesList[1])
        self.imagePos = 0
        self.screenShape = QtGui.QDesktopWidget().screenGeometry()
        self.resize(800,600)
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)

        # Left image (reference)
        self.leftImage = QtGui.QLabel(self)
        self.leftImage.installEventFilter(self)
        self.leftImage.setAlignment(QtCore.Qt.AlignCenter)

        # Right image (comparison)
        self.rightImage = QtGui.QLabel(self)
        self.rightImage.installEventFilter(self)
        self.rightImage.setAlignment(QtCore.Qt.AlignCenter)

        # Next button
        self.btnNext = QtGui.QPushButton('&Next', self)
        self.btnNext.clicked.connect(self.nextImage)

        # Previous button
        self.btnPrev = QtGui.QPushButton('&Previous', self)
        self.btnPrev.clicked.connect(self.prevImage)

        # Make reference button
        self.btnMakeRef = QtGui.QPushButton('Make &reference', self)
        self.btnMakeRef.clicked.connect(self.makeRef)
        self.btnMakeRef.setFixedWidth(140)

        self.statusText = QtGui.QLabel(self)
        self.statusText.setFixedHeight(50)

        # load initial images
        self.loadImage(imagesList[self.imagePos])

        self.show()

    @QtCore.pyqtSlot()
    def makeRef(self):
        shutil.copyfile(self.imagesList[self.imagePos][1],self.imagesList[self.imagePos][0])
        if(len(self.imagesList) == 1):
            self.imagesList=[]
            writeFile(self.viewDirectory+self.cfg.resDiffFile,json.dumps(self.imagesList))
            sys.exit()
        self.imagesList = self.imagesList[:self.imagePos] + self.imagesList[self.imagePos+1 :]
        self.imagePos = self.imagePos - 1
        if self.imagePos == -1:
            self.imagePos = 0
        self.loadImage(self.imagesList[self.imagePos])
        writeFile(self.viewDirectory+self.cfg.resDiffFile,json.dumps(self.imagesList))

    @QtCore.pyqtSlot()
    def nextImage(self):
        if self.imagePos == len(self.imagesList) - 1:
            self.imagePos = 0
        else:
            self.imagePos = self.imagePos + 1
        self.loadImage(self.imagesList[self.imagePos])

    @QtCore.pyqtSlot()
    def prevImage(self):
        if self.imagePos == 0:
            self.imagePos = len(self.imagesList) - 1
        else:
            self.imagePos = self.imagePos - 1
        self.loadImage(self.imagesList[self.imagePos])

    def loadImageOld(self,path):
        self.pixmapLeft = QtGui.QPixmap(path[0])
        self.pixmapRight = QtGui.QPixmap(path[1])

        self.leftImage.setPixmap(self.pixmapLeft)
        self.rightImage.setPixmap(self.pixmapRight)

        self.calcPositions()

        self.rightImage.setPixmap(self.pixmapRight.scaled(
            self.rightImage.width(), self.rightImage.height(),
            QtCore.Qt.KeepAspectRatio,QtCore.Qt.SmoothTransformation))
        self.leftImage.setPixmap(self.pixmapLeft.scaled(
            self.leftImage.width(), self.leftImage.height(),
            QtCore.Qt.KeepAspectRatio,QtCore.Qt.SmoothTransformation))

    def loadImage(self,path):
        # read all images
        referenceImage = imread(path[0])
        comparisonImage = imread(path[1])

        # flatten the diff map to reduce matrix complexity
        diffImage = imread(path[2],flatten=True)

        # get all coordinates that are not zero
        nonzeroCoords = np.nonzero(diffImage)

        # transform to 2 component vectors
        nonzeroCoords = np.column_stack((nonzeroCoords[0],nonzeroCoords[1]))

        # create image which can be used for drawing
        i = Image.fromarray(comparisonImage)
        draw = ImageDraw.Draw(i)

        # use k-means for the first iteration
        result = kmeans(nonzeroCoords.astype(float),1)
        n = 0

        timeout = time.time() + 3
        # iterate k-means until the distortion is lower than 50
        while(result[1] > 15):
            n = n + 1
            result = kmeans(nonzeroCoords.astype(float),n)

            #not more than 10 k-means or 3 seconds
            if n > 10 or time.time() > timeout:
                break
        width = int(result[1])+10
        # draw boxes around all pixel groups
        for x, y in result[0]:
            x = x.astype(np.int64)
            y = y.astype(np.int64)
            coords = (y-width, x-width, y+width, x+width)
            draw.rectangle((coords), fill=None, outline="red")

        # convert nparray to image
        comparisonImage = np.asarray(i)

        # convert image to qimage
        self.pixmapLeft = QtGui.QPixmap.fromImage(toQImage(referenceImage))
        self.pixmapRight = QtGui.QPixmap.fromImage(toQImage(comparisonImage))

        # show image in labels
        self.leftImage.setPixmap(self.pixmapLeft)
        self.rightImage.setPixmap(self.pixmapRight)

        self.calcPositions()

        self.rightImage.setPixmap(self.pixmapRight.scaled(
            self.rightImage.width(), self.rightImage.height(),
            QtCore.Qt.KeepAspectRatio,QtCore.Qt.SmoothTransformation))
        self.leftImage.setPixmap(self.pixmapLeft.scaled(
            self.leftImage.width(), self.leftImage.height(),
            QtCore.Qt.KeepAspectRatio,QtCore.Qt.SmoothTransformation))

        md5 = self.imagesList[self.imagePos][1].split("/")[-2]
        parameters = ""
        for item in self.depHashes[md5]:
            parameters = parameters + item +": "+ self.depHashes[md5][item].upper()+", "
        self.statusText.setText("Page "+str(self.imagePos+1)+"/"+str(len(self.imagesList))+" | "+self.imagesList[self.imagePos][1]+"\nParameters: "+parameters)
        self.setWindowTitle("dapscompare - "+self.imagesList[self.imagePos][1])

    # calculate positions of elements in window
    def calcPositions(self):
        width = self.width()
        height = self.height()
        self.leftImage.move(0,0)
        self.leftImage.resize(width/2,height-70)
        self.rightImage.move(int(width/2)+1,0)
        self.rightImage.resize(width/2,height-70)
        self.btnNext.move(width - 120, height - 50)
        self.btnPrev.move(width - 240, height - 50)
        self.btnMakeRef.move(width - 400, height - 50)
        self.statusText.move(20, height - 50)
        self.statusText.setFixedWidth(width - 450)

    # refresh positions in window when resizing
    def resizeEvent(self,resizeEvent):
        self.calcPositions()

    # fixed image width and height when resizing
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
