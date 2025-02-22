import datetime
import requests
import string
from flask import Flask, render_template, request, redirect, url_for
import os
from dotenv import load_dotenv
load_dotenv()

import mysql.connector

# Establish database connection
db = mysql.connector.connect(
    host="localhost",      # e.g., "localhost"
    user="root",      # e.g., "root"
    password="",
    database="irrigation"
)

cursor = db.cursor()  # Create a cursor object


OWM_ENDPOINT = "https://api.openweathermap.org/data/2.5/weather"
OWM_FORECAST_ENDPOINT = "https://api.openweathermap.org/data/2.5/forecast"
GEOCODING_API_ENDPOINT = "http://api.openweathermap.org/geo/1.0/direct"
api_key = os.getenv("OWM_API_KEY")
# api_key = os.environ.get("OWM_API_KEY")

app = Flask(__name__)


# Display home page and get city name entered into search form
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        city = request.form.get("search")
        return redirect(url_for("get_weather", city=city))
    return render_template("index.html")

"""
# Display weather forecast for specific city using data from OpenWeather API
@app.route("/<city>", methods=["GET", "POST"])
def get_weather(city):
    # Format city name and get current date to display on page
    city_name = string.capwords(city)
    today = datetime.datetime.now()
    current_date = today.strftime("%A, %B %d")

    # Get latitude and longitude for city
    location_params = {
        "q": city_name,
        "appid": api_key,
        "limit": 3,
    }

    location_response = requests.get(GEOCODING_API_ENDPOINT, params=location_params)
    location_data = location_response.json()
    
    # Prevent IndexError if user entered a city name with no coordinates by redirecting to error page
    if not location_data:
        return redirect(url_for("error"))
    else:
        lat = location_data[0]['lat']
        lon = location_data[0]['lon']

    # Get OpenWeather API data
    weather_params = {
        "lat": lat,
        "lon": lon,
        "appid": api_key,
        "units": "metric",
    }
    weather_response = requests.get(OWM_ENDPOINT, weather_params)
    weather_response.raise_for_status()
    weather_data = weather_response.json()

    # Get current weather data
    current_temp = round(weather_data['main']['temp'])
    current_weather = weather_data['weather'][0]['main']
    min_temp = round(weather_data['main']['temp_min'])
    max_temp = round(weather_data['main']['temp_max'])
    wind_speed = weather_data['wind']['speed']

    # Get five-day weather forecast data
    forecast_response = requests.get(OWM_FORECAST_ENDPOINT, weather_params)
    forecast_data = forecast_response.json()

    # Make lists of temperature and weather description data to show user
    five_day_temp_list = [round(item['main']['temp']) for item in forecast_data['list'] if '12:00:00' in item['dt_txt']]
    five_day_weather_list = [item['weather'][0]['main'] for item in forecast_data['list']
                             if '12:00:00' in item['dt_txt']]

    # Get next four weekdays to show user alongside weather data
    five_day_unformatted = [today, today + datetime.timedelta(days=1), today + datetime.timedelta(days=2),
                            today + datetime.timedelta(days=3), today + datetime.timedelta(days=4)]
    five_day_dates_list = [date.strftime("%a") for date in five_day_unformatted]

    return render_template("city.html", city_name=city_name, current_date=current_date, current_temp=current_temp,
                           current_weather=current_weather, min_temp=min_temp, max_temp=max_temp, wind_speed=wind_speed,
                           five_day_temp_list=five_day_temp_list, five_day_weather_list=five_day_weather_list,
                           five_day_dates_list=five_day_dates_list)
"""

