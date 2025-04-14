import requests
import sqlite3
import time
import csv
import pandas as pd
import plotly.express as px
import re


#

API_KEY = 'ca731278'
BASE_URL = 'http://www.omdbapi.com/'
DB_NAME = "movies.db"

MOVIE_TITLES = [
    "The Shawshank Redemption", "The Godfather", "The Dark Knight", "Pulp Fiction",
    "Forrest Gump", "Inception", "The Matrix", "Fight Club", "The Lord of the Rings: The Fellowship of the Ring",
    "The Empire Strikes Back", "The Lord of the Rings: The Return of the King", "Interstellar",
    "The Green Mile", "Gladiator", "The Lion King", "The Prestige", "Saving Private Ryan",
    "The Silence of the Lambs", "Schindler's List", "Se7en", "The Departed", "Django Unchained",
    "The Wolf of Wall Street", "Whiplash", "Avengers: Endgame", "Avengers: Infinity War",
    "Iron Man", "Spider-Man: No Way Home", "Black Panther", "Doctor Strange", "Guardians of the Galaxy",
    "Captain America: Civil War", "Captain Marvel", "Thor: Ragnarok", "Ant-Man", "Deadpool",
    "The Batman", "Joker", "Logan", "The Hunger Games", "Harry Potter and the Sorcerer's Stone",
    "Harry Potter and the Prisoner of Azkaban", "Harry Potter and the Deathly Hallows: Part 2",
    "Fantastic Beasts and Where to Find Them", "Frozen", "Frozen II", "Toy Story", "Toy Story 3",
    "Coco", "Inside Out", "Up", "Finding Nemo", "Monsters, Inc.", "Shrek", "Shrek 2",
    "How to Train Your Dragon", "Kung Fu Panda", "Despicable Me", "Zootopia", "Moana",
    "Encanto", "Turning Red", "The Incredibles", "Ratatouille", "Cars",
    "Wall-E", "Soul", "Brave", "Luca", "Tangled", "Big Hero 6", "Wreck-It Ralph", "Frozen Fever",
    "Maleficent", "Aladdin", "Beauty and the Beast", "The Little Mermaid", "Cinderella",
    "Mulan", "Pocahontas", "Hercules", "Tarzan", "The Hunchback of Notre Dame",
    "Pirates of the Caribbean: The Curse of the Black Pearl", "Pirates of the Caribbean: Dead Man's Chest",
    "National Treasure", "The Chronicles of Narnia: The Lion, the Witch and the Wardrobe",
    "The Maze Runner", "Divergent", "Twilight", "Eclipse", "Breaking Dawn - Part 2", "The Fault in Our Stars",
    "The Notebook", "La La Land", "A Star is Born", "Bohemian Rhapsody", "Rocketman",
    "Elvis", "The Greatest Showman", "Les Misérables", "Hamilton", "West Side Story"
]

def create_table():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # Only create the table if it doesn't already exist
    cur.execute('''
        CREATE TABLE IF NOT EXISTS Movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT UNIQUE,
            box_office TEXT,
            genres TEXT
        )
    ''')

    conn.commit()
    conn.close()

def add_year_column():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # Try to add the 'year' column if it doesn't exist
    try:
        cur.execute("ALTER TABLE Movies ADD COLUMN year TEXT")
        print("'year' column added to Movies table.")
    except sqlite3.OperationalError:
        print("'year' column already exists.")
    
    conn.commit()
    conn.close()


def patch_missing_years():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # Find movies with no year info
    cur.execute("SELECT title FROM Movies WHERE year IS NULL OR year = '' OR year = 'N/A'")
    missing = [row[0] for row in cur.fetchall()]
    conn.close()

    print(f"Found {len(missing)} movies missing year.")

    for title in missing[:25]:  # Still respect the 25-per-run rule
        print(f"Fetching year for: {title}")
        data = fetch_movie_data(title)
        if data and data.get("Response") == "True":
            year = data.get("Year", "N/A")
            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute("UPDATE Movies SET year = ? WHERE title = ?", (year, title))
            conn.commit()
            conn.close()
            print(f"Updated year: {title} ({year})")
        else:
            print(f"Could not fetch: {title}")
        time.sleep(1)


def fetch_movie_data(title):
    params = {
        't': title,
        'apikey': API_KEY
    }
    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        return response.json()
    return None

