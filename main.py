import subprocess
import sqlite3
import csv
import os
import requests
import json
import time
import random
import datetime

# Run weather.py
subprocess.run(["python3", "weather.py"])

# Run pop.py
subprocess.run(["python3", "populationAPI/pop.py"])

# Run movie.py
subprocess.run(["python3", "movie.py"])


#function to interact with rachel's stuff
#She has a locations table. has city_name, latitude, longitude

#she also has a daily_data table. 
# which has location_id: Foreign key referencing the locations table.
#date: Date of the weather data (e.g., "2015-01-01").
#temperature_2m_mean: The mean temperature for that day.
    
#Population table is called countries
# id:
# Type: INTEGER
# Description: Primary key, auto-incremented for each row.
# country_name:
# Type: TEXT
# Description: The name of the country.
# capital:
# Type: TEXT
# Description: The capital city of the country.
# population:
# Type: INTEGER
# Description: The population of the country (can be NULL if not available).
# latitude:
# Type: REAL
# Description: The latitude of the country's location (can be NULL if not available).
# longitude:
# Type: REAL
# Description: The longitude of the country's location (can be NULL if not available).

city_avg_temperatures = []

with open("yearlyWeather.txt", "r") as file:
    lines = file.readlines()
    city_name = None
    total_temp = 0
    count = 0

    for line in lines:
        line = line.strip()
        if line.startswith("City:"):
            # Save the previous city's data if available
            if city_name and count > 0:
                avg_temp = round(total_temp / count, 2)
                city_avg_temperatures.append((city_name, avg_temp))
            
            # Start processing a new city
            city_name = line.split("City:")[1].strip()
            total_temp = 0
            count = 0
        elif line and ":" in line and "°C" in line:
            # Extract the temperature value
            try:
                temp = float(line.split(":")[1].split("°C")[0].strip())
                total_temp += temp
                count += 1
            except ValueError:
                continue

    # Save the last city's data
    if city_name and count > 0:
        avg_temp = round(total_temp / count, 2)
        city_avg_temperatures.append((city_name, avg_temp))

# Print the list of tuples
print(city_avg_temperatures)

DB_NAME = "open_meteo.db"

# Connect to the SQLite database
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# Create a dictionary to store the data
capital_info = {}

# Iterate through the city_avg_temperatures list
for city, avg_temp in city_avg_temperatures:
    # Query the countries table for the capital matching the city name
    cursor.execute("""
        SELECT population, latitude, longitude 
        FROM countries 
        WHERE capital = ?
    """, (city,))
    
    result = cursor.fetchone()
    if result:
        # Add the data to the dictionary
        capital_info[city] = list(result)

# Print the dictionary
print(capital_info)


import matplotlib.pyplot as plt

# Prepare data for visualization
filtered_data = [(city, temp, capital_info[city][0], capital_info[city][1]) for city, temp in city_avg_temperatures if city in capital_info]
cities = [city for city, _, _, _ in filtered_data]
populations = [population for _, _, population, _ in filtered_data]
latitudes = [latitude for _, _, _, latitude in filtered_data]
avg_temperatures = [temp for _, temp, _, _ in filtered_data]

# Visualization 1: Population vs. Distance from Equator (Latitude)
plt.figure(figsize=(10, 6))
plt.scatter(latitudes, populations, color='blue', alpha=0.7)
plt.title("Population vs. Distance from Equator (Latitude)")
plt.xlabel("Latitude (degrees)")
plt.ylabel("Population")
plt.grid(True)
plt.savefig("population_vs_latitude.png")

# Visualization 2: Average Temperature vs. Latitude
plt.figure(figsize=(10, 6))
plt.scatter(latitudes, avg_temperatures, color='green', alpha=0.7)
plt.title("Average Temperature vs. Latitude")
plt.xlabel("Latitude (degrees)")
plt.ylabel("Average Temperature (°C)")
plt.grid(True)
plt.savefig("avg_temperature_vs_latitude.png")

# Visualization 3: Population vs. Average Temperature
plt.figure(figsize=(10, 6))
plt.scatter(avg_temperatures, populations, color='red', alpha=0.7)
plt.title("Population vs. Average Temperature")
plt.xlabel("Average Temperature (°C)")
plt.ylabel("Population")
plt.grid(True)
plt.savefig("population_vs_avg_temperature.png")

# Close the database connection
conn.close()




