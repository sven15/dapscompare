import os
from subprocess import check_output, Popen, PIPE

def renderHtml(pathHtml,pageWidth,pathPng):
	# convert all PDF pages into numbered images and place them in reference or comparison folder
	head, tail = os.path.split(pathHtml)
	somestring = "/home/sven/SUSE/dapscompare/modules/html2png.py "+pathHtml+" "+pathPng+"/"+tail+".png "+str(pageWidth)
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
