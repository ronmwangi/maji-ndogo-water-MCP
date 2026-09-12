import sqlite3

conn = sqlite3.connect("maji_ndogo.db")
cur = conn.cursor()

print("--- type_of_water_source values ---")
for row in cur.execute(
    "SELECT type_of_water_source, COUNT(*) FROM water_source GROUP BY type_of_water_source ORDER BY COUNT(*) DESC"
):
    print(row)

print("\n--- province_name values ---")
for row in cur.execute(
    "SELECT province_name, COUNT(*) FROM location GROUP BY province_name ORDER BY COUNT(*) DESC"
):
    print(row)

print("\n--- well_pollution.results values ---")
for row in cur.execute(
    "SELECT results, COUNT(*) FROM well_pollution GROUP BY results ORDER BY COUNT(*) DESC"
):
    print(row)

conn.close()