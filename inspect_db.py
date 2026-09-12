import sqlite3

conn = sqlite3.connect("maji_ndogo.db")
cur = conn.cursor()

tables = cur.execute(
    "SELECT name FROM sqlite_master WHERE type='table'"
).fetchall()

for (table_name,) in tables:
    print(f"\n=== {table_name} ===")
    cols = cur.execute(f"PRAGMA table_info({table_name})").fetchall()
    for col in cols:
        print(f"  {col[1]} ({col[2]})")
    count = cur.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    print(f"  rows: {count}")

conn.close()