import sys
import json
import datetime
from dateutil import parser
import tornado.websocket
from tornado import gen

from integrations.slack import slack
from integrations.teamwork import teamwork

def slack_ws_finished(conn):
	print('slack_ws_finished', conn)

@gen.coroutine
def slack_today(slack_id, config):
	print('slack_today', config)
	tw = teamwork.Teamwork(config['tw']['account-name'], config['tw']['token'])

	now = datetime.datetime.now()
	today = tw.calendarevents(startdate=now, enddate=now)

	tw_id = None
	found = False
	for name, mapping in config['id-map'].items():
		if mapping['slack'] == slack_id:
			found = True
			try:
				tw_id = mapping['tw']
			except:
				return "Sorry {}, your don't have a Teamwork account id".format(name)

	if not found:
		return "Sorry, can't figure out who you are!"

	message = "Hi {}, these are your events for today:\n".format(name)

	for event in today['events']:
		print(event)
		if tw_id in event['notify-user-ids'] or (tw_id in event['attending-user-ids']):
			start = parser.parse(event['start'])
			end = parser.parse(event['end'])
			title = event['title']
			url = 'https://csag.teamworkpm.net/calendar'
			message += "*{}:* {} {}\n".format(start.strftime("%-I:%M %p"), title, url)

	return message



@gen.coroutine
def slack_ws_connect(url, config, channel):
	print('slack_ws_connect', config, channel)

	conn = yield tornado.websocket.websocket_connect(ws_url)
	print(conn)

	id = 0
	while True:
		msg = yield conn.read_message()

		if msg:
			message = json.loads(msg)
			print(message)

			if "type" in message and message["type"] == "message":

				# Find a mention
				pos = message['text'].find('<@U1C659QG3>')
				if pos >= 0:
					cmd = message['text'][pos+13:].split()[0]
				else:
					cmd = message['text'][:5]

				print('cmd', pos,cmd)
				if cmd == 'today':
					text = yield slack_today(message['user'], config)
				else:
					text = "Not sure what you mean by: {}".format(message["text"])


				message = {"id":id, "type":"message", "channel":channel, "text":text}
				conn.write_message(json.dumps(message))

		id += 1
	


if __name__ == '__main__':

	config = json.loads(open(sys.argv[1]).read())
	print('setting up slack team config')
	s = slack.Slack(config['slack']['token'])

	print('getting slack IM channel')
	im = s.open_im('U04QRTZ3X')
	channel = im['channel']['id']
	print('got channel {}'.format(channel))

	print('starting RTM session')
	response = s.rtm_start()

	ws_url = response['url']
	print('opening WS url {}'.format(ws_url))

	io_loop = tornado.ioloop.IOLoop.current()
	io_loop.spawn_callback(slack_ws_connect, ws_url, config, channel)
	io_loop.start()


				
