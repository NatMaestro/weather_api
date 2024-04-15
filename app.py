import os
import psycopg2
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv
from flask import Flask, json, jsonify, request

load_dotenv()

app = Flask(__name__)

# Connect to the database

hostname = os.getenv("HOST_NAME")
database = os.getenv("DATABASE")
username = os.getenv("USERNAME")
pwd = os.getenv("PASSWORD")
port_id = os.getenv("PORT_ID")


try:
    connection = psycopg2.connect(
        host=hostname,
        dbname=database,
        user=username,
        password=pwd,
        port=port_id
    )
    print("Successfully connected to the database")
except Exception as e:
    print(f"Failed to connect to the database: {e}")


# Get the Weather API Data
url = os.getenv("API_URL")


# 
@app.route('/check_weather', methods=['POST','GET'])
def check_weather():
    if request.method== "POST":
        print("hey")
        try:
            data = request.get_json()
            city = data.get('city', 'Accra')  # Default to 'Accra' if 'city' is not provided
            print(data)
            response = requests.get(url.format(city))

            response = response.json()
            # country = response['sys']["country"]
            # temperature = response["main"]["temp"]
            # description = response['weather'][0]['description']
            # try:
            #     date = datetime.strptime(response['date'], "%m-%d-%Y %H:%M:%S")
            # except KeyError:
            #     date = datetime.now(timezone.utc)
            
            if response["cod"] == 200:
                weather_data = {
                "city": response["name"],
                "country": response.get("sys", {}).get("country", ""),  # Safely extract country information
                "temperature": response["main"]["temp"],
                "description": response["weather"][0]["description"],
                "icon": response["weather"][0]["icon"],
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # Include date in the timestamp
                "date": datetime.now().strftime("%Y-%m-%d")
            } 
                cursor = connection.cursor()
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS weather_data (
                    id SERIAL PRIMARY KEY,
                    city VARCHAR(255) NOT NULL,
                    country VARCHAR(255) NOT NULL,
                    temperature REAL NOT NULL,
                    description VARCHAR(255) NOT NULL,
                    time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    date DATE
                )
            """)
                connection.commit()
                cursor.execute("INSERT INTO weather_data (city, country, temperature, description, time, date) VALUES (%s, %s, %s, %s, %s, %s)",
                (weather_data["city"], weather_data["country"], weather_data["temperature"], weather_data["description"], weather_data["time"], weather_data["date"]))

                connection.commit()
        

                return jsonify({"message": "Data Successfully added","weather":weather_data})
            else:
                return jsonify({"error": "Failed to fetch weather data"}), response.status_code
        
        except Exception as e:
            return jsonify({"error": str(e)}), 500  # Return error message and HTTP status code 500 for internal server error
    else:
        connection.close()
        return "Checked Successfully"

@app.route('/view_weather_data')
def view():
    cursor = connection.cursor()
    cursor.description

    cursor.execute('SELECT * FROM weather_data ORDER BY id')
    data = cursor.fetchall()
    # Convert rows to list of dictionaries
    all_data = [dict((cursor.description[i][0], value) for i, value in enumerate(row)) for row in data]

    # Convert to JSON
    json_data = json.dumps(all_data)

    # Close cursor and connection
    cursor.close()
    connection.close()
    return jsonify({"message":"Data retrieved Successfully", "All Weather Data": all_data})
