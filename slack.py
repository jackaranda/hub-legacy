import requests

class Slack:

	def __init__(self, token):

		self.token = token
		self.base_url = 'https://slack.com/api/'


	def query(self, method, extra_params=None):

		url = "{}{}".format(self.base_url, method)
		params = {'token':self.token}

		if extra_params:
			for key,value in extra_params.items():
				params[key] = value

		r = requests.get(url, params=params)
		
		return r.json()

	def users_list(self):
		return self.query('users.list')

	def channels_list(self):
		return self.query('channels.list')

	def channels_history(self, channel_id, count=100):
		return self.query('channels.history', {'channel':channel_id, 'count':count})
	
	def open_im(self, user):
		return self.query('im.open', {'user':user})

	def rtm_start(self):
		return self.query('rtm.start')

	def post(self, channel, text):
		return self.query('chat.postMessage', {'channel':channel, 'text':text})

