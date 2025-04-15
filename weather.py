import os
import requests
import sqlite3
import csv
import datetime

DB_NAME = "test13.db"
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
STATE_FILE = "line.txt"
MAX_INSERTS_PER_RUN = 25

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
    yearly_data = {}
    for record in daily_data:
        date = record["date"]
        temperature = record["temperature_2m_mean"]
        if not temperature:
            continue
        year = date[:4]
        if year not in yearly_data:
            yearly_data[year] = {"total_temp": 0, "count": 0}
        yearly_data[year]["total_temp"] += temperature
        yearly_data[year]["count"] += 1

    yearly_averages = [
        {"year": year, "avg_temp": round(data["total_temp"] / data["count"], 2)}
        for year, data in yearly_data.items()
    ]

    with open(CSV_FILE, mode="a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        for record in yearly_averages:
            writer.writerow([city_name, record["year"], record["avg_temp"]])

def process_csv():
    if not os.path.exists(CSV_FILE):
        print("CSV file does not exist. Run the script to generate it first.")
        return

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    with open(STATE_FILE, "r+") as state_file:
        state = state_file.read().strip().split(",")
        current_line = int(state[0])
        csv_created = state[1] == "True"

        with open(CSV_FILE, mode="r") as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Skip the header row
            for i, row in enumerate(reader):
                if i < current_line:
                    continue
                if i >= current_line + MAX_INSERTS_PER_RUN:
                    break
                city, year, temp = row
                temp = float(temp) if temp else None
                if temp is not None:
                    cur.execute("SELECT id FROM locations WHERE city_name = ?", (city,))
                    location_id = cur.fetchone()
                    if location_id:
                        location_id = location_id[0]
                        cur.execute("""
                            INSERT INTO yearly_data (location_id, year, avg_temp)
                            VALUES (?, ?, ?)
                        """, (location_id, year, temp))
                        conn.commit()

        current_line += MAX_INSERTS_PER_RUN
        state_file.seek(0)
        state_file.write(f"{current_line},{csv_created}")
        state_file.truncate()

    conn.close()

def main():
    if not os.path.exists(STATE_FILE):
        with open(STATE_FILE, "w") as state_file:
            state_file.write("0,False")

    with open(STATE_FILE, "r") as state_file:
        state = state_file.read().strip().split(",")
        current_line = int(state[0])
        csv_created = state[1] == "True"

    if not csv_created:
        create_tables()
        with open(CSV_FILE, mode="w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["City", "Year", "Temperature (°C)"])

        for city_name, lat, lon in LOCATIONS:
            loc_id = get_or_create_location(lat, lon, city_name)
            data = retrieve_yearly_data(lat, lon, START_DATE, END_DATE)
            if not data:
                continue
            daily_info = extract_daily_info(data)
            write_to_csv(city_name, daily_info)

        with open(STATE_FILE, "w") as state_file:
            state_file.write(f"0,True")

    process_csv()

if __name__ == "__main__":
    main()