@app.route("/<city>", methods=["GET", "POST"])
def get_weather(city):
    city_name = string.capwords(city)
    today = datetime.datetime.now()
    current_date = today.strftime("%A, %B %d")

    # Get latitude and longitude for city
    location_params = {
        "q": city_name,
        "appid": api_key,
        "limit": 3,
    }

    location_response = requests.get(GEOCODING_API_ENDPOINT, params=location_params)
    location_data = location_response.json()

    if not location_data:
        return redirect(url_for("error"))

    lat = location_data[0]['lat']
    lon = location_data[0]['lon']

    # Get weather data
    weather_params = {
        "lat": lat,
        "lon": lon,
        "appid": api_key,
        "units": "metric",
    }
    weather_response = requests.get(OWM_ENDPOINT, weather_params)
    weather_data = weather_response.json()

    current_temp = round(weather_data['main']['temp'])
    current_weather = weather_data['weather'][0]['main']
    min_temp = round(weather_data['main']['temp_min'])
    max_temp = round(weather_data['main']['temp_max'])
    wind_speed = weather_data['wind']['speed']

    # Get five-day weather forecast
    forecast_response = requests.get(OWM_FORECAST_ENDPOINT, weather_params)
    forecast_data = forecast_response.json()

    five_day_temp_list = [round(item['main']['temp']) for item in forecast_data['list'] if '12:00:00' in item['dt_txt']]
    five_day_weather_list = [item['weather'][0]['main'] for item in forecast_data['list']
                             if '12:00:00' in item['dt_txt']]
    five_day_dates_list = [(today + datetime.timedelta(days=i)).strftime("%a") for i in range(5)]

    # **Call should_irrigate() function to get irrigation decision**
    irrigation_status = should_irrigate(city_name)

    return render_template(
        "city.html",
        city_name=city_name,
        current_date=current_date,
        current_temp=current_temp,
        current_weather=current_weather,
        min_temp=min_temp,
        max_temp=max_temp,
        wind_speed=wind_speed,
        five_day_temp_list=five_day_temp_list,
        five_day_weather_list=five_day_weather_list,
        five_day_dates_list=five_day_dates_list,
        pump_status=irrigation_status.get("Pump Status", "Unknown"),
        soil_moisture=irrigation_status.get("Soil Moisture", "Unknown"),
        rain_expected="Yes" if irrigation_status.get("Rain Expected") else "No",
    )








# Display error page for invalid input
@app.route("/error")
def error():
    return render_template("error.html")
@app.route('/update', methods=['POST'])
def update_data():
    try:
        data = request.json
        record_id = data.get('id')
        moisture = data.get('moisture')
        temperature = data.get('temperature')

        if not record_id or moisture is None or temperature is None:
            return jsonify({"error": "Missing required fields"}), 400

        # SQL query to update the record
        query = "UPDATE IrrigationData SET soill_moisture = %s, Temperature = %s WHERE id = %s"
        values = (moisture, temperature, record_id)

        cursor.execute(query, values)
        db.commit()  # Save changes to the database

        if cursor.rowcount > 0:
            return jsonify({"message": "Data updated successfully"}), 200
        else:
            return jsonify({"error": "Record not found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/sensors")
def sensors():
    return render_template("sensors.html")




def should_irrigate(city):
    """Determines if irrigation is needed based on soil moisture and weather forecast."""
    
    # Get the latest soil moisture data from the database
    cursor.execute("SELECT soil_moisture, Weather_Rainfall FROM IrrigationData WHERE City=%s ORDER BY timestamp DESC LIMIT 1", (city,))
    data = cursor.fetchone()
    
    if not data:
        return {"error": "No data found for Chennai"}
    
    soil_moisture, expected_rainfall = data  # Extract values

    # Fetch weather forecast for Chennai
    weather_params = {
        "q": city,
        "appid": api_key,
        "units": "metric",
    }
    forecast_response = requests.get(OWM_FORECAST_ENDPOINT, params=weather_params)
    forecast_data = forecast_response.json()
    
    # Check if rain is expected in the next 2 days
    rain_forecast = any("rain" in item["weather"][0]["main"].lower() for item in forecast_data["list"][:16])  # Checking first 2 days
    
    # Define irrigation decision logic
    if soil_moisture < 30 and not rain_forecast:
        pump_status = "ON"
    else:
        pump_status = "OFF"

    # Update the database with the decision
    cursor.execute("UPDATE IrrigationData SET Pump_Status = %s WHERE City = %s ORDER BY timestamp DESC LIMIT 1", 
                   (pump_status, city))
    db.commit()
    
    return {"Pump Status": pump_status, "Soil Moisture": soil_moisture, "Rain Expected": rain_forecast}













if __name__ == "__main__":
    app.run(debug=True)
