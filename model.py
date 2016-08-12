from urlparse import urlparse
from collections import OrderedDict
import sys

from backends import MongoBackend

class ValueException(Exception):

	def __init__(self, error):
		self.error = error

	def __str__(self):
		return "<ValueException: {}>".format(self.error)


class BaseField(object):
	"""
	Base properties class.  This calls should never be used except to derive other sub classes
	"""

	def __init__(self, **kwargs):
		
		self._value = None
		
		for key, value in kwargs:
			self.__setattr__(key, value)

		self.valid = True
		self.error = None
		self.warn = None

	@property
	def value(self):
		return self._value

	@value.setter
	def value(self, value):
		print "setting value of {} to {}".format(self, value)
		self._value = value
		self.validate()

		if not self.valid:
			raise ValueException(self.error)

	def validate(self):
		return self.valid, self.error, self.warn

#	def __str__(self):
#		if self.value:
#			return "<{}: {} >".format(self.__class__.__name__, self.value)
#		else:
#			return "<{}>".format(self.__class__.__name__)




class IntegerField(BaseField):
	"""
	An integer property class
	"""

	def __init__(self, minimum=None, maximum=None, default=0):

		super(IntegerField, self).__init__()
		self.minimum = minimum
		self.maximum = maximum
		self.default = default

	def validate(self):

		self.valid = True
		self.error = None
		self.warn = None

		if type(self.value) != int:
			self.error = "Value not an integer"
			self.valid = False

		elif self.minimum != None and self.value < self.minimum:
			self.error = "value {} smaller than minimum value {}".format(self.value, self.minimum)
			self.valid = False

		elif self.maximum  != None and self.value > self.maximum:
			self.error = "value {} greater than maximum value {}".format(self.value, self.maximum)
			self.valid = False

		return super(IntegerField, self).validate()


class StringField(BaseField):

	def __init__(self, maxlength=None, required=False):
		super(StringField, self).__init__()
		self.maxlength = maxlength

	def validate(self):
		if self.value and type(self.value) not in [str, unicode]:
			self.valid = False
			self.error = "Expected str or unicode value"
			self.value = None

		return super(StringField, self).validate()

class URLField(BaseField):

	def validate(self):
		if self.value != None:
			try:
				parts = urlparse(self.value)
			except:
				self.valid = False
			else:
				if not (parts[0] and parts[1]):
					self.valid = False

			if not self.valid:
				self.error = "'{}' is not a valid URL".format(self.value)

		return super(URLField, self).validate()


class EmailField(BaseField):

	def validate(self):
		if self.value != None:
			try:
				self.value.index('@')
			except:
				self.valid = False
				self.error = "'{}' is not a valid email address".format(self.value)

		return super(EmailField, self).validate()


class List(BaseField):

	def __init__(self, subtype, options={}, values=[], ref=False):
		"""
		>>> print List('String')
		<list of <class 'schema.String'>>
		"""
		self._values = values
		self.__subtype__ = subtype

		#print "Created list with subtype ", self.__subtype__

	def validate(self):
		return True, None, None

	def __getitem__(self, idx):
		return self._values[idx]

	def append(self, value):

		if type(value) != self.__subtype__:
			instance = self.__subtype__()
			instance.value = value
		else:
			instance = value
		
		self._values.append(instance)


	def __str__(self):
		return "<List ({}): {} >".format(self.__subtype__, str([str(item) for item in self._values]))


class Model(object):
	"""
	A model is a collection of properties.  Nested models are possible by assigning another model as a property
	"""

	# Initialise an instance of the model setting properties from the kwargs
	def __init__(self, **properties):

		self.__id__ = None

		for key, value in properties.items():
			try:
				prop = self.__getattribute__(key)
				prop.value = value
			except:
				self.__setattr__(key, value)

#		self.validate()

	@classmethod
	def add_backend(cls, backend):
		cls._backend = backend

	def save(self):
		if not self.__id__:
			self.__class__._backend.insert(self)
		else:
			self.__class__._backend.update(self)

	@classmethod
	def find(cls, query={}):
		return cls._backend.find(cls, query)

	@classmethod
	def find_one(cls, query={}):
		return cls._backend.find_one(cls, query)

	def validate(self):

		self.valid = True
		self.errors = []
		self.warnings = []
		
		for name in self.__names__:

			instance = self.__getattribute__(name)

			valid, error, warning = self.__getattribute__(name).validate()

			if not valid:
				self.errors.append(error)
				self.warnings.append(warning)
				self.valid = False

		return self.valid, self.errors, self.warnings

	def __setattr__(self, key, value):

		try:
			self.__getattribute__(key).value = value
		except:
			super(Model, self).__setattr__(key, value)

	def __getitem__(self, key):

		return self.__getattribute__(key)


	@classmethod
	def make(cls, schema, name=None, properties={}, description=None, store=None):
		
		class_props = OrderedDict()
		class_props['__description__'] = description
		class_props['__names__'] = []
		class_props['__schema__'] = schema

		print Model.__subclasses__()
		
		for key, config in properties.items():

			definition = config['type']

			if 'alias' in config:
				alias = config['alias']
			else:
				alias = None

			# Check for lists
			if type(definition) == list:
				islist = True
				definition = definition[0]
			else:
				islist = False

			if definition in [c.__name__ for c in BaseField.__subclasses__()]:
				prop = eval(definition)

			elif definition in schema.models.keys():
				prop = schema.models[definition]

			elif type(definition) == dict:
				prop = cls.make(schema, **definition)
			else:
				raise TypeError('{} not a valid type'.format(typestring))


			if 'options' in config:
				options = config['options']
			else:
				options = {}

			if islist:
				class_props[str(key)] = List(prop, options)
			else:
				class_props[str(key)] = prop(**options)

			if alias:
				class_props[alias] = class_props[str(key)]

			class_props['__names__'].append(key)
		

		model = type(str(name), (Model,), class_props)

		schema.add_model(model)

		print class_props
		return model
	

	def __str__(self):
		return "<Model {}: {}>".format(self.__class__.__name__, self.name)



class Schema(object):

	def __init__(self, name=None):

		self.name = name
		self.models = OrderedDict()

	def add_model(self, model):
		self.models[model.__name__] = model

	def __getitem__(self, name):
		return self.models[name]



if __name__ == "__main__":

	import json

	schema = Schema('hub')

	with open('schema/person.json') as f:
		Person = Model.make(schema, **json.loads(f.read()))
		Person.add_backend(MongoBackend())

	with open('schema/article.json') as f:
		Article = Model.make(schema, **json.loads(f.read()))


	print Person.name

	person1 = Person(name='Chris')
	print person1

	person2 = Person(name='Jack')
	print person1, person2