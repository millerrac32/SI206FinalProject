import requests
import sqlite3
import time

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

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    try:
        cur.execute('INSERT INTO Movies (title, box_office, genres) VALUES (?, ?, ?)', (title, box_office, genres))
        print(f"✅ Stored: {title}")
        conn.commit()
    except sqlite3.IntegrityError:
        print(f"⚠️ Skipped (already exists): {title}")
    conn.close()

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
            print(f"❌ Failed to fetch or bad response for: {title}")
        time.sleep(1)


if __name__ == '__main__':
    main()
