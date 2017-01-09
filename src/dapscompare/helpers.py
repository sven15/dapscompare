# The MIT License (MIT)
# 
# Copyright (c) 2016, Sven Seeberg-Elverfeldt <sseebergelverfeldt@suse.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import os

def readFile(filePath):
	if(os.path.isfile(filePath)):
		f = open(filePath, 'r')
		content = f.read()
		f.close()
		return content
	else:
		return False

def writeFile(path,content):
	f = open(path,'w')
	f.write(content)
	f.close()

def modeToName(mode):
	if mode == 1:
		return "dapscompare-reference"
	if mode == 2:
		return "dapscompare-comparison"

def hashPath(path):
	import hashlib, os
	SHAhash = hashlib.sha1()
	if not os.path.exists (path):
		return False
	if os.path.isfile(path):
		readFileBlock(path,SHAhash)
	else:
		for root, dirs, files in os.walk(path):
			for names in files:
				filepath = os.path.join(root,names)
				readFileBlock(filepath,SHAhash)
	return SHAhash.hexdigest()

def readFileBlock(filepath,SHAhash):
	with open(filepath, 'rb') as f1:
		while True:
			buf = f1.read(4096)
			if not buf : break
			SHAhash.update(hashlib.sha1(buf).hexdigest())

def registerHash(params,dataCollection):
	import json, hashlib
	# create md5sum of hash
	hashstring = json.dumps(params, sort_keys=True)
	md5 = hashlib.md5(hashstring.encode('utf-8'))
	# add md5sum and string to config and save to file in the end
	dataCollection.lock.acquire()
	dataCollection.depHashes[md5.hexdigest()] = params
	dataCollection.lock.release()
	return md5.hexdigest()

def listFiles(folder):
	result = []
	for item in os.listdir(folder):
		if os.path.isfile(folder+item):
			result.append(item)
	return result
