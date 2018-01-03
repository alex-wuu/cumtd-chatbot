from flask import Flask, request
from flask.views import MethodView

import os
import botredis
import responder

app = Flask(__name__)

PAGE_ACCESS_TOKEN = os.getenv('PAGE_ACCESS_TOKEN')
VERIFICATION_TOKEN = os.getenv('VERIFICATION_TOKEN')
CUMTD_KEY = os.getenv('CUMTD_KEY')
FB_URL = os.getenv('FB_URL')
BASE_URL = os.getenv('BASE_URL')
REDIS_URL = os.getenv('REDIS_URL')


def generate_response(messaging_event):
    """Return the user's ID and response text"""
    sender_id = messaging_event['sender']['id']
    try:
        if messaging_event['postback']['payload'] == 'get_started':
            return sender_id, responder.get_started()
    except KeyError:
        pass
    received_text = responder.check_text(messaging_event['message']['text'])
    nlp_entity = responder.get_entity(messaging_event['message']['nlp']['entities'])
    if 'help' in received_text:
        return sender_id, responder.get_help()
    elif nlp_entity != '':
        print('NLP entity found: {0}'.format(nlp_entity))
        return sender_id, responder.entity_response(nlp_entity)
    else:
        remaining_time = botredis.check_user(REDIS_URL, sender_id)
        if remaining_time == 0:
            stop_id, stop_name = responder.get_stop_id(CUMTD_KEY, BASE_URL, received_text)
            if stop_id != '':
                message_text = botredis.check_departures(REDIS_URL, stop_id)
            else:
                message_text = stop_name
        else:
            message_text = 'Request limit reached! Try again in {0} seconds.'.format(remaining_time)
        if message_text is False:
            departures = responder.get_departures(CUMTD_KEY, BASE_URL, stop_id)
            message_text = departures if type(departures) == str else responder.departures_text(stop_name, departures)
            botredis.update_departures(REDIS_URL, stop_id, message_text)
        return sender_id, message_text


class handlerAPI(MethodView):
    """Handles Facebook GET and POST requests"""

    def get(self):
        """Check the verification token from the Facebook Graph API to identify the webhook"""
        print('Handling Facebook verification')
        if request.args.get('hub.mode') == 'subscribe' and request.args.get('hub.verify_token') == VERIFICATION_TOKEN:
            print('Verification successful!')
            return request.args.get('hub.challenge', default=''), 200
        else:
            return 'Verification failed; wrong verification token.', 403

    def post(self):
        """Handle messages from sender"""
        print('Handling messages')
        payload = request.get_json()
        print(payload)
        # Find the messages then respond to each
        if payload['object'] != 'page':
            return 'ok', 200
        botredis.flush_redis(REDIS_URL)
        for entry in payload['entry']:
            for messaging_event in entry['messaging']:
                try:
                    sender_id, message_text = generate_response(messaging_event)
                    print(message_text)
                    responder.send_text(PAGE_ACCESS_TOKEN, FB_URL, sender_id, message_text)
                except KeyError:
                    pass
        return 'ok', 200


app.add_url_rule('/', view_func=handlerAPI.as_view('handler_api'))

if __name__ == '__main__':
    app.run()
