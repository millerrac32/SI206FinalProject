import requests
import sqlite3
import os

DB_NAME = "open_meteo_yearly.db"
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
    ("Beijing", 39.91, 116.41),
    ("Los Angeles", 34.05, -118.25)
]

START_DATE = "2015-01-01"
END_DATE = "2022-12-31"
DAILY_PARAMS = "temperature_2m_mean"
ANALYSIS_OUTPUT_FILE = "analysis_results_yearly.txt"

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
        CREATE TABLE IF NOT EXISTS daily_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            temperature_2m_mean REAL,
            FOREIGN KEY (location_id) REFERENCES locations(id),
            UNIQUE(location_id, date)
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
    except Exception as e:
        print(f"Error retrieving data for {latitude}, {longitude}: {e}")
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

def store_daily_data_with_limit(location_id, daily_data, limit):
    """
    Inserts records into the daily_data table for a given location, but
    stops after 'limit' new records have been inserted.
    The INSERT OR IGNORE ensures that duplicates are skipped.
    """
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    insert_count = 0
    for record in daily_data:
        if insert_count >= limit:
            break
        date_val = record["date"]
        temp_val = record["temperature_2m_mean"]
        try:
            cur.execute("""
                INSERT OR IGNORE INTO daily_data (location_id, date, temperature_2m_mean)
                VALUES (?, ?, ?)
            """, (location_id, date_val, temp_val))
            if cur.rowcount == 1:
                insert_count += 1
        except Exception as e:
            print(f"Error inserting record {record}: {e}")
    conn.commit()
    conn.close()
    return insert_count

def load_joined_data():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT L.city_name, D.date, D.temperature_2m_mean
        FROM daily_data AS D
        JOIN locations AS L
        ON D.location_id = L.id
        ORDER BY L.city_name, D.date
    """)
    rows = cur.fetchall()
    conn.close()
    return rows

def analyze_data_by_year(data):
    if not data:
        return {}
    city_year_temps = {}
    for city, date_str, temp in data:
        year = date_str.split("-")[0]
        city_year_temps.setdefault(city, {}).setdefault(year, []).append(temp)
    
    city_year_avgs = {}
    for city, year_dict in city_year_temps.items():
        city_year_avgs[city] = {}
        for year, temps in year_dict.items():
            if temps:
                city_year_avgs[city][year] = sum(temps) / len(temps)
            else:
                city_year_avgs[city][year] = None
    return city_year_avgs

def write_analysis_to_file(yearly_averages):
    with open(ANALYSIS_OUTPUT_FILE, "w") as f:
        f.write("Yearly Average Temperature by City and Year\n\n")
        for city in sorted(yearly_averages.keys()):
            f.write(f"City: {city}\n")
            for year in sorted(yearly_averages[city].keys()):
                avg = yearly_averages[city][year]
                f.write(f"  {year}: {avg:.2f} °C\n")
            f.write("\n")

def main():
    create_tables()
    total_inserted = 0
    MAX_RECORDS_PER_RUN = 25
    for city_name, lat, lon in LOCATIONS:
        if total_inserted >= MAX_RECORDS_PER_RUN:
            break
        loc_id = get_or_create_location(lat, lon, city_name)
        data = retrieve_yearly_data(lat, lon, START_DATE, END_DATE)
        if not data:
            continue
        daily_info = extract_daily_info(data)
        remaining_limit = MAX_RECORDS_PER_RUN - total_inserted
        inserted = store_daily_data_with_limit(loc_id, daily_info, limit=remaining_limit)
        total_inserted += inserted
        print(f"Inserted {inserted} records for {city_name}.")
    print(f"Total new records inserted this run: {total_inserted}")
    joined_data = load_joined_data()
    yearly_averages = analyze_data_by_year(joined_data)
    write_analysis_to_file(yearly_averages)
    print(f"Analysis written to {ANALYSIS_OUTPUT_FILE}")

if __name__ == "__main__":
    main()
