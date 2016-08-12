from teamwork import Teamwork
from slack import Slack
from dateutil import parser
import json
import sys
import datetime

config = json.loads(open(sys.argv[1]).read())

idmap = {'34144':'U04QRTZ3X'}

tw = Teamwork(config['tw']['account-name'], config['tw']['token'])
s = Slack(config['slack']['token'])

now = datetime.datetime.now()
today = tw.calendarevents(startdate=now, enddate=now)

for twid, sid in idmap.items():

	message = "*Your meetings for today*\n"
	for event in today['events']:

		print
		print event	
		print

		if twid in event['notify-user-ids'] or (twid in event['attending-user-ids']):
			#for key, value in event.items():
			#	print key, value
			#print 

			start = parser.parse(event['start'])
			end = parser.parse(event['end'])
			title = event['title']
			url = 'https://csag.teamworkpm.net/calendar'
			message += "*{}:* {} {}\n".format(start.strftime("%-I:%M %p"), title, url)


	im = s.open_im(sid)
	print im
	print message
	channel = im['channel']['id']
	print s.post(channel, message)

