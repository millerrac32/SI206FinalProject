# My API Key = 61e19889572de6f647a1b9d9d3d7836e
import requests
import json
import csv
import os
import sqlite3

DB_NAME = "test13.db"

# Fetch the list of countries from the CountryLayer API
def get_countries(api_key):
    url = "https://api.countrylayer.com/v2/all"
    params = {"access_key": api_key}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        #place the entire data in a json file called all_countries.json
        with open("all_countries.json", "w") as json_file:
            json.dump(data, json_file, indent=4)
        print("All countries data has been saved to all_countries.json.")
        # Check for API-specific error in the response
        
        if "error" in data:  # Check for API-specific error in the response
            print(f"API Error: {data['error']['info']}")
            return []
        return [country["name"] for country in data]  # Extract country names
    elif response.status_code == 404:
        print("Error: The requested resource does not exist (404 Not Found).")
        return []
    elif response.status_code == 101:
        print("Error: Invalid API Key specified.")
        return []
    elif response.status_code == 104:
        print("Error: Monthly API request volume has been exceeded.")
        return []
    else:
        print(f"Error: Unable to fetch countries (Status Code: {response.status_code})")
        return []

# Function to create a CSV file with country details: capital, population, latitude, and longitude
def makeCSV():
    # Read the JSON file and extract country details
    with open("all_countries.json", "r") as json_file:
        countries_data = json.load(json_file)

    # Write the country details to a CSV file
    with open("country_details.csv", "w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        # Write the header row
        writer.writerow(["Country Name", "Capital", "Population", "Latitude", "Longitude"])

        # Write data rows
        for country in countries_data:
            name = country.get("name", "N/A")
            capital = country.get("capital", "N/A")
            population = country.get("population", "N/A")
            latlng = country.get("latlng", ["N/A", "N/A"])
            latitude = latlng[0] if len(latlng) > 0 else "N/A"
            longitude = latlng[1] if len(latlng) > 1 else "N/A"
            writer.writerow([name, capital, population, latitude, longitude])

    print("Country details have been saved to country_details.csv.")
    
#describe function
#This function fetches data for a specific country using the CountryLayer API and saves it to a JSON file.
def get_country_data(api_key, country_name):
    url = f"https://api.countrylayer.com/v2/name/{country_name}"
    params = {"access_key": api_key, "fullText": "true"}
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        if "error" in data:  # Check for API-specific error in the response
            print(f"API Error: {data['error']['info']}")
            return
        # Save the data to a JSON file in the 'data_from_countries' folder
        folder_path = "data_from_countries"
        os.makedirs(folder_path, exist_ok=True)  # Create the folder if it doesn't exist
        file_path = os.path.join(folder_path, f"{country_name.replace(' ', '_')}.json")
        with open(file_path, "w") as json_file:
            json.dump(data, json_file, indent=4)
        print(f"Data for '{country_name}' has been saved to {file_path}.")
    elif response.status_code == 404:
        print("Error: The requested resource does not exist (404 Not Found).")
    elif response.status_code == 101:
        print("Error: Invalid API Key specified.")
    elif response.status_code == 104:
        print("Error: Monthly API request volume has been exceeded.")
    else:
        print(f"Error: Unable to fetch data for '{country_name}' (Status Code: {response.status_code}).")

def populate_database_from_csv(db_name, csv_file="country_details.csv", limit=25):
    conn = sqlite3.connect(os.path.join("..", db_name))
    cursor = conn.cursor()

    # Create the 'countries' table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS countries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country_name TEXT,
            capital TEXT,
            population INTEGER,
            latitude REAL,
            longitude REAL
        )
    ''')

    # Track already-inserted rows
    cursor.execute("SELECT COUNT(*) FROM countries")
    already_inserted = cursor.fetchone()[0]

    with open(csv_file, "r") as file:
        reader = csv.DictReader(file)
        for i, row in enumerate(reader):
            if i < already_inserted:
                continue  # Skip already-inserted rows
            if i >= already_inserted + limit:
                break  # Stop after inserting the limit

            country_name = row["Country Name"]
            capital = row["Capital"]
            population = int(row["Population"]) if row["Population"].isdigit() else None
            latitude = float(row["Latitude"]) if row["Latitude"] != "N/A" else None
            longitude = float(row["Longitude"]) if row["Longitude"] != "N/A" else None

            cursor.execute('''
                INSERT INTO countries (country_name, capital, population, latitude, longitude)
                VALUES (?, ?, ?, ?, ?)
            ''', (country_name, capital, population, latitude, longitude))

    conn.commit()

    # Check if at least 100 rows are stored in the database
    cursor.execute("SELECT COUNT(*) FROM countries")
    total_rows = cursor.fetchone()[0]
    if total_rows < 100:
        print(f"Warning: Only {total_rows} rows are stored in the database. Ensure at least 100 rows are added.")
    else:
        print(f"Database contains {total_rows} rows.")

    conn.close()
    print(f"Inserted up to {limit} new rows into the database.")


#function to interact with rachel's stuff
#She has a locations table. has city_name, latitude, longitude
#she also has a daily_data table. which has location_id: Foreign key referencing the locations table.
    #date: Date of the weather data (e.g., "2015-01-01").
    #temperature_2m_mean: The mean temperature for that day.



api_key = "61e19889572de6f647a1b9d9d3d7836e"


#gets all the available countries the api can interact with, places in a json file, and prints the names of the countries
countries = get_countries(api_key)
#print(countries)
    
# #FUnction to create a csv file with all the countries
makeCSV()
populate_database_from_csv(DB_NAME, "country_details.csv")
