import tornado.ioloop
import tornado.web
import tornado.gen
import os.path
import json

from model import *
from backends import MongoBackend

class RESTHandler(tornado.web.RequestHandler):
	
	def initialize(self, model):
		self.model = model

	@tornado.gen.coroutine
	def get(self, path):

		print("get", path)

		if path == "":
			items = self.model.find()

			result = "<ul>"

			for item in items:
				print item
				result += "<li>{}: {} {}</li>".format(item.__id__, item.name.value, item.familyName.value)

			result += "</ul>"
		
		else:
			item = self.model.find_one({'__id__':path})
			result = item.name.value

		self.write("RESTHandler for {}, path = {}, result = {}".format(model.__name__, path, result))



if __name__ == "__main__":

	handlers = []

	schema = Schema('hub')

	with open('schema/person.json') as f:
		Person = Model.make(schema, **json.loads(f.read()))
		Person.add_backend(MongoBackend())

	with open('schema/article.json') as f:
		Article = Model.make(schema, **json.loads(f.read()))
		Person.add_backend(MongoBackend())

	for name, model in schema.models.items():
		handlers.append((r"/api/{}/(.*)".format(model.__name__.lower()), RESTHandler, {'model':model}))

	print handlers

	people = Person.find()
	print people

	app = tornado.web.Application(handlers, autoreload=True)

	app.listen(port=8080, address='0.0.0.0')
	tornado.ioloop.IOLoop.current().start()