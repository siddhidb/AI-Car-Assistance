from flask import Flask, request, render_template, jsonify
import openrouteservice
from openrouteservice import convert
import folium
import requests
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import os
import osmnx as ox  # For address geocoding

# Initialize Flask app
app = Flask(__name__)

# ---------- OpenRouteService Setup ----------
ors_api_key = '5b3ce3597851110001cf62483559ef0b0fba4d588a1bc854367193c6'
ors_client = openrouteservice.Client(key=ors_api_key)

# ---------- Weather Setup using wttr.in ----------
location = "Pune"
weather_url = f"https://wttr.in/{location}?format=j1"

# ---------- Machine Learning Model ----------
def train_model():
    data = {
        "Time_of_Day": ["Morning", "Afternoon", "Evening", "Night", "Morning", "Evening", "Afternoon", "Night", "Morning", "Evening"],
        "Weather": ["Sunny", "Rainy", "Foggy", "Sunny", "Rainy", "Foggy", "Sunny", "Rainy", "Foggy", "Sunny"],
        "Distance_km": [5.0, 5.0, 5.0, 5.0, 10.0, 10.0, 10.0, 10.0, 15.0, 15.0],
        "Duration_min": [10, 12, 15, 9, 20, 25, 18, 22, 30, 28]
    }
    df = pd.DataFrame(data)

    # Encode categorical variables
    le_time = LabelEncoder()
    le_weather = LabelEncoder()
    df['Time_of_Day'] = le_time.fit_transform(df['Time_of_Day'])
    df['Weather'] = le_weather.fit_transform(df['Weather'])

    X = df[['Time_of_Day', 'Weather', 'Distance_km']]
    y = df['Duration_min']

    model = RandomForestRegressor(random_state=42)
    model.fit(X, y)
    return model, le_time, le_weather

# Train model
model, le_time, le_weather = train_model()

# ---------- Flask Routes ----------
@app.route('/', methods=["GET", "POST"])
def index():
    if request.method == "POST":
        origin_address = request.form.get("origin")
        destination_address = request.form.get("destination")
        time_of_day = request.form.get("time")

        try:
            origin_coords_temp = list(ox.geocode(origin_address))
            destination_coords_temp = list(ox.geocode(destination_address))
        except Exception as e:
            return f"Error geocoding addresses: {e}"

        origin_coords = (origin_coords_temp[1], origin_coords_temp[0])
        destination_coords = (destination_coords_temp[1], destination_coords_temp[0])

        try:
            route = ors_client.directions(
                coordinates=[origin_coords, destination_coords],
                profile='driving-car',
                format='geojson'
            )
        except Exception as e:
            return f"Error fetching route: {e}"

        summary = route['features'][0]['properties']['summary']
        distance_km = summary['distance'] / 1000
        duration_min = summary['duration'] / 60

        try:
            weather_response = requests.get(weather_url)
            weather_data = weather_response.json()
            current_temp = weather_data['current_condition'][0]['temp_C']
            weather_desc = weather_data['current_condition'][0]['weatherDesc'][0]['value']
        except Exception as e:
            current_temp = "N/A"
            weather_desc = "N/A"
            print("Error fetching weather:", e)

        try:
            encoded_time = le_time.transform([time_of_day])[0]
            if weather_desc in le_weather.classes_:
                encoded_weather = le_weather.transform([weather_desc])[0]
            else:
                encoded_weather = 0
            predicted_duration = model.predict([[encoded_time, encoded_weather, distance_km]])[0]
        except Exception as e:
            predicted_duration = "N/A"
            print("Error predicting travel time:", e)

        # Map generation
        m = folium.Map(location=[origin_coords_temp[0], origin_coords_temp[1]], zoom_start=13)
        folium.GeoJson(route, name='route').add_to(m)
        folium.Marker(location=[origin_coords_temp[0], origin_coords_temp[1]], tooltip='Start').add_to(m)
        folium.Marker(location=[destination_coords_temp[0], destination_coords_temp[1]], tooltip='End').add_to(m)

        m.save('Templates/map.html')

        return render_template("map.html",
                               distance=f"{distance_km:.2f} km",
                               duration=f"{duration_min:.2f} min",
                               predicted_duration=f"{predicted_duration:.2f} min",
                               temp=current_temp,
                               weather=weather_desc)
    return render_template("index.html")

# Run the app
if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, render_template, request
import openrouteservice

app = Flask(__name__)

# Your OpenRouteService API Key
api_key = 'your_openrouteservice_api_key'
client = openrouteservice.Client(key=api_key)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/route', methods=['POST'])
def route():
    origin = request.form['origin']
    destination = request.form['destination']
    time = request.form['time']

    # Here you can use geocoding if needed (or skip and mock for now)
    # Example response placeholder
    route_info = f"Simulated optimal route considering traffic and time: {time}"

    return render_template('map.html', origin=origin, destination=destination, time=time, route_info=route_info)

if __name__ == '__main__':
    app.run(debug=True)
    
    
import os
print(f"Template folder: {os.path.join(os.getcwd(), 'Templates')}")
