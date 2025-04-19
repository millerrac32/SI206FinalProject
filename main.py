import sqlite3
import numpy as np
import matplotlib.pyplot as plt

DB_NAME = "test100.db"

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()
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

plt.figure(figsize=(12, 8))
scatter = plt.scatter(populations, avg_temps, c=avg_temps, cmap='viridis', s=100, edgecolor='k', alpha=0.8)
plt.title('Average Temperature vs Population for Capital Cities', fontsize=16, fontweight='bold')
plt.xlabel('Population', fontsize=14)
plt.ylabel('Average Temperature (°C)', fontsize=14)
plt.colorbar(scatter, label='Average Temperature (°C)')
plt.grid(True, linestyle='--', alpha=0.7)

for i, capital in enumerate(capitals):
    plt.annotate(capital, (populations[i], avg_temps[i]), fontsize=10, ha='right', alpha=0.7)

plt.show()

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

latitudes_np = np.array(latitudes)
avg_temps_lat_np = np.array(avg_temps_lat)

left_mask = latitudes_np < 0
right_mask = latitudes_np >= 0

if np.any(left_mask):
    left_fit = np.polyfit(latitudes_np[left_mask], avg_temps_lat_np[left_mask], 1)
    left_line = np.poly1d(left_fit)
    plt.plot(latitudes_np[left_mask], left_line(latitudes_np[left_mask]), color='blue', label='Best Fit (Left)')
    plt.text(-40, left_line(-40), f"y = {left_fit[0]:.2f}x + {left_fit[1]:.2f}", 
             color='blue', fontsize=10, ha='center', bbox=dict(facecolor='white', alpha=0.5))

if np.any(right_mask):
    right_fit = np.polyfit(latitudes_np[right_mask], avg_temps_lat_np[right_mask], 1)
    right_line = np.poly1d(right_fit)
    plt.plot(latitudes_np[right_mask], right_line(latitudes_np[right_mask]), color='green', label='Best Fit (Right)')
    plt.text(40, right_line(40), f"y = {right_fit[0]:.2f}x + {right_fit[1]:.2f}", 
             color='green', fontsize=10, ha='center', bbox=dict(facecolor='white', alpha=0.5))

plt.title('Latitude vs Average Temperature')
plt.xlabel('Latitude')
plt.ylabel('Average Temperature (°C)')
plt.legend()
plt.grid(True)
plt.show()

query4 = """
SELECT y.year, AVG(y.avg_temp) as avg_temp, SUM(m.box_office) as total_box_office
FROM yearly_data y
LEFT JOIN movies m ON y.year = m.year
WHERE y.year BETWEEN 2014 AND 2022 AND y.location_id = 10
GROUP BY y.year
ORDER BY y.year
"""
cursor.execute(query4)
data4 = cursor.fetchall()
years = [row[0] for row in data4]
avg_temps = [row[1] for row in data4]
total_box_offices = [row[2] for row in data4]
fig, ax1 = plt.subplots(figsize=(12, 6))
ax1.plot(years, avg_temps, marker='o', color='red', label='Average Temperature (°C)', linewidth=2)
ax1.set_xlabel('Year', fontsize=14)
ax1.set_ylabel('Average Temperature (°C)', color='red', fontsize=14)
ax1.tick_params(axis='y', labelcolor='red')
ax1.grid(True, linestyle='--', alpha=0.7)

ax2 = ax1.twinx()
ax2.plot(years, total_box_offices, marker='o', color='blue', label='Total Box Office Revenue ($)', linewidth=2)
ax2.set_ylabel('Total Box Office Revenue ($)', color='blue', fontsize=14)
ax2.tick_params(axis='y', labelcolor='blue')
plt.title('Yearly Average Temperature vs Total Box Office Revenue (2014-2022)', fontsize=16, fontweight='bold')
fig.tight_layout()

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=12)

plt.show()
plt.figure(figsize=(12, 6))
scatter = plt.scatter(avg_temps, total_box_offices, c=avg_temps, cmap='plasma', s=150, edgecolor='k', alpha=0.8)
plt.title('Total Box Office Revenue vs Average Temperature (2014-2022)', fontsize=16, fontweight='bold')
plt.xlabel('Average Temperature (°C)', fontsize=14)
plt.ylabel('Total Box Office Revenue ($)', fontsize=14)
plt.colorbar(scatter, label='Average Temperature (°C)')
plt.grid(True, linestyle='--', alpha=0.7)
for i, year in enumerate(years):
    plt.annotate(year, (avg_temps[i], total_box_offices[i]), fontsize=10, ha='right', alpha=0.7)

plt.show()

query5 = """
SELECT country_name, population
FROM countries
ORDER BY population DESC
LIMIT 10
"""
cursor.execute(query5)
data5 = cursor.fetchall()
countries = [row[0] for row in data5]
populations = [row[1] for row in data5]

plt.figure(figsize=(14, 8))
bars = plt.barh(countries, populations, color='skyblue', edgecolor='black')
plt.title('Top 10 Countries with the Most Population', fontsize=18, fontweight='bold', pad=20)
plt.xlabel('Population', fontsize=14, labelpad=10)
plt.ylabel('Country', fontsize=14, labelpad=10)
plt.gca().invert_yaxis()
plt.grid(axis='x', linestyle='--', alpha=0.7)

for bar in bars:
    plt.text(bar.get_width() + 0.02 * max(populations), bar.get_y() + bar.get_height() / 2,
             f'{int(bar.get_width()):,}', va='center', fontsize=12, color='black')

plt.tight_layout()

plt.show()
conn.close()
