import datetime as dt
import json

import requests
from flask import Flask, jsonify, request

API_TOKEN = ""
RapidAPI_Key = ""

app = Flask(__name__)


def get_forecast(location: str):
    url_base_url = "https://forecast9.p.rapidapi.com/"
    url_api = "rapidapi/forecast/"
    url_endpoint = "summary/"
    url_location = "Kyiv/"

    if location:
        url_location = f"{location}/"

    url = f"{url_base_url}{url_api}{url_location}{url_endpoint}"

    headers = {
        "X-RapidAPI-Key": RapidAPI_Key,
        "X-RapidAPI-Host": "forecast9.p.rapidapi.com"
    }

    response = requests.request("GET", url, headers=headers)
    return json.loads(response.text)


class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv["message"] = self.message
        return rv


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route("/")
def home_page():
    return "<p><h2>Weather forecast by Maksym Polishchuk.</h2></p>"


@app.route(
    "/weather/api/v1/forecast",
    methods=["POST"],
)
def weather_endpoint():
    start_dt = dt.datetime.now()
    json_data = request.get_json()

    if json_data.get("token") is None:
        raise InvalidUsage("token is required", status_code=400)
        
    if json_data.get("location") is None:
        raise InvalidUsage("location is required", status_code=400)
        
    if json_data.get("requester_name") is None:
        raise InvalidUsage("requester_name is required", status_code=400)

    token = json_data.get("token")

    if token != API_TOKEN:
        raise InvalidUsage("wrong API token", status_code=403)

    response_weather = get_forecast(json_data.get("location"))
        
    requester_name = json_data.get("requester_name")

    end_dt = dt.datetime.now()

    result = {
        "event": {
            "event_start_datetime": start_dt.isoformat(),
            "event_finished_datetime": end_dt.isoformat(),
            "event_duration": str(end_dt - start_dt),
        },
        "requester_name": requester_name,
        "location": response_weather['location']['name'],
        "coordinates": {
            "latitude": response_weather['location']['coordinates']['latitude'],
            "longitude": response_weather['location']['coordinates']['longitude']
        }
    }
    
    count_forecast = -1
    
    if json_data.get("date"):
        count_forecast = get_number_date(json_data.get("date"), len(response_weather['forecast']['items']))
        
    if count_forecast >= 0:
        result['forecast'] = [get_dict_forecast(response_weather['forecast']['items'][count_forecast])]
    
    else:
        iter = 0
        forecast = [None] * len(response_weather['forecast']['items'])
        
        for item in response_weather['forecast']['items']:
            forecast[iter] = get_dict_forecast(item)
            iter += 1
            
        result['forecast'] = forecast

    return result

def get_dict_forecast(item):
    
    forecast = {
        "date": item['date'],
        "timestamp": item['dateWithTimezone'],
        "description": item['weather']['text'],
        "prec_probability": item['prec']['probability'],
        "temperature": {
            "min_c": item['temperature']['min'],
            "max_c": item['temperature']['max'],
        },
        "wind": {
            "wind_direction": item['wind']['direction'],
            "min_speed_kph": item['wind']['min'],
            "max_speed_kph": item['wind']['max'], 
            "gusts_value_kph": item['wind']['gusts']['value']
        }
    }
    
    return forecast;

def get_number_date(date: str, count_date: int):
    delta_date = dt.date.fromisoformat(date) - dt.date.today()
    
    if delta_date.days < 0:
        return 0
        
    elif delta_date.days >= count_date:
        return -1
    
    else:
        return delta_date.days
