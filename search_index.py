import cv2
import sqlite3
import pickle
import numpy as np
import shutil
import os

from insightface.app import FaceAnalysis

# ------------------------
# Load AI Model
# ------------------------

app = FaceAnalysis()
app.prepare(ctx_id=0)

# ------------------------
# Selfie
# ------------------------

selfie_path = "selfies/RAM.jpg"

img = cv2.imread(selfie_path)

faces = app.get(img)

if len(faces) == 0:

    print("No face found in selfie")
    exit()

selfie_embedding = faces[0].embedding

# ------------------------
# Results Folder
# ------------------------

os.makedirs("results_db", exist_ok=True)

# Clear old results

for file in os.listdir("results_db"):

    os.remove(
        os.path.join(
            "results_db",
            file
        )
    )

# ------------------------
# Open Database
# ------------------------

conn = sqlite3.connect(
    "face_index.db"
)

cursor = conn.cursor()

cursor.execute(
    """
    SELECT filename,
           filepath,
           embedding
    FROM faces
    """
)

rows = cursor.fetchall()

matches = 0

# ------------------------
# Compare Faces
# ------------------------

for row in rows:

    filename = row[0]
    filepath = row[1]

    embedding = pickle.loads(
        row[2]
    )

    similarity = np.dot(
        selfie_embedding,
        embedding
    ) / (
        np.linalg.norm(selfie_embedding)
        * np.linalg.norm(embedding)
    )

    if similarity > 0.45:

        matches += 1

        print(
            f"MATCH: {filename} "
            f"Score={similarity:.3f}"
        )

        try:

            shutil.copy2(
                filepath,
                os.path.join(
                    "results_db",
                    filename
                )
            )

        except:
            pass

conn.close()

print(
    f"\nTotal Matches: {matches}"
)