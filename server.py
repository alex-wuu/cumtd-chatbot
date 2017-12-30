from flask import Flask, request
from flask.views import MethodView

import os
import responder

app = Flask(__name__)

PAGE_ACCESS_TOKEN = os.getenv('PAGE_ACCESS_TOKEN')
VERIFICATION_TOKEN = os.getenv('VERIFICATION_TOKEN')
CUMTD_KEY = os.getenv('CUMTD_KEY')
BASE_URL = os.getenv('BASE_URL')

class handlerAPI(MethodView):

	def get(self):
		'''Checks the verification token from the Facebook Graph API to identify the webhook'''
		print('Handling Facebook verification.')
		if request.args.get('hub.mode') == 'subscribe' and request.args.get('hub.verify_token') == VERIFICATION_TOKEN:
			print('Verification successful!')
			return request.args.get('hub.challenge', default = ''), 200
		else:
			return 'Verification failed; wrong verification token.', 403

	def post(self):
		'''Handles messages from sender'''
		print('Handling messages.')
		payload = request.get_json()
		print(payload)
		# Find the message text with sender and recipient IDs, and respond to each
		if payload['object'] == 'page':
			for entry in payload['entry']:
				for messaging_event in entry['messaging']:
					try:
						sender_id = messaging_event['sender']['id']
						recipient_id = messaging_event['recipient']['id'] # not needed
						stop_id, stop_name = responder.get_stop_id(CUMTD_KEY, BASE_URL, messaging_event['message']['text'])
						if stop_id != '':
							print('{0}: {1}'.format(stop_id, stop_name))
							departures = responder.get_departures(CUMTD_KEY, BASE_URL, stop_id)
							message_text = responder.departures_text(stop_name, departures)
						else:
							message_text = stop_name
						print(message_text)
						responder.message_response(PAGE_ACCESS_TOKEN, sender_id, message_text)
					except:
						pass
		return 'ok', 200

app.add_url_rule('/', view_func = handlerAPI.as_view('handler_api'))

if __name__ == '__main__':
	app.run()