import requests
import xml.etree.ElementTree as ET
import sys
import json


def print_tree(tree, path="", indent=0):

	for child in tree:
		print "{}{}".format(" "*indent*4, repr(child.tag))
		print "{}{}".format(" "*indent*4, repr(child.attrib))
		print "{}{}".format(" "*indent*4, repr(child.text))
		print_tree(child, indent=indent+1)
		print "{}END{}".format(" "*indent*4, repr(child))


class Grobid(object):

	def __init__(self, url):
		
		#url = "http://localhost:10810/processHeaderDocument"
		self.url = url
		self.tagmap = json.loads(open('grobid.tagmap').read())

		newmap = {}
		for key, entry in self.tagmap.items():
			xpath = entry['xpath']
			parts = xpath.split('/')
			newxpath = ""
			for part in parts:
				newxpath += "{}{}/".format("{http://www.tei-c.org/ns/1.0}", part)
			newmap[key] = {'source':entry['source'], "xpath":newxpath[:-1]}

		self.tagmap = newmap


	def processHeaderDocument(self, document):

		if isinstance(document, str):
			document = open(document)
		
		full_url = "{}/processHeaderDocument".format(self.url)

		files = {'input': document}

		r = requests.post(full_url, files=files)
#		print r.text
		tree = ET.fromstring(r.text)
#		print_tree(tree)
#		print r.text

		meta = {}


		for tag, params in self.tagmap.items():
			if 'xpath' in params:
				#print params['xpath']
				elements = tree.iterfind(params['xpath'])
				for element in elements:
					#print element.tag, element.attrib
					if params["source"] == "text":
						#print element.text
						meta['title'] = element.text

		return meta

#		nodes = tree.iter()
		
#		for node in nodes:
#			print node
#			print node.tag
#			print node.attrib
#			print node.text
#			print

if __name__ == "__main__":

	grobid = Grobid("http://localhost:10810")
	print grobid.tagmap
	meta = grobid.processHeaderDocument(sys.argv[1])
	print meta