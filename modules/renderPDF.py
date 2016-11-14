from subprocess import check_output, Popen, PIPE
import os

class renderPDF:
	def __init__(self,pdfPath,pageWidth,pathTarget = False):
		# convert all PDF pages into numbered images and place them in reference or comparison folder
		somestring = "cd "+configSettings.directory+"/"+testcase+" && /usr/bin/convert -density 110 build/*/*.pdf -quality 100 -background white -alpha remove dapscompare-reference/pdf/page-%03d.png"
		
		self.process = Popen([somestring], env=my_env, shell=True, stdout=PIPE, stderr=PIPE)
		process.wait()
