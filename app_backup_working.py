from PIL import Image, ImageTk
from tkinter import ttk
import shutil
import numpy as np
import cv2
from insightface.app import FaceAnalysis
from tkinter import filedialog
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import messagebox
import sqlite3
import os
if not os.path.exists("selfies"):
    os.makedirs("selfies")
    
app_face = FaceAnalysis()
app_face.prepare(ctx_id=0)

# Create database
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    selfie_taken INTEGER DEFAULT 0
)
""")

conn.commit()


# Register User
def register():
    username = user_entry.get()
    password = pass_entry.get()

    if username == "" or password == "":
        messagebox.showerror("Error", "Enter username and password")
        return

    try:
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password)
        )

        conn.commit()

        messagebox.showinfo(
            "Success",
            "User Registered Successfully"
        )

    except:
        messagebox.showerror(
            "Error",
            "User already exists"
        )

import cv2

def capture_selfie(username):

    import cv2
    from tkinter import messagebox

    cam = cv2.VideoCapture(0)

    while True:

        ret, frame = cam.read()

        cv2.imshow(
            "Press SPACE to Capture",
            frame
        )

        key = cv2.waitKey(1)

        if key == 32:

            gray = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2GRAY
            )

            face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades +
                "haarcascade_frontalface_default.xml"
            )

            faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5
            )

            if len(faces) != 1:

                messagebox.showerror(
                    "Error",
                    f"Expected 1 face, found {len(faces)}"
                )

                continue

            filename = f"selfies/{username}.jpg"

            cv2.imwrite(
                filename,
                frame
            )

            break

    cam.release()
    cv2.destroyAllWindows()

    messagebox.showinfo(
        "Success",
        "Selfie Saved Successfully"
    )
def open_dashboard(username):

    dashboard = tk.Toplevel()

    dashboard.title("Face Finder")

    dashboard.geometry("400x200")

    tk.Label(
        dashboard,
        text=f"Welcome {username}"
    ).pack(pady=20)

    tk.Button(
    dashboard,
    text="Search My Photos",
    width=20,
    command=lambda:
        search_database(username)
).pack(pady=10)
        
        
def show_results():

    result_window = tk.Toplevel()

    result_window.title("Matching Photos")

    result_window.geometry("1200x800")

    canvas = tk.Canvas(result_window)

    scrollbar = tk.Scrollbar(
        result_window,
        orient="vertical",
        command=canvas.yview
    )

    canvas.configure(
        yscrollcommand=scrollbar.set
    )

    scrollbar.pack(
        side="right",
        fill="y"
    )

    canvas.pack(
        side="left",
        fill="both",
        expand=True
    )

    frame = tk.Frame(canvas)

    canvas.create_window(
        (0, 0),
        window=frame,
        anchor="nw"
    )

    frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    thumbnails = []

    files = os.listdir("results")

    row = 0
    col = 0

    for filename in files:

        path = os.path.join(
            "results",
            filename
        )

        try:

            img = Image.open(path)

            img.thumbnail((220, 220))

            photo = ImageTk.PhotoImage(img)

            thumbnails.append(photo)

            photo_frame = tk.Frame(
                frame,
                bd=2,
                relief="ridge"
            )

            photo_frame.grid(
                row=row,
                column=col,
                padx=10,
                pady=10
            )

            lbl = tk.Label(
                photo_frame,
                image=photo,
                cursor="hand2"
            )

            lbl.pack()

            tk.Label(
                photo_frame,
                text=filename,
                wraplength=220
            ).pack()

            lbl.bind(
                "<Button-1>",
                lambda e, p=path:
                    os.startfile(p)
            )

            col += 1

            if col >= 4:
                col = 0
                row += 1

        except Exception as ex:
            print(ex)

    result_window.thumbnails = thumbnails
        



def scan_folder(username, folder):

    progress_window = tk.Toplevel()

    progress_window.title("Scanning Photos")
    progress_window.geometry("400x120")

    status_label = tk.Label(
        progress_window,
        text="Preparing..."
    )
    status_label.pack(pady=10)

    progress = ttk.Progressbar(
        progress_window,
        orient="horizontal",
        length=350,
        mode="determinate"
    )
    progress.pack(pady=10)

    selfie_path = f"selfies/{username}.jpg"

    img = cv2.imread(selfie_path)

    faces = app_face.get(img)

    if len(faces) == 0:

        progress_window.destroy()

        messagebox.showerror(
            "Error",
            "No face found in selfie"
        )
        return

    selfie_embedding = faces[0].embedding

    os.makedirs("results", exist_ok=True)

    for file in os.listdir("results"):
        try:
            os.remove(
                os.path.join(
                    "results",
                    file
                )
            )
        except:
            pass

    photo_files = [
        f for f in os.listdir(folder)
        if f.lower().endswith(
            (".jpg", ".jpeg", ".png")
        )
    ]

    total_photos = len(photo_files)

    progress["maximum"] = total_photos

    current_photo = 0
    matches = 0

    for filename in photo_files:

        current_photo += 1

        progress["value"] = current_photo

        status_label.config(
            text=f"Scanning {current_photo}/{total_photos}"
        )

        progress_window.update()

        path = os.path.join(
            folder,
            filename
        )

        image = cv2.imread(path)

        if image is None:
            continue

        detected_faces = app_face.get(image)

        best_similarity = 0

        for face in detected_faces:

            similarity = np.dot(
                selfie_embedding,
                face.embedding
            ) / (
                np.linalg.norm(selfie_embedding)
                * np.linalg.norm(face.embedding)
            )

            best_similarity = max(
                best_similarity,
                similarity
            )

        if best_similarity > 0.45:

            matches += 1

            shutil.copy2(
                path,
                os.path.join(
                    "results",
                    filename
                )
            )

    progress_window.destroy()

    messagebox.showinfo(
        "Scan Complete",
        f"{matches} matching photos found."
    )

    show_results()
def search_database(username):

    import sqlite3
    import pickle

    selfie_path = f"selfies/{username}.jpg"

    img = cv2.imread(selfie_path)

    faces = app_face.get(img)

    if len(faces) == 0:

        messagebox.showerror(
            "Error",
            "No face found in selfie"
        )

        return

    selfie_embedding = faces[0].embedding

    os.makedirs(
        "results",
        exist_ok=True
    )

    # clear old results

    for file in os.listdir("results"):

        try:
            os.remove(
                os.path.join(
                    "results",
                    file
                )
            )
        except:
            pass

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

            try:

                shutil.copy2(
                    filepath,
                    os.path.join(
                        "results",
                        filename
                    )
                )

            except:
                pass

    conn.close()

    messagebox.showinfo(
        "Search Complete",
        f"{matches} matching photos found."
    )

    show_results()
        
# Login User
def login():

    username = user_entry.get()
    password = pass_entry.get()

    cursor.execute(
        """
        SELECT * FROM users
        WHERE username=? AND password=?
        """,
        (username, password)
    )

    user = cursor.fetchone()

    if user:

        selfie_taken = user[3]

        if selfie_taken == 0:

            messagebox.showinfo(
                "First Login",
                "Please capture your selfie"
            )

            capture_selfie(username)

            cursor.execute(
                """
                UPDATE users
                SET selfie_taken=1
                WHERE username=?
                """,
                (username,)
            )

            conn.commit()

            open_dashboard(username)

        else:

            messagebox.showinfo(
                "Welcome",
                f"Welcome back {username}"
            )

            open_dashboard(username)

    else:

        messagebox.showerror(
            "Error",
            "Invalid username or password"
        )        


# UI
root = tk.Tk()
root.title("Face Finder Login")
root.geometry("400x300")

tk.Label(root, text="User ID").pack(pady=5)

user_entry = tk.Entry(root, width=30)
user_entry.pack()

tk.Label(root, text="Password").pack(pady=5)

pass_entry = tk.Entry(root, width=30, show="*")
pass_entry.pack()

tk.Button(
    root,
    text="Register",
    command=register
).pack(pady=10)

tk.Button(
    root,
    text="Login",
    command=login
).pack(pady=10)

root.mainloop()