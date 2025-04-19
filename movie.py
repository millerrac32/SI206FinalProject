import requests
import sqlite3
import time
import csv
import pandas as pd
import re

API_KEY = 'ca731278'
BASE_URL = 'http://www.omdbapi.com/'
DB_NAME = "test100.db"

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
    cur.execute('''
        CREATE TABLE IF NOT EXISTS Movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT UNIQUE,
            box_office INTEGER,
            year TEXT
        )
    ''')
    conn.commit()
    conn.close()

def parse_box_office(box_office_str):
    """Convert box office string (e.g., '$1,000,000') to an integer (e.g., 1000000)."""
    if not box_office_str or box_office_str == 'N/A':
        return None
    return int(re.sub(r'[^\d]', '', box_office_str))

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
    box_office = parse_box_office(movie_data.get('BoxOffice', 'N/A'))
    year = movie_data.get('Year', 'N/A')

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    try:
        cur.execute('''
            INSERT INTO Movies (title, box_office, year)
            VALUES (?, ?, ?)
        ''', (title, box_office, year))
        print(f"Stored: {title} ({year})")
    except sqlite3.IntegrityError:
        cur.execute('''
            UPDATE Movies SET year = ?, box_office = ? WHERE title = ?
        ''', (year, box_office, title))
        print(f"Updated: {title} ({year})")
    conn.commit()
    conn.close()

def export_movies_to_csv(filename="movies_export.csv"):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT title, box_office, year FROM Movies ORDER BY title")
    rows = cur.fetchall()
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Title", "Box Office", "Year"])
        for row in rows:
            writer.writerow(row)
    conn.close()
    print(f"Exported {len(rows)} movies to {filename}")

def export_movies_to_txt(filename="movies_export.txt"):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT title, box_office, year FROM Movies ORDER BY title")
    rows = cur.fetchall()
    with open(filename, "w", encoding="utf-8") as f:
        f.write("🎬 Movie Database Export\n")
        f.write("====================================\n")
        for row in rows:
            title, box_office, year = row
            f.write(f"Title: {title}\n")
            f.write(f"Box Office: {box_office}\n")
            f.write(f"Year: {year}\n")
            f.write("------------------------------------\n")
    conn.close()
    print(f"Movie data exported to {filename}")


####################################################################################################
def main():
    create_table()

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT title FROM Movies')
    stored_titles = set(row[0] for row in cur.fetchall())
    conn.close()

    remaining_titles = [title for title in MOVIE_TITLES if title not in stored_titles]
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

################################################################################################

if __name__ == '__main__':
    create_table()
    main()
    export_movies_to_txt()
    export_movies_to_csv()