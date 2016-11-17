from subprocess import check_output, Popen, PIPE
import os

class daps:
	def __init__(self, testcase, dapsParam, filetypes = ['pdf','html']):
		self.testcase = testcase
		self.filetypes = filetypes
		self.dapsParam = dapsParam
		
		self.createFolders()
		
		self.dcFiles = []
		
		self.findDcFiles()
		
		self.compileAllWait()
				
	def findDcFiles(self):
		for filename in os.listdir(self.testcase):
			if(filename[0:2] == "DC"):
				self.dcFiles.append(self.testcase+filename)
				
	def createFolders(self):
		# create dapscompare target folders
		for filetype in self.filetypes:
			for targetfolder in ['/dapscompare-comparison/','/dapscompare-reference/','/dapscompare-result/']:
				if not os.path.exists(self.testcase+targetfolder):
					os.makedirs(self.testcase+targetfolder)

	def compilePdf(self):
		my_env = os.environ.copy()
		for dcFile in self.dcFiles:
			self.procDaps = Popen(["cd "+self.testcase+" && /usr/bin/daps "+self.dapsParam+" -d "+dcFile+" pdf"], env=my_env, shell=True, stdout=PIPE, stderr=PIPE)
			self.procDaps.wait()
		
	def compileHtml(self):
		my_env = os.environ.copy()
		for dcFile in self.dcFiles:
			self.procHtml = Popen(["cd "+self.testcase+" && /usr/bin/daps "+self.dapsParam+" -d "+dcFile+" html"], env=my_env, shell=True, stdout=PIPE, stderr=PIPE)
			self.procHtml.wait()
		
	def compileEpub(self):
		my_env = os.environ.copy()
		self.procEpub = Popen(["cd "+self.testcase+" && /usr/bin/daps "+self.dapsParam+" -d "+dcFile+" epub"], env=my_env, shell=True, stdout=PIPE, stderr=PIPE)
		
	def compileAllWait(self):
		self.compilePdf()
		self.compileHtml()
