import sqlite3

conn = sqlite3.connect("face_index.db")
cursor = conn.cursor()

cursor.execute("""
SELECT filename, COUNT(*)
FROM faces
GROUP BY filename
HAVING COUNT(*) > 1
ORDER BY COUNT(*) DESC
LIMIT 20
""")

rows = cursor.fetchall()

for row in rows:
    print(row)

conn.close()