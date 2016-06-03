import slack
import sys
import json
import tornado.websocket
import websocket

config = json.loads(open(sys.argv[1]).read())


s = slack.Slack(config['slack']['token'])

im = s.open_im('U04QRTZ3X')
channel = im['channel']['id']

response = s.rtm_start()

ws_url = response['url']

ws = websocket.create_connection(ws_url)

id = 1
while True:
	message_string = ws.recv()
	if message_string != "":
		
		message = json.loads(message_string)
		print message

		if "type" in message and message["type"] == "message":
			response = {"id":id, "channel":channel, "type":"message", "text":"You said: {}".format(message["text"])}
			print response
			ws.send(json.dumps(response))
			id += 1
