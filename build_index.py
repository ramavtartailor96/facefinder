import os
import cv2
import sqlite3
import pickle
from insightface.app import FaceAnalysis

# ------------------------
# Load InsightFace
# ------------------------

app = FaceAnalysis()
app.prepare(ctx_id=0)

# ------------------------
# Database
# ------------------------

conn = sqlite3.connect("face_index.db")

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS faces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT,
    filepath TEXT,
    embedding BLOB
)
""")

conn.commit()

# ------------------------
# Select Folder
# ------------------------

folder = input(
    "Enter photo folder path: "
)

if not os.path.exists(folder):

    print("Folder not found")
    exit()

# ------------------------
# Scan Photos
# ------------------------

photo_files = []

for file in os.listdir(folder):

    if file.lower().endswith(
        (".jpg", ".jpeg", ".png")
    ):
        photo_files.append(file)

total = len(photo_files)

print(f"\nFound {total} photos\n")

count = 0

for filename in photo_files:

    count += 1

    filepath = os.path.join(
        folder,
        filename
    )

    print(
        f"[{count}/{total}] "
        f"{filename}"
    )

    image = cv2.imread(filepath)

    if image is None:
        continue

    try:

        faces = app.get(image)

        for face in faces:

            embedding = pickle.dumps(
                face.embedding
            )

            cursor.execute(
                """
                INSERT INTO faces
                (
                    filename,
                    filepath,
                    embedding
                )
                VALUES (?, ?, ?)
                """,
                (
                    filename,
                    filepath,
                    embedding
                )
            )

    except Exception as ex:

        print(
            f"Error: {filename}"
        )

conn.commit()

conn.close()

print(
    "\nIndexing Complete!"
)