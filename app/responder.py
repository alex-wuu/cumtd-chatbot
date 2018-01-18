import ast
import iso8601
import json
import random
import re
import requests


def check_custom_stop(custom_stops, received_text):
    """Check for defined custom stops based on received text"""
    d = ast.literal_eval(custom_stops)
    for word in received_text.split():
        if word in d:
            return d[word]
    return ''


def check_text(received_text):
    """Check the received text for bad things"""
    return re.sub(r'\W+', ' ', received_text)


def departures_text(stop_name, departures):
    """Create message text containing bus departure times for a stop"""
    print('Creating message with bus departures')
    cur_time = iso8601.parse_date(departures['time'])
    message_text = '{0} departures at {1}\n'.format(stop_name, cur_time.strftime('%I:%M %p'))
    message_text += 'Data provided by CUMTD\n'  # needed for CUMTD TOS
    if len(departures['departures']) == 0:
        message_text += '\nNo buses are currently scheduled :('
    for bus_time in departures['departures']:
        message_text += '\n{0} in {1} min'.format(bus_time['headsign'], bus_time['expected_mins'])
    return message_text


def entity_response(nlp_entity):
    """Create message text for greetings, thanks and bye NLP entities"""
    message_text = ''
    bus_emoji = b' \\U0001f68c'.decode('unicode-escape')
    if nlp_entity == 'greetings':
        message_text = random.choice(['Hi there!', 'Hi!', 'Hello!'])
    elif nlp_entity == 'thanks':
        message_text = random.choice(['No problem!', "You're welcome!"])
    elif nlp_entity == 'bye':
        message_text = random.choice(['Goodbye!', 'Have a good day!'])
    return message_text + random.choice([bus_emoji, ''])


def get_departures(key, base_url, stop_id):
    """Get json of departures by stop_id"""
    print('Finding departures for bus stop')
    params = {
        "key": key,
        "stop_id": stop_id
    }
    r = requests.get(base_url + '/getdeparturesbystop', params=params)
    if r.status_code == 200:
        return r.json()
    else:
        return "Can't get bus departures: Error {0}".format(r.status_code)


def get_entity(nlp_entities):
    """Return max confidence NLP entity over 0.6"""
    max_entity = ''
    max_confidence = 0
    for entity in nlp_entities:
        confidence = nlp_entities[entity][0]['confidence']
        if entity in ['greetings', 'thanks', 'bye'] and confidence > 0.7 and confidence > max_confidence:
            max_entity = entity
            max_confidence = confidence
    return max_entity


def get_nearby_stops(key, base_url, latitude, longitude):
    print('Finding nearby bus stops')
    params = {
        "key": key,
        "lat": latitude,
        "lon": longitude,
        "count": 5
    }
    r = requests.get(base_url + '/getstopsbylatlon', params=params)
    if r.status_code == 200:
        return r.json()
    else:
        return "Can't find nearby bus stops: Error {0}".format(r.status_code)


def get_started():
    """Create message when user clicks the get started button"""
    message_text = ("Hi there! I can show you bus departures in the Champaign-"
                    "Urbana area.\n\nJust send me a bus stop that you'd like to "
                    "check! E.g. \"transit plaza\" or \"illini union\"\n\nType "
                    "\"help\" to see this example and other commands.")
    return message_text


def get_stop_id(key, base_url, received_text):
    """Search based on received text, then returns the stop_id and stop_name of closest match"""
    print('Finding bus stops for {0}'.format(received_text))
    params = {
        "key": key,
        "query": received_text
    }
    r = requests.get(base_url + '/getstopsbysearch', params=params)
    if r.status_code == 200:
        match_ids = r.json()
        try:
            stop_id = match_ids['stops'][0]['stop_id']
            stop_name = match_ids['stops'][0]['stop_name']
            return stop_id, stop_name
        except IndexError:
            return '', "Can't find a matching bus stop :("
    else:
        return '', "Can't find bus stops: Error {0}".format(r.status_code)


def get_help():
    """Return help text when user types help"""
    message_text = ("Bus stop departures and nearby stops are currently supported.\n\n"
                    "Type a bus stop e.g. \"transit plaza\" or "
                    "\"illini union\"\n\n"
                    "Ask for nearby bus stops e.g. \"stops near me\" or \"close bus stops\"")
    # Add feedback line
    return message_text


def nearby_stops_text(nearby_stops):
    print('Creating message with nearby stops')
    message_text = 'Nearby bus stops:\n'
    for stop in nearby_stops['stops']:
        distance = round(stop['distance'], 2)
        distance_text = str(distance) + ' ft' if distance < 1000 else str(round(distance / 5280, 2)) + ' mi'
        message_text += '\n{0}: {1}'.format(stop['stop_name'], distance_text)
    return message_text


def send_action(token, fb_url, recipient_id, action):
    """Display sender action for the user"""
    params = {
        "access_token": token
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "sender_action": action
    })
    r = requests.post(fb_url, params=params, headers=headers, data=data)
    if r.status_code != 200:
        print(r.status_code)
        print(r.text)


def send_location_button(token, fb_url, recipient_id):
    """Ask the user for their location"""
    params = {
        "access_token": token
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": "Please share your location",
            "quick_replies": [
                {
                    "content_type": "location"
                }
            ]
        }
    })
    r = requests.post(fb_url, params=params, headers=headers, data=data)
    if r.status_code != 200:
        print(r.status_code)
        print(r.text)


def send_text(token, fb_url, recipient_id, message_text):
    """Send message back to the original sender"""
    params = {
        "access_token": token
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "messaging_type": "RESPONSE",
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    })
    r = requests.post(fb_url, params=params, headers=headers, data=data)
    if r.status_code != 200:
        print(r.status_code)
        print(r.text)
