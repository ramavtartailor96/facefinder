import sqlite3

conn = sqlite3.connect("face_index.db")
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(faces)")
for row in cursor.fetchall():
    print(row)

conn.close()