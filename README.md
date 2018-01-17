# Champaign-Urbana Transit Chatbot

A facebook chatbot for use with the [CUMTD developer API](https://developer.cumtd.com/) built with [Flask](https://github.com/pallets/flask). Gives incoming bus departures for a given bus stop searched by the user.

## Setup
The provided procfile is used for deployment using Heroku. These instructions assume that you use Heroku for deployment and that a new app is already created for your bot through Heroku. Note that Heroku still requires you to enter a valid credit card to use their free Heroku redis addon.

### Requirements
- Python 3
- Redis or a Redis addon through your platform

### Installation Instructions
Clone the repository inside your current directory:
```
$ git clone https://github.com/alex-wuu/cumtd-chatbot.git cumtd-chatbot
$ cd cumtd-chatbot
```

Install virtualenv if you don't have it:
```
$ pip install virtualenv
```

Create your virtual environment with virtualenv if desired. `venv` can be changed to the virtual environment name of your choice:
```
$ virtualenv venv
```

Activate your virtual environment:
```
$ source venv/bin/activate
```

Install package dependencies with pip:
```
$ pip install -r app/requirements.txt
```

Add environment variables. This can be done through your platform, e.g. Heroku, or through an additional config file. If you use a config file, then it needs to be imported in `server.py`.
- ```PAGE_ACCESS_TOKEN``` is the page access token generated from your app's [Facebook developers page](https://developers.facebook.com/). See the [Deployment](#deployment) section for more information.
- ```VERIFICATION_TOKEN``` is the "Verify Token" entered when a webhook is set up through your app's Facebook developers page. See the [Deployment](#deployment) section for more information.
- ```CUMTD_KEY``` is your API key from [CUMTD](https://developer.cumtd.com/).
- ```FB_URL``` is used as a starting point for requests with the [Facebook graph API](https://developers.facebook.com/docs/messenger-platform/send-messages/), e.g. ```https://graph.facebook.com/v2.11/me/messages```.
- ```BASE_URL``` is used as a starting point for [requests with the CUMTD API](https://developer.cumtd.com/documentation/v2.2/requests/) with the format ```https://developer.cumtd.com/api/{version}/{format}/{method}?key={api_key}```.
- ```REDIS_URL``` is your Redis URL.
- ```CUSTOM_STOPS``` string containing user defined custom stops in a dictionary format. This is used to account for common bus stop acronyms/nicknames that aren't caught by the CUMTD API.

Set up your Redis. The Heroku redis addon was used for creating the app.

### Deployment
If you're using Heroku, then you can add a remote to the local repository with the following command and your app's name:
```
$ heroku git:remote -a YOUR_HEROKU_APP_NAME
```

Deploy the app with:
```
$ git subtree push --prefix app heroku master
```

Or if you move all the files from the app subdirectory to the root directory, then you can deploy this way:
```
$ git add .
$ git commit -m "Moved files from subdirectory root directory"
$ git push heroku master
```

Your bot's URL is shown as the "Web URL" from your Heroku app's info:
```
$ heroku apps:info
```

Create a new Facebook app for the chatbot through the [developers page](https://developers.facebook.com/). Click on the "My Apps" button and add a new app. Go to your new app's page, then click "Messenger" on the left side to get to the messenger platform. Add a webhook and set the callback URL to the chatbot's URL supplied by Heroku, and check the "messages" and "messaging_postbacks" boxes. The "Verify Token" you set corresponds to the ```VERIFICATION_TOKEN``` environment variable. Create a page for your bot so a "Page Access Token" can be generated, which corresponds to the ```PAGE_ACCESS_TOKEN``` environment variable. Enable NLP under the "Built-in NLP" section.

Take note of the Facebook graph API version, e.g. v2.11, you are using by going to "Webhooks" page on the left side.

Add a [Get Started button](https://developers.facebook.com/docs/messenger-platform/reference/messenger-profile-api/get-started-button) to your bot by [setting the get_started Messenger Profile property](https://developers.facebook.com/docs/messenger-platform/reference/messenger-profile-api#post). Your command will look like this:
```
curl -X POST -H "Content-Type: application/json" -d '{
  "get_started":{
    "payload":"get_started"
  },
  "greeting":[{
    "locale":"default",
    "text":"Gives bus stop departures in the Champaign-Urbana area. Data provided by CUMTD."
  }]
}' "https://graph.facebook.com/{version}/me/messenger_profile?access_token={PAGE_ACCESS_TOKEN}"
```

Go to the Facebook page you created for your chatbot and say hi or send a bus stop!
