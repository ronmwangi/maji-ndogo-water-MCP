import re
import sqlite3
import pathlib

SQL_DUMP = pathlib.Path("data/Maji_Ndogo_Part_1/md_water_services.sql")
DB_OUT = pathlib.Path("maji_ndogo.db")

# Read SQL dump
text = SQL_DUMP.read_text(encoding="utf-8", errors="ignore")

# --------------------------------------------------
# Remove MySQL-specific syntax
# --------------------------------------------------

# Remove MySQL conditional comments
text = re.sub(r"/\*!.*?\*/", "", text, flags=re.DOTALL)

# Remove LOCK / UNLOCK TABLES
text = re.sub(
    r"^(LOCK|UNLOCK) TABLES.*?;$",
    "",
    text,
    flags=re.MULTILINE | re.IGNORECASE
)

# Remove ENGINE=...
text = re.sub(
    r"ENGINE=\w+.*?;",
    ";",
    text,
    flags=re.IGNORECASE | re.DOTALL
)

# Remove AUTO_INCREMENT
text = re.sub(
    r"\s+AUTO_INCREMENT\b",
    "",
    text,
    flags=re.IGNORECASE
)

# Remove UNSIGNED
text = re.sub(
    r"\s+UNSIGNED\b",
    "",
    text,
    flags=re.IGNORECASE
)

# Remove MySQL KEY definitions
text = re.sub(
    r",\s*KEY\s+`[^`]+`\s*\([^)]*\)",
    "",
    text,
    flags=re.IGNORECASE
)

# Remove CHARACTER SET
text = re.sub(
    r"CHARACTER\s+SET\s+\w+",
    "",
    text,
    flags=re.IGNORECASE
)

# Remove COLLATE
text = re.sub(
    r"COLLATE\s+\w+",
    "",
    text,
    flags=re.IGNORECASE
)

# --------------------------------------------------
# Remove MySQL database commands
# --------------------------------------------------

text = re.sub(
    r"^(DROP|CREATE)\s+DATABASE.*?;",
    "",
    text,
    flags=re.MULTILINE | re.IGNORECASE
)

text = re.sub(
    r"^USE\s+`[^`]+`\s*;?",
    "",
    text,
    flags=re.MULTILINE | re.IGNORECASE
)

# --------------------------------------------------
# Convert MySQL escaping to SQLite
# --------------------------------------------------

# MySQL: 'N\'Djamena'
# SQLite: 'N''Djamena'
text = text.replace("\\'", "''")

# Remove MySQL backticks
text = text.replace("`", "")

# --------------------------------------------------
# Create fresh SQLite database
# --------------------------------------------------

if DB_OUT.exists():
    DB_OUT.unlink()

conn = sqlite3.connect(DB_OUT)
cur = conn.cursor()

# Split SQL statements
statements = [
    s.strip()
    for s in text.split(";")
    if s.strip()
    and not s.strip().startswith("--")
]

errors = []

# --------------------------------------------------
# Execute statements
# --------------------------------------------------

for stmt in statements:
    try:
        cur.execute(stmt)
    except sqlite3.Error as e:
        errors.append((str(e), stmt[:200]))

conn.commit()
conn.close()

# --------------------------------------------------
# Report results
# --------------------------------------------------

print(
    f"Done. {len(statements)} statements processed, "
    f"{len(errors)} failed."
)

if errors:
    print("\nFailed statements:")
    for err, stmt in errors[:20]:
        print(f" - {err} | {stmt}")
else:
    print("All statements imported successfully!")