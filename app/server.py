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
CUSTOM_STOPS = os.getenv('CUSTOM_STOPS')


def generate_response(messaging_event):

    """Return the user's ID and response text"""
    
    sender_id = messaging_event['sender']['id']

    # Try block to check if user pressed get_started
    try:
        if messaging_event['postback']['payload'] == 'get_started':
            return sender_id, responder.get_started()
    except KeyError:
        pass

    # Try block to check if user sent their location to find nearby stops
    try:
        lat = messaging_event['message']['attachments'][0]['payload']['coordinates']['lat']
        lon = messaging_event['message']['attachments'][0]['payload']['coordinates']['long']
        remaining_time = botredis.check_user(REDIS_URL, sender_id)
        if remaining_time == 0:
            nearby_stops = responder.get_nearby_stops(CUMTD_KEY, BASE_URL, lat, lon)
            message_text = responder.nearby_stops_text(nearby_stops)
        else:
            message_text = 'Request limit reached! Try again in {0} seconds.'.format(remaining_time)
        return sender_id, message_text
    except KeyError:
        pass

    received_text = responder.check_ordinal(
        responder.check_alphanumeric(
            messaging_event['message']['text']
        ).lower()
    )

    # Bot actions for showing that message was seen, and bot is typing the message
    responder.send_action(PAGE_ACCESS_TOKEN, FB_URL, sender_id, 'mark_seen')
    responder.send_action(PAGE_ACCESS_TOKEN, FB_URL, sender_id, 'typing_on')

    # Get NLP entities if confidence is high enough
    nlp_entity = responder.get_entity(messaging_event['message']['nlp']['entities'])

    # Check for custom stops
    custom_stop = responder.check_custom_stop(CUSTOM_STOPS, received_text)
    received_text = custom_stop if custom_stop != '' else received_text

    if any(x in received_text for x in ['near', 'close']):
        message_text = 'location_request'
    elif 'help' in received_text:
        message_text = responder.get_help()
    elif nlp_entity != '' and custom_stop == '':
        print('NLP entity found: {0}'.format(nlp_entity))
        message_text = responder.entity_response(nlp_entity)
    else:

        # Check number of user requests in the last minute
        remaining_time = botredis.check_user(REDIS_URL, sender_id)
        if remaining_time == 0:
            stop_id, stop_name = responder.get_stop_id(CUMTD_KEY, BASE_URL, received_text)
            if stop_id != '':
                message_text = botredis.check_departures(REDIS_URL, stop_id)
            else:
                message_text = stop_name  # stop_name contains the error message if a stop_id not found
        else:
            message_text = 'Request limit reached! Try again in {0} seconds.'.format(remaining_time)

        # message_text is False only if the redis needs to be updated for the requested stop_id
        if message_text is False:
            departures = responder.get_departures(CUMTD_KEY, BASE_URL, stop_id)
            message_text = departures if type(departures) == str else responder.departures_text(stop_name, departures)
            botredis.update_departures(REDIS_URL, stop_id, message_text)
    responder.send_action(PAGE_ACCESS_TOKEN, FB_URL, sender_id, 'typing_off')
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
                    if message_text != 'location_request':
                        print(message_text)
                        responder.send_text(PAGE_ACCESS_TOKEN, FB_URL, sender_id, message_text)
                    else:
                        responder.send_location_button(PAGE_ACCESS_TOKEN, FB_URL, sender_id)
                except KeyError:
                    pass
        return 'ok', 200


app.add_url_rule('/', view_func=handlerAPI.as_view('handler_api'))

if __name__ == '__main__':
    app.run()
