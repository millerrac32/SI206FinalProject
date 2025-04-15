import sqlite3
import matplotlib.pyplot as plt

#Capital cities that match between countries-> capital and locations-> city_name
# Berlin:
# London: 
# Moscow: 
# Paris: 
# Tokyo: 

DB_NAME = "test13.db"

#COUNTRIES INFORMATION
#Table: countries
# Columns: country_name, capital, population, latitude, longitude


#WEATHER INFORMATION
#The two tables share a common column: locations-> id and yearly_data-> location_id
#Table yearly_data
# Columns: id, location_id, year, avg_temp
#Table: locations
# Columns: id, city_name, latitude, longitude

# Connect to the SQLite database
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# Prepare data for visualization

# 1. Graph: Average temperature vs Population for capital cities
query1 = """
SELECT c.capital, c.population, AVG(y.avg_temp) as avg_temp
FROM countries c
JOIN locations l ON c.capital = l.city_name
JOIN yearly_data y ON l.id = y.location_id
GROUP BY c.capital
"""
cursor.execute(query1)
data1 = cursor.fetchall()

capitals = [row[0] for row in data1]
populations = [row[1] for row in data1]
avg_temps = [row[2] for row in data1]

plt.figure(figsize=(10, 6))
plt.scatter(populations, avg_temps, color='blue')
plt.title('Average Temperature vs Population for Capital Cities')
plt.xlabel('Population')
plt.ylabel('Average Temperature (°C)')
plt.grid(True)
plt.show()

# 2. Graph: Average temperature over years for a specific capital city (e.g., Berlin)
query2 = """
SELECT y.year, AVG(y.avg_temp) as avg_temp
FROM yearly_data y
JOIN locations l ON y.location_id = l.id
WHERE l.city_name = 'Berlin'
plt.show(block=True)
ORDER BY y.year
"""
cursor.execute(query2)
data2 = cursor.fetchall()

years = [row[0] for row in data2]
avg_temps_berlin = [row[1] for row in data2]

plt.figure(figsize=(10, 6))
plt.plot(years, avg_temps_berlin, marker='o', color='green')
plt.title('Average Temperature Over Years for Berlin')
plt.xlabel('Year')
plt.ylabel('Average Temperature (°C)')
plt.grid(True)
plt.show()

# 3. Graph: Latitude vs Average Temperature for all locations
query3 = """
SELECT l.latitude, AVG(y.avg_temp) as avg_temp
FROM locations l
JOIN yearly_data y ON l.id = y.location_id
GROUP BY l.latitude
"""
cursor.execute(query3)
data3 = cursor.fetchall()

latitudes = [row[0] for row in data3]
avg_temps_lat = [row[1] for row in data3]

plt.figure(figsize=(10, 6))
plt.scatter(latitudes, avg_temps_lat, color='red')
plt.title('Latitude vs Average Temperature')
plt.xlabel('Latitude')
plt.ylabel('Average Temperature (°C)')
plt.grid(True)
plt.show()

# Close the database connection
conn.close()
