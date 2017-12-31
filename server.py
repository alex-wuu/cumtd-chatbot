from flask import Flask, request
from flask.views import MethodView

import os
import redis
import responder

app = Flask(__name__)

PAGE_ACCESS_TOKEN = os.getenv('PAGE_ACCESS_TOKEN')
VERIFICATION_TOKEN = os.getenv('VERIFICATION_TOKEN')
CUMTD_KEY = os.getenv('CUMTD_KEY')
BASE_URL = os.getenv('BASE_URL')
REDIS_URL = os.getenv('REDIS_URL')


def check_redis(stop_id, stop_name):
	'''Update redis for a stop_id if last update was more than a minute ago, then returns message_text to send'''
	print('Checking redis for {0}: {1}'.format(stop_id, stop_name))
	r = redis.from_url(REDIS_URL)
	cur_time = responder.get_cur_time()
	if r.exists(stop_id):
		if cur_time != r.lindex(stop_id, 0):
			departures = responder.get_departures(CUMTD_KEY, BASE_URL, stop_id)
			message_text = departures if type(departures) == str else responder.departures_text(stop_name, departures)
			r.lset(stop_id, 0, cur_time)
			r.lset(stop_id, 1, message_text)
		else:
			message_text = r.lindex(stop_id, 1)
	else:
		departures = responder.get_departures(CUMTD_KEY, BASE_URL, stop_id)
		message_text = departures if type(departures) == str else responder.departures_text(stop_name, departures)
		r.lpush(stop_id, message_text)
		r.lpush(stop_id, cur_time)
	return message_text


class handlerAPI(MethodView):

	def get(self):
		'''Checks the verification token from the Facebook Graph API to identify the webhook'''
		print('Handling Facebook verification')
		if request.args.get('hub.mode') == 'subscribe' and request.args.get('hub.verify_token') == VERIFICATION_TOKEN:
			print('Verification successful!')
			return request.args.get('hub.challenge', default=''), 200
		else:
			return 'Verification failed; wrong verification token.', 403

	def post(self):
		'''Handles messages from sender'''
		print('Handling messages')
		payload = request.get_json()
		print(payload)
		# Find the message text with sender and recipient IDs, and respond to each
		if payload['object'] != 'page':
			return 'ok', 200
		for entry in payload['entry']:
			for messaging_event in entry['messaging']:
				try:
					sender_id = messaging_event['sender']['id']
					stop_id, stop_name = responder.get_stop_id(CUMTD_KEY, BASE_URL, messaging_event['message']['text'])
					if stop_id != '':
						message_text = check_redis(stop_id, stop_name)
					else:
						message_text = stop_name
					print(message_text)
					responder.message_response(PAGE_ACCESS_TOKEN, sender_id, message_text)
				except IndexError:
					pass
		return 'ok', 200


app.add_url_rule('/', view_func=handlerAPI.as_view('handler_api'))

if __name__ == '__main__':
	app.run()
