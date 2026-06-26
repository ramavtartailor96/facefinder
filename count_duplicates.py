# count_duplicates.py

import sqlite3

conn = sqlite3.connect("face_index.db")
cursor = conn.cursor()

cursor.execute("""
SELECT filename, COUNT(*)
FROM faces
GROUP BY filename
HAVING COUNT(*) > 1
""")

rows = cursor.fetchall()

print("Duplicate filenames found:", len(rows))

for row in rows[:20]:
    print(row)

conn.close()