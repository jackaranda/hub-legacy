import slack
import sys
import json
import tornado.websocket
import websocket
import requests
from StringIO import StringIO
import grobid

config = json.loads(open(sys.argv[1]).read())

grobid = grobid.Grobid("http://localhost:10810")

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
		#print message

		if "type" in message and message["type"] == "message":

			if "subtype" in message and message["subtype"] == "file_share":
				filetype = message["file"]["filetype"]
				file_url = message["file"]["url_private_download"]
				file_id = message["file"]["id"]

				print message
				print filetype, file_url, file_id

				if filetype == 'pdf':

					r = requests.get(file_url, headers={'Authorization': 'Bearer {}'.format(config['slack']['token'])})
					meta = grobid.processHeaderDocument(StringIO(r.content))

					text = "*Title:* {}".format(meta["title"])
					message = {"id":id, "type":"message", "channel":channel, "text":text}
					ws.send(json.dumps(message))

			else:
				text = "You sent a message"
				message = {"id":id, "type":"message", "channel":channel, "text":text}
				ws.send(json.dumps(message))


				
