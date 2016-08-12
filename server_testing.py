import tornado.ioloop
import tornado.web
import tornado.gen
import motor
import os.path

from jinja2 import Environment, BaseLoader, FileSystemLoader, TemplateNotFound

client = motor.motor_tornado.MotorClient()
db = client.hub

class MongoLoader(BaseLoader):
	"""
	Initial attempt to build an asyncronous Jinja2 template loader built on 
	tornado-motor
	"""

	def __init__(self, db):
		self.db = db

	def get_source(self, environment, template):

		try:
			source = yield db.templates.find_one({'name':template})
		except:
			raise TemplateNotFound(template)


		print source
		raise tornado.gen.Return(('template', None, True,))
		#return 'test', 'test', True


#env = Environment(loader=MongoLoader(db))
env = Environment(loader=FileSystemLoader('templates'))

def hub_filter(value, *args, **kwargs):
	return "{} (args={} kwargs={})".format(value, repr(args), repr(kwargs))

#env.add_filter('hub') = hub_filter

class StaticHandler(tornado.web.RequestHandler):

	def get(self, path):

		fullpath = "./static/{}".format(path)
		base, ext = os.path.splitext(fullpath)

		if ext == '.css':
			self.set_header('Content-Type', 'text/css')

		self.write(open(fullpath).read())


class MainHandler(tornado.web.RequestHandler):
	
	@tornado.gen.coroutine
	def get(self, path):
		
		print path		
		db = self.settings['db']
		
		pathitem = yield db.paths.find_one({'path':path})
		print pathitem

		if not pathitem:
			self.set_status(404, 'Error, path item matching {} not found!'.format(path))
			self.finish()

		else:
			
			template = env.get_template(pathitem['template']+".html")

			if 'type' in pathitem and pathitem['type'] == 'list':
				result = yield db[pathitem['collection']].find(pathitem['query']).to_list(None)
				print result
				self.write(template.render(items=result))

			else:
				result = yield db[pathitem['collection']].find_one(pathitem['query'])
				self.write(template.render(result))



	@tornado.gen.coroutine
	def put(self, path):

		db = self.settings['db']

		pathitem = yield db.paths.find_one({'path':path})
		
		if not pathitem:
			self.set_status(404, 'Error, path item matching {} not found!'.format(path))
			self.finish()
		
		else:
			item = yield db[pathitem['collection']].find_one(pathitem['query'])
			schema = yield db.schema.find_one({'name':item['type']})

			updated = {}
			for field in item.keys():
				data = self.get_argument(field, default=None)
				if data:
					updated[field] = data

			print updated
			yield db[pathitem['collection']].update(pathitem['query'], {'$set':updated})

			self.set_status(200)
			self.finish()


def make_app():
	return tornado.web.Application([
		(r"/static/(.*)", StaticHandler),
		(r"/(.*)", MainHandler),
	], 
		autoreload=True, 
		db=db
	)



if __name__ == "__main__":
	app = make_app()
	app.listen(port=8080, address='0.0.0.0')
	tornado.ioloop.IOLoop.current().start()