from flask import Flask
from flask import request

import requests
from requests.auth import HTTPBasicAuth

import slack

app = Flask(__name__)


@app.route('/teamwork/reminder', methods=['GET', 'POST'])
def teamwork_calendarevent():
	
	app.logger.debug(repr(request.form))

	objectID = request.form['objectId']

	url = 'https://csag.teamworkpm.net/calendarevents/{}.json'.format(objectID)
	app.logger.debug(url)

	event = requests.get(url, auth=HTTPBasicAuth('drama980judah', 'xyz')).json()
	app.logger.debug(repr(event))

	channel = s.open_im('U04QRTZ3X')['channel']['id']
	app.logger.debug(repr(channel))

	s.post(channel, event['event']['description'])

	return repr(event)

@app.route('/slack/slash', methods=['GET', 'POST'])
def slack_slash():
	app.logger.debug(request.form)

	return "thanks"


if __name__ == '__main__':
	app.run(host='0.0.0.0', debug=True)