import sqlite3
import matplotlib.pyplot as plt

#Capital cities that match between countries-> capital and locations-> city_name
# Berlin:
# London: 
# Moscow: 
# Paris: 
# Tokyo: 

DB_NAME = "test30.db"

#COUNTRIES INFORMATION
#Table: countries
# Columns: country_name, capital, population, latitude, longitude


#WEATHER INFORMATION
#The two tables share a common column: locations-> id and yearly_data-> location_id
#Table yearly_data
# Columns: id, location_id, year, avg_temp
#Table: locations
# Columns: id, city_name, latitude, longitude

#This whole data is from los angeles
#Table: Movies
# Columns: id, title, box_office, genres, year

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


# 4. Graph: Average Box Office vs Average Temperature in Los Angeles (2013-2022)
query4 = """
SELECT AVG(m.box_office) as avg_box_office, AVG(y.avg_temp) as avg_temp
FROM movies m
JOIN locations l ON l.city_name = 'Los Angeles'
JOIN yearly_data y ON l.id = y.location_id
WHERE m.year BETWEEN 2013 AND 2022 AND y.year = m.year
"""
cursor.execute(query4)
data4 = cursor.fetchone()

avg_box_office = data4[0]
avg_temp_la = data4[1]

plt.figure(figsize=(10, 6))
plt.bar(['Average Box Office', 'Average Temperature (°C)'], [avg_box_office, avg_temp_la], color=['green', 'orange'])
plt.title('Average Box Office vs Average Temperature in Los Angeles (2013-2022)')
plt.ylabel('Value')
plt.grid(axis='y')
plt.show()



# Close the database connection
conn.close()
