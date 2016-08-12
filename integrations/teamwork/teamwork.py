import requests
from requests.auth import HTTPBasicAuth
import datetime

class Teamwork:

	def __init__(self, account, token):

		self.token = token
		self.base_url = 'https://{}.teamworkpm.net/'.format(account)


	def query(self, method, objectid=None, extra_params=None):

		print method, objectid, extra_params

		if objectid:
			objectid = str(objectid)
			url = "{}{}/{}.json".format(self.base_url, method, objectid)
		else:
			url = "{}{}.json".format(self.base_url, method)

		params = {}

		if extra_params:
			for key,value in extra_params.items():
				params[key] = value

		print url, params
		r = requests.get(url, params=params, auth=HTTPBasicAuth(self.token, 'xyz'))
		
		return r.json()

	def calendarevents(self, startdate=None, enddate=None):
		params = {'startdate':startdate.strftime("%Y%m%d"), 'enddate':enddate.strftime("%Y%m%d")}
		return self.query('calendarevents', extra_params=params)

	def calendarevent(self, id):
		return self.query('events', objectid=id)


