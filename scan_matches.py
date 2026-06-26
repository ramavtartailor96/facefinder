import shutil
import os
import cv2
import numpy as np
from insightface.app import FaceAnalysis
photo_folder = "photos"
os.makedirs("results", exist_ok=True)

# Load AI model
app = FaceAnalysis()
app.prepare(ctx_id=0)

# Your selfie
selfie_path = "selfies/ram.jpg"

img = cv2.imread(selfie_path)

faces = app.get(img)

if len(faces) == 0:
    print("No face found in selfie")
    exit()

selfie_embedding = faces[0].embedding

# Folder containing photos
photo_folder = "photos"

print("\nScanning photos...\n")

for filename in os.listdir(photo_folder):

    if not filename.lower().endswith(
        (".jpg", ".jpeg", ".png")
    ):
        continue

    path = os.path.join(
        photo_folder,
        filename
    )

    image = cv2.imread(path)

    if image is None:
        continue

    detected_faces = app.get(image)

    best_similarity = 0

    for face in detected_faces:

        similarity = np.dot(
            selfie_embedding,
            face.embedding
        ) / (
            np.linalg.norm(selfie_embedding)
            * np.linalg.norm(face.embedding)
        )

        if similarity > best_similarity:
            best_similarity = similarity

    if best_similarity > 0.45:

        print(
            f"MATCH: {filename} "
            f"Score={best_similarity:.3f}"
        )

        shutil.copy2(
            path,
            os.path.join(
                "results",
                filename
            )
        )