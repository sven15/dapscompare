from subprocess import check_output, Popen, PIPE
import os

class renderPDF:
	def __init__(self,pathPdf,pageWidth,pathTarget = False):
		# convert all PDF pages into numbered images and place them in reference or comparison folder
		somestring = "/usr/bin/convert -density 110 "+pathPdf+" -quality 100 -background white -alpha remove "+pathTarget+"/page-%03d.png"
		my_env = os.environ.copy()
		self.process = Popen([somestring], env=my_env, shell=True, stdout=PIPE, stderr=PIPE)
		self.process.wait()

	def pdfToPngs(pathPdf, pathPngDir):
		all_pages = Image(filename=pathPdf , resolution=100)        # PDF will have several pages.
		for x, page in enumerate(all_pages.sequence):    # Just work on first page
			with Image(page) as i:
				i.format = 'png'
				i.background_color = Color('white')
				i.alpha_channel = 'remove'
				#i.alpha_channel = False
				#i.save(filename=pathPngDir+'/page-%s.png' % x)
				i.save(filename=pathPngDir+'/page-%03d.png')
