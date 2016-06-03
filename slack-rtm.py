import slack
import sys
import json
import tornado.websocket

config = json.loads(open(sys.argv[1]).read())


s = slack.Slack(config['slack']['token'])

response = s.rtm_start()

ws_url = response['url']


