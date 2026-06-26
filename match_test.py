import cv2
import numpy as np
from insightface.app import FaceAnalysis

# Load InsightFace model
app = FaceAnalysis()
app.prepare(ctx_id=0)

# -------------------------
# SELFIE IMAGE
# -------------------------
selfie_path = "selfies/ram.jpg"

img1 = cv2.imread(selfie_path)

faces1 = app.get(img1)

if len(faces1) == 0:
    print("No face found in selfie!")
    exit()

selfie_embedding = faces1[0].embedding

# -------------------------
# PHOTO TO CHECK
# -------------------------
photo_path = "photos/DSC02578.JPG"

img2 = cv2.imread(photo_path)

faces2 = app.get(img2)

if len(faces2) == 0:
    print("No face found in photo!")
    exit()

best_similarity = 0

for face in faces2:

    embedding = face.embedding

    similarity = np.dot(
        selfie_embedding,
        embedding
    ) / (
        np.linalg.norm(selfie_embedding)
        * np.linalg.norm(embedding)
    )

    if similarity > best_similarity:
        best_similarity = similarity

print(f"Similarity Score: {best_similarity:.3f}")

if best_similarity > 0.45:
    print("MATCH FOUND")
else:
    print("NO MATCH")