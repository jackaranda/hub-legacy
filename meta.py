
from collections import OrderedDict

from pymongo import MongoClient
from bson.objectid import ObjectId

import json

class ValueException(Exception):

	def __init__(self, error):
		self.error = error

	def __str__(self):
		return "<ValueException: {}>".format(self.error)



class Property(object):
	"""
	Base Property class.  This class should never be used except to derive other sub classes
	"""
	pass

	def __init__(self):
		self.default = None

	def add_to_model(self, model, name):
		#print("add_to_model", model, name)
		self.model = model
		self.name = name

	def validate(self, value):
		return True, ""


class StringProperty(Property):

	def __init__(self, maxlength=None, default=None):
		self.maxlength = maxlength
		self.default = default


	def validate(self, value):

		valid, error = super(StringProperty, self).validate(value)

		if not valid:
			return valid, error

		elif not isinstance(value, str):
			return False, "{}.{}: {} should be a str".format(self.model.__class__.__name__, self.name, value)

		else:
			return True, ""

class IntegerProperty(Property):

	def __init__(self, default=None):
		self.min = min
		self.max = max
		self.default = default

	def validate(self, value):

		valid, error = super(IntegerProperty, self).validate(value)
		
		if not valid:
			return False, error 
		elif not isinstance(value, int):
			return False, "{} is not a valid IntegerProperty value".format(str(value))
		else:
			return True, ""


class BoundedIntegerProperty(IntegerProperty):

	def __init__(self, min, max, default=None):
		self.min = min
		self.max = max
		self.default = default

	def validate(self, value):

		valid, error = super(IntegerProperty, self).validate(value)
		
		if not valid:
			return False, error
		elif value < self.min or value > self.max:
			return False, "{}.{}: {} should be >= {} and <= {}".format(self.model.__class__.__name__, self.name, value, self.min, self.max)
		else:
			return True, ""


class ModelProperties(object):

	def __init__(self):
		self.properties = OrderedDict()

	def add_property(self, name, prop):
		self.properties[name] = prop


class ModelMeta(type):

	def __new__(cls, clsname, bases, namespace):
		#print(cls, clsname, bases, namespace)

		newnamespace = OrderedDict(_meta=ModelProperties())
		newnamespace['_storage'] = None

		for name, thing in namespace.items():
			
			if name == '_storage':
				newnamespace['_storage'] = thing

			elif isinstance(thing, Property):
				#print("Adding {} called {} to _meta properties".format(type(thing), name))
				newnamespace[name] = thing.default
				newnamespace['_meta'].add_property(name, thing)

			else:
				newnamespace[name] = thing


		result = super(ModelMeta, cls).__new__(cls, clsname, bases, newnamespace)
		return result


class MongoStorage(object):

	def __init__(self, dbname, host='localhost', port=27017):

		self.host = host
		self.port = port
		self.client = MongoClient(host, port)
		self.db = self.client[dbname]
		
	def add_to_model(self, model):
		self.model = model

	def insert(self, data):
		print("insert", data)
		collection = self.db[self.model.__name__]
		return collection.insert(data)

	def find(self, query):
		print("query", query)
		collection = self.db[self.model.__name__]
		return list(collection.find(query))


class Model(metaclass=ModelMeta):

	def __init__(self, **kwargs):

		for name, prop in self._meta.properties.items():
			prop.add_to_model(self, name)

		for name, value in kwargs.items():
			self.__setattr__(name, value)


	def __setattr__(self, name, value):

		if name in self._meta.properties:

			valid, error = self._meta.properties[name].validate(value)
			
			if valid:
				super(Model, self).__setattr__(name, value)
			else:
				raise ValueException(error)


	def __getattribute__(self, name):

		meta = super(Model, self).__getattribute__('_meta')
		
		if name in meta.properties:
			#print("Getting value of a {} called {}".format(meta.properties[name], name))
			return super(Model, self).__getattribute__(name)
		
		else:
			return super(Model, self).__getattribute__(name)


	def as_dict(self):

		result = OrderedDict()

		for name, prop in self._meta.properties.items():
			result[name] = getattr(self, name, prop.default)

		return result

	def as_json(self):
		return json.dumps(self.as_dict())

	@classmethod
	def add_storage(cls, storage):
		cls._storage = storage
		storage.add_to_model(cls)
		return cls

	def save(self):
		print('save', self._storage, self.as_json())
		self._storage.insert(self.as_dict())

	@classmethod
	def find(cls, query):
		print('find', cls._storage, query)
		return cls._storage.find(query)


	@classmethod
	def make(cls, name, properties, storage=None):
		return type(name, (Model,), properties)


if __name__ == "__main__":

	props = OrderedDict([('name',StringProperty(default='CJ')), ('age',BoundedIntegerProperty(0,120))])
	MyModel = Model.make('MyModel', props).add_storage(MongoStorage('meta'))

	p1 = MyModel(name='Jack', age=39)
	p2 = MyModel(name='Chris', age=42)
	p3 = AnotherModel(age=19)

	print(p1.name, p2.name, p3.name)
	print(p1.age, p2.age, p3.age)

	print(p1.name, p2.name, p3.name)
	print(p1.age, p2.age, p3.age)

	print(p1.as_json())

	p1.save()
	p2.save()
	p3.save()

	print(MyModel.find({'name':'Chris'}))
