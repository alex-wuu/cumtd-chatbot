import json
import requests

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

# def get_buses(key, message_text):
# 	'''Get buses by stop'''
# 	base_url = 'https://developer.cumtd.com/api/{0}/{1}'.format('v2.2', 'json')
# 	stop_id_url = (base_url + '/{0}?key={1}?query={2}').format('getstopsbysearch', key, message_text)
# 	r = requests.get(stop_id_url)
# 	if r.status_code == 200:
# 		all_ids = r.json()
# 		stop_id = 
# 	else:
# 		return 'Bus stop cannot be found! Error {}'.format(r.status_code)
# 	departures_url = (base_url + '/{0}?key={1}?stop_id={2}').format('getdeparturesbystop', key, stop_id)
