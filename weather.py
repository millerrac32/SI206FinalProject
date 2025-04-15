import requests
import sqlite3
import csv
import datetime

DB_NAME = "test10.db"
USER_AGENT = "SI206Project/1.0 (your_email@umich.edu)"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/era5"

LOCATIONS = [
    ("Berlin", 52.52, 13.41),
    ("New York", 40.71, -74.01),
    ("Tokyo", 35.68, 139.69),
    ("Sydney", -33.87, 151.21),
    ("São Paulo", -23.55, -46.63),
    ("London", 51.51, -0.13),
    ("Paris", 48.86, 2.35),
    ("Moscow", 55.75, 37.62),
    ("Delhi", 28.66, 77.23),
    ("Los Angeles", 34.05, -118.25)
]

START_DATE = "2013-01-01"
END_DATE = "2022-12-31"
DAILY_PARAMS = "temperature_2m_mean"
ANALYSIS_OUTPUT_FILE = "analysis_results_yearly.txt"
CSV_FILE = "yearly_data.csv"
MAX_INSERTS_PER_RUN = 36500

def create_tables():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city_name TEXT,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL
        );
    """)
    conn.commit()
    conn.close()

def get_or_create_location(latitude, longitude, city_name):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT id FROM locations WHERE latitude=? AND longitude=?", (latitude, longitude))
    row = cur.fetchone()
    if row:
        location_id = row[0]
    else:
        cur.execute("INSERT INTO locations (city_name, latitude, longitude) VALUES (?, ?, ?)",
                    (city_name, latitude, longitude))
        conn.commit()
        location_id = cur.lastrowid
    conn.close()
    return location_id

def retrieve_yearly_data(latitude, longitude, start_date, end_date):
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "daily": DAILY_PARAMS,
        "timezone": "UTC"
    }
    headers = {"User-Agent": USER_AGENT}
    try:
        r = requests.get(ARCHIVE_URL, params=params, headers=headers, timeout=15)
        r.raise_for_status()
        return r.json()
    except:
        return None

def extract_daily_info(data):
    if not data or "daily" not in data or "temperature_2m_mean" not in data["daily"]:
        return []
    dates = data["daily"].get("time", [])
    temps = data["daily"].get("temperature_2m_mean", [])
    records = []
    for i in range(len(dates)):
        records.append({
            "date": dates[i],
            "temperature_2m_mean": temps[i]
        })
    return records

def write_to_csv(city_name, daily_data):
    # Aggregate daily data into yearly averages
    yearly_data = {}
    for record in daily_data:
        date = record["date"]
        temperature = record["temperature_2m_mean"]
        if not temperature:  # Skip if temperature is None
            continue
        year = date[:4]  # Extract "YYYY" from the date
        if year not in yearly_data:
            yearly_data[year] = {"total_temp": 0, "count": 0}
        yearly_data[year]["total_temp"] += temperature
        yearly_data[year]["count"] += 1

    # Calculate yearly averages
    yearly_averages = [
        {"year": year, "avg_temp": round(data["total_temp"] / data["count"], 2)}
        for year, data in yearly_data.items()
    ]

    # Write yearly averages to the CSV file
    with open(CSV_FILE, mode="a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        for record in yearly_averages:
            writer.writerow([city_name, record["year"], record["avg_temp"]])
            
def analyze_data_from_csv():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    # Create the yearly_data table if it doesn't exist
    cur.execute("""
        CREATE TABLE IF NOT EXISTS yearly_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location_id INTEGER NOT NULL,
            year TEXT NOT NULL,
            avg_temp REAL NOT NULL,
            FOREIGN KEY (location_id) REFERENCES locations (id)
        );
    """)
    conn.commit()

    city_yearly_data = {}
    with open(CSV_FILE, mode="r") as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Skip the header row
        for row in reader:
            city, year, temp = row
            temp = float(temp) if temp else None
            if temp is not None:
                # Get the location_id for the city
                cur.execute("SELECT id FROM locations WHERE city_name = ?", (city,))
                location_id = cur.fetchone()
                if location_id:
                    location_id = location_id[0]
                    # Insert the data into the yearly_data table
                    cur.execute("""
                        INSERT INTO yearly_data (location_id, year, avg_temp)
                        VALUES (?, ?, ?)
                    """, (location_id, year, temp))
                    conn.commit()

                # Add to city_yearly_data for analysis
                if city not in city_yearly_data:
                    city_yearly_data[city] = []
                city_yearly_data[city].append((year, temp))
    
    conn.close()
    return city_yearly_data

def write_analysis_to_file(yearly_averages):
    with open(ANALYSIS_OUTPUT_FILE, "w") as f:
        f.write("Yearly Average Temperature\n\n")
        for city in sorted(yearly_averages.keys()):
            f.write(f"{city}: {yearly_averages[city]:.2f} °C\n")

def main():
    create_tables()
    # Initialize CSV file with headers
    with open(CSV_FILE, mode="w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["City", "Year", "Temperature (°C)"])  # Updated header

    total_inserts_this_run = 0
    for city_name, lat, lon in LOCATIONS:
        if total_inserts_this_run >= MAX_INSERTS_PER_RUN:
            break
        loc_id = get_or_create_location(lat, lon, city_name)
        data = retrieve_yearly_data(lat, lon, START_DATE, END_DATE)
        if not data:
            continue
        daily_info = extract_daily_info(data)
        remaining_inserts = MAX_INSERTS_PER_RUN - total_inserts_this_run
        daily_info = daily_info[:remaining_inserts]
        write_to_csv(city_name, daily_info)
        
        total_inserts_this_run += len(daily_info)

    # Analyze the data from the CSV file
    # and write the results to a text file
    city_yearly_data = analyze_data_from_csv()
    yearly_averages = {
        city: sum(temp for _, temp in data) / len(data)
        for city, data in city_yearly_data.items()
    }
    
    write_analysis_to_file(yearly_averages)
    
    
    
    

if __name__ == "__main__":
    main()
