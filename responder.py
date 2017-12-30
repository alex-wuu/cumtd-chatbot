import json
import requests
import datetime
import iso8601

# CUMTD API base url
BASE_URL = 'https://developer.cumtd.com/api/{0}/{1}'.format('v2.2', 'json')

def message_response(token, recipient_id, message_text):
	'''Send message back to the sender'''
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
	r = requests.post('https://graph.facebook.com/v2.11/me/messages', params = params, headers = headers, data = data)
	if r.status_code != 200:
		print(r.status_code)
		print(r.text)

def departures_text(stop_name, departures):
	'''Create message text containing bus departure times for a stop'''
	print('Creating message with bus departures')
	cur_time = iso8601.parse_date(departures['time'])
	# Account for AM/PM, and CUMTD clock is 30 hours
	# if cur_time.datetime.hour >= 24:
	# 	cur_time.datetime.hour -= 24
	message_text = 'Bus departures for {0} at {1}:{2}'.format(stop_name, cur_time.hour, cur_time.minute)
	for bus_time in departures['departures']:
		message_text += '\n{0} in {1} min'.format(bus_time['head_sign'], bus_time['expected_mins'])
	return message_text

def get_stop_id(key, received_text):
	'''Get buses by stop then returns the id and name of closest match'''
	print('Finding bus stops')
	stop_id_url = BASE_URL + '/{0}?key={1}?query={2}?count={3}'.format('getstopsbysearch', key, received_text, 3)
	r = requests.get(stop_id_url)
	if r.status_code == 200:
		match_ids = r.json()
		print(match_ids)
		try:
			stop_id = match_ids['stops'][0]['stop_id']
			stop_name = match_ids['stops'][0]['stop_name']
			return stop_id, stop_name 
		except:
			return '', 'Can\'t find a matching bus stop :('
	else:
		return '', 'Can\'t find bus stop: Error {0}'.format(r.status_code)

def get_departures(key, stop_id):
	'''Get json of departures by stop_id'''
	print('Finding departures for bus stop')
	departures_url = BASE_URL + '/{0}?key={1}?stop_id={2}'.format('getdeparturesbystop', key, stop_id)
	r = requests.get(departures_url)
	if r.status_code == 200:
		return r.json()
	else:
		return 'Can\'t get bus departures: Error {0}'.format(r.status_code)