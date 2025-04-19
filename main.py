import sqlite3
import matplotlib.pyplot as plt

#Capital cities that match between countries-> capital and locations-> city_name
# Berlin:
# London: 
# Moscow: 
# Paris: 
# Tokyo: 

DB_NAME = "test100.db"

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

# Query to get yearly average temperature and total box office revenue for each year (2014-2022)
query4 = """
SELECT y.year, AVG(y.avg_temp) as avg_temp, SUM(CAST(REPLACE(m.box_office, '$', '') AS REAL)) as total_box_office
FROM yearly_data y
LEFT JOIN movies m ON y.year = m.year
WHERE y.year BETWEEN 2014 AND 2022 AND y.location_id = 10
GROUP BY y.year
ORDER BY y.year
"""
cursor.execute(query4)
data4 = cursor.fetchall()

# Extract data for plotting
years = [row[0] for row in data4]
avg_temps = [row[1] for row in data4]
total_box_offices = [row[2] for row in data4]

# Create a plot graph with two y-axes
fig, ax1 = plt.subplots(figsize=(12, 6))

# Plot average temperature on the first y-axis
ax1.plot(years, avg_temps, marker='o', color='red', label='Average Temperature (°C)')
ax1.set_xlabel('Year')
ax1.set_ylabel('Average Temperature (°C)', color='red')
ax1.tick_params(axis='y', labelcolor='red')
ax1.grid(True)

# Create a second y-axis for total box office revenue
ax2 = ax1.twinx()
ax2.plot(years, total_box_offices, marker='o', color='blue', label='Total Box Office Revenue ($)')
ax2.set_ylabel('Total Box Office Revenue ($)', color='blue')
ax2.tick_params(axis='y', labelcolor='blue')

# Add a title and show the plot
plt.title('Yearly Average Temperature vs Total Box Office Revenue (2014-2022)')
fig.tight_layout()
plt.show()

# Create a scatter plot
avg_temps = [row[1] for row in data4]  # Use average temperatures as x-axis
total_box_offices = [row[2] for row in data4]  # Use total box office revenue as y-axis

plt.figure(figsize=(12, 6))
plt.scatter(avg_temps, total_box_offices, color='purple', marker='o')
plt.title('Total Box Office Revenue vs Average Temperature (2014-2022)')
plt.xlabel('Average Temperature (°C)')
plt.ylabel('Total Box Office Revenue ($)')
plt.grid(True)
plt.show()

# Close the database connection
conn.close()
