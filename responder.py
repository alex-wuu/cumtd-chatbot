import iso8601
import json
import requests


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


def get_stop_id(key, base_url, received_text):
    """Search based on received text, then returns the stop_id and stop_name of closest match"""
    print('Finding bus stops')
    stop_id_url = base_url + '/{0}?key={1}&query={2}&count={3}'.format('getstopsbysearch', key, received_text, 3)
    r = requests.get(stop_id_url)
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


def get_departures(key, base_url, stop_id):
    """Get json of departures by stop_id"""
    print('Finding departures for bus stop')
    departures_url = base_url + '/{0}?key={1}&stop_id={2}'.format('getdeparturesbystop', key, stop_id)
    r = requests.get(departures_url)
    if r.status_code == 200:
        return r.json()
    else:
        return "Can't get bus departures: Error {0}".format(r.status_code)


def send_response(token, fb_url, recipient_id, message_text):
    """Send message back to the original sender"""
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
            "text": message_text
        }
    })
    r = requests.post(fb_url, params=params, headers=headers, data=data)
    if r.status_code != 200:
        print(r.status_code)
        print(r.text)