def store_movie_data(movie_data):
    if movie_data.get('Response') == 'False':
        return

    title = movie_data.get('Title')
    box_office = movie_data.get('BoxOffice', 'N/A')
    genres = movie_data.get('Genre', '')
    year = movie_data.get('Year', 'N/A')

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    try:
        cur.execute('''
            INSERT INTO Movies (title, box_office, genres, year)
            VALUES (?, ?, ?, ?)
        ''', (title, box_office, genres, year))
        print(f"Stored: {title} ({year})")
    except sqlite3.IntegrityError:
        # Already exists — update year
        cur.execute('''
            UPDATE Movies SET year = ? WHERE title = ?
        ''', (year, title))
        print(f"Updated year for: {title} ({year})")
    conn.commit()
    conn.close()

def export_movies_to_csv(filename="movies_export.csv"):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # Get all movies
    cur.execute("SELECT title, box_office, genres, year FROM Movies ORDER BY title")
    rows = cur.fetchall()

    # Write to CSV
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # Write header row
        writer.writerow(["Title", "Box Office", "Genres", "Year"])
        # Write data rows
        for row in rows:
            writer.writerow(row)

    conn.close()
    print(f"Exported {len(rows)} movies to {filename}")


# Load your data
movie_df = pd.read_csv("movies_export.csv")

def clean_box_office(value):
    if isinstance(value, str):
        cleaned = re.sub(r'[^\d.]', '', value)
        return int(cleaned) if cleaned.isdigit() else None
    return None

movie_df['Box Office Cleaned'] = movie_df['Box Office'].apply(clean_box_office)
movie_df['Year'] = pd.to_numeric(movie_df['Year'], errors='coerce')
box_office_by_year = movie_df.groupby('Year')['Box Office Cleaned'].mean().dropna().reset_index()
box_office_by_year.columns = ['Year', 'Average Box Office']

# Parse LA temp data
la_yearly_temp = {}
with open("analysis_results_yearly.txt", "r", encoding="utf-8") as f:
    lines = f.readlines()

in_la = False
for line in lines:
    if "City: Los Angeles" in line:
        in_la = True
        continue
    if in_la:
        if line.startswith("City:"):
            break
        match = re.match(r"(\d{4}): ([\d.]+) °C", line.strip())
        if match:
            la_yearly_temp[int(match.group(1))] = float(match.group(2))

temp_df = pd.DataFrame(list(la_yearly_temp.items()), columns=['Year', 'Average Temperature'])

# Merge and plot
merged_df = pd.merge(temp_df, box_office_by_year, on='Year')
fig = px.scatter(
    merged_df,
    x='Average Temperature',
    y='Average Box Office',
    title='LA Avg Temp vs Movie Box Office',
    hover_name='Year',
    trendline='ols'
)
fig.show()




def main():
    create_table()

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT title FROM Movies')
    stored_titles = set(row[0] for row in cur.fetchall())
    conn.close()

    # Filter out movies that are already in the DB
    remaining_titles = [title for title in MOVIE_TITLES if title not in stored_titles]

    # Limit to 25 new attempts per run
    to_process = remaining_titles[:25]

    print(f"🎬 Attempting to process {len(to_process)} movies...")

    for title in to_process:
        print(f"Fetching: {title}")
        data = fetch_movie_data(title)
        if data and data.get("Response") == "True":
            store_movie_data(data)
        else:
            print(f"Failed to fetch or bad response for: {title}")
        time.sleep(1)
def export_movies_to_txt(filename="movies_export.txt"):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("SELECT title, box_office, genres, year FROM Movies ORDER BY title")
    rows = cur.fetchall()

    with open(filename, "w", encoding="utf-8") as f:
        f.write("🎬 Movie Database Export\n")
        f.write("====================================\n")
        for row in rows:
            title, box_office, genres, year = row
            f.write(f"Title: {title}\n")
            f.write(f"Box Office: {box_office}\n")
            f.write(f"Genres: {genres}\n")
            f.write(f"Year: {year}\n")
            f.write("------------------------------------\n")

    conn.close()
    print(f"Movie data exported to {filename}")



if __name__ == '__main__':
    create_table()
    add_year_column()
    patch_missing_years()
    export_movies_to_txt()
    export_movies_to_csv()
