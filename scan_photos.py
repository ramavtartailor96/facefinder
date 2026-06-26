import os
import cv2

photo_folder = "photos"

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades +
    "haarcascade_frontalface_default.xml"
)

print("\nScanning photos...\n")

for filename in os.listdir(photo_folder):

    if filename.lower().endswith(
        (".jpg", ".jpeg", ".png")
    ):

        path = os.path.join(
            photo_folder,
            filename
        )

        image = cv2.imread(path)

        if image is None:
            continue

        gray = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY
        )

        faces = face_cascade.detectMultiScale(
    gray,
    scaleFactor=1.2,
    minNeighbors=8,
    minSize=(80, 80)
)

        print(
            f"{filename} --> {len(faces)} face(s)"
        )