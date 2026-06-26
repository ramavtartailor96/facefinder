print("MAIN.PY STARTED")
results_frame = None
API_URL = "http://127.0.0.1:8000"
drive_manager = None
import requests
import pickle
from drive_manager import DriveManager
from tkinter import simpledialog
import time
from pillow_heif import register_heif_opener
from PIL import Image
import numpy as np
register_heif_opener()
import sys
stop_search = False
current_results = []
current_index = 0
result_thumbnails = []
gallery_row = 0
gallery_col = 0
result_row = 0
result_col = 0
current_page = 0
photos_per_page = 50
import threading
import shutil
import numpy as np
import cv2
from insightface.app import FaceAnalysis
from tkinter import filedialog
from PIL import Image, ImageTk, ImageOps
from tkinter import messagebox
import sqlite3
import tkinter as tk
from tkinter import ttk
import os
import tempfile
if not os.path.exists("selfies"):
    os.makedirs("selfies")
    
if getattr(sys, "frozen", False):
    model_root = os.path.join(sys._MEIPASS)
else:
    model_root = os.path.join(
        os.path.expanduser("~"),
        ".insightface"
    )
app_face = FaceAnalysis(
    name="buffalo_l",
    root=model_root
)

app_face.prepare(ctx_id=0)
print("\n========== MODEL ROOT ==========")
print(model_root)
print("================================\n")
# Create database

conn = sqlite3.connect("users.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    selfie_taken INTEGER DEFAULT 0,
    role TEXT
)
""")

conn.commit()

cursor.execute(
    """
    SELECT COUNT(*)
    FROM users
    WHERE LOWER(username)='admin'
    """
)

admin_exists = cursor.fetchone()[0]

if admin_exists == 0:

    cursor.execute(
        """
        INSERT INTO users
        (
            username,
            password,
            selfie_taken,
            role
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            "ram",
            "1234",
            0,
            "admin"
        )
    )

    conn.commit()
#==================================NEW SECTION START ====================#

import tkinter as tk
from tkinter import ttk


class GoogleLoginDialog:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("Google Sign In")

        self.window.geometry("500x250")
        self.window.resizable(True, True)

        self.window.transient(parent)
        self.window.grab_set()

        ttk.Label(
            self.window,
            text="Google Drive Authentication",
            font=("Segoe UI", 16, "bold")
        ).pack(pady=(25, 10))

        ttk.Label(
            self.window,
            text="Click the button below to sign in to Google.\n"
                 "Your browser will open once.",
            justify="center"
        ).pack()

        self.status = ttk.Label(
            self.window,
            text="Waiting...",
            foreground="blue"
        )

        self.status.pack(pady=20)

        self.button = ttk.Button(
            self.window,
            text="Continue with Google",
            command=self.start_login
        )

        self.button.pack()

    def start_login(self):
        self.button.config(state="disabled")
        self.status.config(text="Waiting for authentication...")

        self.window.after(
            100,
            self.authenticate
        )

    def authenticate(self):
        from google_auth import get_drive

        try:
            get_drive()

            self.status.config(text="Authentication successful!")

            self.window.after(
                700,
                self.window.destroy
            )

        except Exception as e:
            self.status.config(text=str(e))
            self.button.config(state="normal")
            

#==================================NEW SECTION END===================================

# Register User

def register():

    username = user_entry.get()
    password = pass_entry.get()

    if username == "" or password == "":

        messagebox.showerror(
            "Error",
            "Enter username and password"
        )
        return

    try:

        response = requests.post(
            f"{API_URL}/register",
            json={
                "username": username,
                "password": password
            }
        )

        data = response.json()

    except Exception as e:

        messagebox.showerror(
            "Server Error",
            str(e)
        )
        return

    if data["success"]:

        messagebox.showinfo(
            "Success",
            data["message"]
        )

    else:

        messagebox.showerror(
            "Error",
            data["message"]
        )

def test_server():
    try:
        response = requests.get(f"{API_URL}/")
        print(response.json())
    except Exception as e:
        print("Server not running:", e)


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

def create_progress_window():

    progress_window = tk.Toplevel()

    progress_window.title("Building Face Index")

    progress_window.geometry("450x180")

    tk.Label(
        progress_window,
        text="Indexing Photos...",
        font=("Arial", 12)
    ).pack(pady=10)

    status_label = tk.Label(
        progress_window,
        text="Starting..."
    )

    status_label.pack()

    progress_bar = ttk.Progressbar(
        progress_window,
        orient="horizontal",
        length=350,
        mode="determinate"
    )

    progress_bar.pack(pady=15)

    percent_label = tk.Label(
        progress_window,
        text="0%"
    )

    percent_label.pack()

    return (
        progress_window,
        status_label,
        progress_bar,
        percent_label
    )
    
def select_drive_folder(folders):

    folder_window = tk.Toplevel()
    folder_window.title("Google Drive Folders")
    folder_window.geometry("500x500")

    selected = {"folder": None}

    listbox = tk.Listbox(
        folder_window,
        font=("Segoe UI", 11)
    )

    listbox.pack(
        fill="both",
        expand=True,
        padx=10,
        pady=10
    )

    for folder in folders:
        listbox.insert(
            tk.END,
            folder["title"]
        )

    def choose():

        selection = listbox.curselection()

        if not selection:
            return

        selected["folder"] = folders[
            selection[0]
        ]

        folder_window.destroy()

    tk.Button(
        folder_window,
        text="Select Folder",
        command=choose
    ).pack(pady=10)

    folder_window.grab_set()
    folder_window.wait_window()

    return selected["folder"]

def show_drive_folders(folders):

    global results_frame
    global drive_folder_table

    for widget in results_frame.winfo_children():
        widget.destroy()
        
    table_frame = tk.Frame(results_frame)
    table_frame.pack(fill="both", expand=True, padx=20, pady=20)

    drive_folder_table = ttk.Treeview(
        table_frame,
        columns=("sr", "folder"),
        show="headings",
        height=15
    )
    scrollbar = ttk.Scrollbar(
    table_frame,
    orient="vertical",
    command=drive_folder_table.yview
    )

    drive_folder_table.configure(
        yscrollcommand=scrollbar.set
    )

    scrollbar.pack(side="right", fill="y")
    drive_folder_table.pack(side="left", fill="both", expand=True)

    drive_folder_table.heading(
        "sr",
        text="Sr No"
    )

    drive_folder_table.heading(
        "folder",
        text="Folder Name"
    )

    drive_folder_table.column(
        "sr",
        width=80,
        anchor="center"
    )

    drive_folder_table.column(
        "folder",
        width=600
    )

    drive_folder_table.pack(
    fill="both",
    expand=True
)
    
    
   
    
    for i, folder in enumerate(folders, 1):

        drive_folder_table.insert(
            "",
            "end",
            values=(
                i,
                folder["title"]
            )
        )
    global drive_folders_cache

    drive_folders_cache = folders

def start_drive_indexing(
        selected_folder,
        progress_window,
        status_label,
        progress_bar,
        percent_label):

    global result_count_label

    result_count_label.config(
        text=f"☁️ Indexing : {selected_folder['title']}"
    )

    global drive_manager

    drive = drive_manager
    print("drive_manager =", drive_manager)
    
    progress_window.after(
    0,
    lambda: status_label.config(
        text="Checking Google Drive..."
        )
    )
    
    import tempfile
    import os

    images = drive.list_images(
        selected_folder["id"]
    )
    total_images = len(images)
    processed = 0

    print(
        f"Found {len(images)} images"
    )

    temp_folder = os.path.join(
        "photos",
        "GoogleDrive"
    )

    os.makedirs(
        temp_folder,
        exist_ok=True
    )

    failed = 0
    
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
    
    for image in images:
        processed += 1

        percent = int((processed / total_images) * 100)

        progress_window.after(
            0,
            lambda p=percent,
                proc=processed,
                total=total_images:
                update_progress(
                    progress_bar,
                    percent_label,
                    status_label,
                    p,
                    proc,
                    total
                )
        )
        cursor.execute(
            "SELECT 1 FROM faces WHERE filename = ?",
            (image["title"],)
        )

        if cursor.fetchone():
            print(f"Skipping already indexed: {image['title']}")
            continue
        
        print(
            "Downloading:",
            image["title"]
        )

        save_path = os.path.join(
            temp_folder,
            image["title"]
        )
        if os.path.exists(save_path):
            print(
                f"Already downloaded: {image['title']}"
            )
            continue

        success = drive.download_file(
            image["id"],
            save_path
        )
        

        if not success:
            failed += 1

    print(
        f"Download complete. Failed: {failed}"
    )
    progress_window.after(
    0,
    lambda: status_label.config(
        text="Indexing downloaded photos..."
        )
    )
    
    folder = temp_folder

    conn.close()
    
    process_folder(
    folder,
    progress_window,
    status_label,
    progress_bar,
    percent_label
)
    

    print("START INDEXING SECTION")

def start_selected_drive_folder():

    global drive_folder_table
    global drive_folders_cache

    selected = drive_folder_table.selection()

    if not selected:
        messagebox.showwarning(
            "Select Folder",
            "Please select a folder first."
        )
        return

    item = drive_folder_table.item(selected[0])

    sr_no = item["values"][0]

    folder = drive_folders_cache[sr_no - 1]

    print("Selected Folder:", folder["title"])

    progress_window, status_label, progress_bar, percent_label = create_progress_window()

    threading.Thread(
        target=start_drive_indexing,
        args=(
            folder,
            progress_window,
            status_label,
            progress_bar,
            percent_label
        ),
        daemon=True
    ).start()
    
def update_progress(progress_bar,
                    percent_label,
                    status_label,
                    percent,
                    processed,
                    total):

    progress_bar["value"] = percent

    percent_label.config(
        text=f"{percent}%"
    )

    status_label.config(
        text=f"Processing {processed}/{total}"
    )

def process_folder(
        folder,
        progress_window,
        status_label,
        progress_bar,
        percent_label):

    conn = sqlite3.connect(
        "face_index.db"
    )

    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS faces (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT,
        filepath TEXT ,
        embedding BLOB
    )
    """)

    conn.commit()

    photo_count = 0
    skipped_count = 0


    total_photos = len([
        f for f in os.listdir(folder)
        if f.lower().endswith(
            (".jpg", ".jpeg", ".png", ".heic")
        )
    ])

    processed = 0

    for filename in os.listdir(folder):

        processed += 1

        percent = int(
            (processed / total_photos) * 100
        )

        progress_window.after(
            0,
            lambda p=percent,
                proc=processed,
                total=total_photos: update_progress(
                        progress_bar,
                        percent_label,
                        status_label,
                        p,
                        proc,
                        total
                )
        )

        if not filename.lower().endswith(
            (".jpg", ".jpeg", ".png", ".heic")
        ):
            continue

        filepath = os.path.join(
            folder,
            filename
        )

        # Skip already indexed photos
        cursor.execute(
            """
            SELECT filename
            FROM faces
            WHERE filename=?
            """,
            (filename,)
        )

        existing = cursor.fetchone()

        if existing:
            skipped_count += 1
            print(f"Skipping: {filename}")
            continue

        try:

            if filepath.lower().endswith(".heic"):

                pil_image = Image.open(filepath)

                image = cv2.cvtColor(
                    np.array(pil_image),
                    cv2.COLOR_RGB2BGR
                )

            else:

                image = cv2.imread(filepath)

            if image is None:
                print(
                    f"FAILED TO LOAD IMAGE -> {filepath}"
                )
                continue

        except Exception as e:

            print(
                f"FAILED TO LOAD IMAGE -> {filepath}"
            )

            print(e)

            continue

        height, width = image.shape[:2]

        if width > 1200:

            scale = 1200 / width

            image = cv2.resize(
                image,
                None,
                fx=scale,
                fy=scale
            )

        try:

            try:
                try:
                    faces = app_face.get(image)
                except Exception as e:
                    print(f"Face detection failed: {filename}")
                    print(e)
                    continue
                print(f"\nProcessing: {filename}")
            except Exception as ex:
                print(f"Skipping {filename}: {ex}")
                continue

            print(f"{filename} -> Faces found: {len(faces)}")

            if len(faces) > 0:

                face = faces[0]

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
            conn.commit()

            photo_count += 1

            print(
                f"Indexed: {photo_count} | "
                f"Skipped: {skipped_count}"
            )

        except Exception as ex:

            import traceback

            print("\n===================")
            print(f"ERROR FILE: {filename}")
            traceback.print_exc()
            print("===================\n")

    conn.close()

    progress_window.after(
        0,
        lambda: finish_indexing(
            progress_window,
            photo_count,
            skipped_count
        )
    )
    import tempfile
    import shutil

    try:
        if folder.startswith(tempfile.gettempdir()):
            shutil.rmtree(folder, ignore_errors=True)
            print("Temporary Google Drive folder deleted.")
    except Exception as e:
        print(e)
        
    result_count_label.config(
        text="📸 Search Results "
    )

def finish_indexing(progress_window,
                    photo_count,
                    skipped_count):

    progress_window.destroy()

    result_count_label.config(
        text="✅ Index Completed"
    )

    messagebox.showinfo(
        "Index Complete",
        f"""
New photos indexed: {photo_count}

Already indexed: {skipped_count}
"""
    )

    result_count_label.config(
        text="📸 Search Results"
    )

def build_index():

    show_index_options()

def show_index_options():

    global results_frame
    global result_count_label

    result_count_label.config(
        text="📂 Build / Update Index"
    )
    # Clear right panel
    for widget in results_frame.winfo_children():
        widget.destroy()

    tk.Label(
        results_frame,
        text="Choose Index Source",
        font=("Arial", 18, "bold"),
        bg="#f8fafc",
        fg="#1e3a8a"
    ).pack(pady=(20,10))

    tk.Label(
        results_frame,
        text="Select where you want to index photos from",
        font=("Arial",12),
        bg="#f8fafc",
        fg="gray"
    ).pack(pady=(0,25))
    
    tk.Button(
        results_frame,
        text="☁️\nGoogle Drive / Cloud",
        font=("Arial", 14, "bold"),
        bg="#2563eb",
        fg="white",
        width=28,
        height=4,
        command=open_google_drive_index
    ).pack(side="left", padx=55, pady=15) # Added side="left" and adjusted padding

    tk.Button(
        results_frame,
        text="💻\nLocal Folder",
        font=("Arial", 14, "bold"),
        bg="#10b981",
        fg="white",
        width=28,
        height=4,
        command=open_local_index
    ).pack(side="left", padx=15, pady=15) # Added side="left" and adjusted padding  
    
def open_google_drive_index():

    result_count_label.config(
        text="☁️ Connecting to Google Drive..."
    )

    threading.Thread(
        target=google_drive_worker,
        daemon=True
    ).start()
    
def google_drive_worker():

    drive = DriveManager()

    global drive_manager
    drive_manager = drive

    folders = drive.list_folders()

    root.after(
        0,
        lambda: show_drive_folders(folders)
    )
    
def open_local_index():

    folder = filedialog.askdirectory()

    if folder == "":
        return

    progress_window, status_label, progress_bar, percent_label = create_progress_window()

    threading.Thread(
        target=process_folder,
        args=(
            folder,
            progress_window,
            status_label,
            progress_bar,
            percent_label
        ),
        daemon=True
    ).start()

def open_results_folder():

    os.makedirs(
        "results",
        exist_ok=True
    )

    os.startfile("results")    

def logout(dashboard):
    
    # Delete Google Drive token
    if os.path.exists("token.pickle"):
        os.remove("token.pickle")

    # Reset any cached DriveManager
    global drive_manager
    drive_manager = None
    
    dashboard.destroy()

    root.deiconify()

    root.state("zoomed")

def get_dashboard_stats():

    import sqlite3

    photos = 0
    faces = 0

    try:

        conn = sqlite3.connect(
            "face_index.db"
        )

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT COUNT(DISTINCT filepath)
            FROM faces
            """
        )

        photos = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM faces
            """
        )

        faces = cursor.fetchone()[0]

        conn.close()

    except:
        pass

    return photos, faces

def open_user_management():

    print("USER MANAGEMENT OPENED")

    import traceback

    try:

        win = tk.Toplevel()

        win.title("User Management")
        win.geometry("700x500")
        win.configure(bg="white")

        tk.Label(
            win,
            text="👥 User Management",
            font=("Arial", 18, "bold"),
            bg="white",
            fg="#1e3a8a"
        ).pack(pady=10)

        users_frame = tk.Frame(
            win,
            bg="white"
        )

        users_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=10
        )

        from tkinter import ttk

        # TABLE

        columns = (
            "sr",
            "username",
            "role"
        )

        users_table = ttk.Treeview(
            users_frame,
            columns=columns,
            show="headings",
            height=15
        )

        users_table.heading(
            "sr",
            text="Sr No."
        )

        users_table.heading(
            "username",
            text="Username"
        )

        users_table.heading(
            "role",
            text="Role"
        )

        users_table.column(
            "sr",
            width=80,
            anchor="center"
        )

        users_table.column(
            "username",
            width=250,
            anchor="center"
        )

        users_table.column(
            "role",
            width=150,
            anchor="center"
        )

        users_table.pack(
            fill="both",
            expand=True
        )

        # Alternate row colors

        users_table.tag_configure(
            "odd",
            background="#f8fafc"
        )

        users_table.tag_configure(
            "even",
            background="#e2e8f0"
        )
        response = requests.get(
            f"{API_URL}/users"
        )

        users = response.json()

        for i, (username, role) in enumerate(users, start=1):

            tag = "odd" if i % 2 else "even"

            users_table.insert(
                "",
                "end",
                values=(
                    i,
                    username,
                    role
                ),
                tags=(tag,)
            )
        
        btn_frame = tk.Frame(
            win,
            bg="white"
        )

        btn_frame.pack(pady=10)

        tk.Button(
            btn_frame,
            text="➕ Add User",
            bg="#16a34a",
            fg="white",
            font=("Arial", 10, "bold"),
            width=15,
            relief="flat",
            command=add_user_window
        ).grid(row=0, column=0, padx=10)

        tk.Button(
            btn_frame,
            text="🗑 Delete User",
            bg="#dc2626",
            fg="white",
            font=("Arial", 10, "bold"),
            width=15,
            relief="flat",
            command=lambda: delete_user(users_table)
        ).grid(row=0, column=1, padx=10)

        tk.Button(
            btn_frame,
            text="🔑 Reset Password",
            bg="#2563eb",
            fg="white",
            font=("Arial", 10, "bold"),
            width=15,
            relief="flat",
            command=lambda: reset_password(users_table)
        ).grid(row=0, column=2, padx=10)

        print("USER MANAGEMENT WINDOW READY")

    except Exception:

        print("USER MANAGEMENT ERROR")
        traceback.print_exc()
    
def add_user_window():
    print("ADD USER WINDOW OPENED")

    win = tk.Toplevel()

    win.title("Add User")
    win.geometry("350x250")

    tk.Label(win, text="Username").pack(pady=5)

    username_entry = tk.Entry(win)
    username_entry.pack()

    tk.Label(win, text="Password").pack(pady=5)

    password_entry = tk.Entry(
        win,
        show="*"
    )

    password_entry.pack()

    tk.Label(win, text="Role").pack(pady=5)

    role_var = tk.StringVar(
        value="user"
    )

    tk.OptionMenu(
        win,
        role_var,
        "user",
        "admin"
    ).pack()

    def save_user():

        username = username_entry.get()
        password = password_entry.get()
        role = role_var.get()

        try:

            response = requests.post(
                f"{API_URL}/register",
                json={
                    "username": username,
                    "password": password,
                    "role": role
                }
            )

            data = response.json()

            if data["success"]:

                messagebox.showinfo(
                    "Success",
                    "User Added"
                )

                win.destroy()

            else:

                messagebox.showerror(
                    "Error",
                    data["message"]
                )

        except Exception as e:

            messagebox.showerror(
                "Server Error",
                str(e)
            )
            
    tk.Button(
        win,
        text="Save User",
        command=save_user
    ).pack(pady=15)

def delete_user(user_table):

    selected = user_table.selection()

    if not selected:
        messagebox.showwarning(
            "Select User",
            "Please select a user"
        )
        return

    values = user_table.item(
        selected[0],
        "values"
    )

    username = values[1]

    response = requests.post(
        f"{API_URL}/delete-user",
        json={
            "username": username
        }
    )

    data = response.json()

    if data["success"]:

        user_table.delete(selected[0])

        messagebox.showinfo(
            "Deleted",
            f"{username} removed successfully"
        )

def reset_password(user_table):

    selected = user_table.selection()

    if not selected:
        messagebox.showwarning(
            "Select User",
            "Please select a user"
        )
        return

    values = user_table.item(
        selected[0],
        "values"
    )

    username = values[1]

    new_password = simpledialog.askstring(
        "Reset Password",
        f"Enter new password for {username}"
    )

    if not new_password:
        return

    response = requests.post(
        f"{API_URL}/reset-password",
        json={
            "username": username,
            "password": new_password
        }
    )

    data = response.json()

    if data["success"]:

        messagebox.showinfo(
            "Success",
            f"Password updated for {username}"
        )

    else:

        messagebox.showerror(
            "Error",
            data["message"]
        )
         
def open_dashboard(actual_username, role):
    import traceback
    traceback.print_stack()
    print("OPEN DASHBOARD ROLE =", role)
    global results_frame
    global stop_search
    stop_search = False
    global dashboard_window

    dashboard_window = tk.Toplevel()
    dashboard = dashboard_window
    
    dashboard.title("FaceFinder Dashboard")
    dashboard.state("zoomed")
    dashboard.configure(bg="#f0f4f8")

    # Logout Area

    logout_frame = tk.Frame(
        dashboard,
        bg="#f0f4f8"
    )

    logout_frame.pack(
        fill="x",
        pady=10,
        padx=20
    )

    tk.Button(
        logout_frame,
        text="Logout",
        font=("Arial", 11, "bold"),
        bg="#dc2626",
        fg="white",
        relief="flat",
        padx=15,
        pady=5,
        command=lambda: logout(dashboard)
    ).pack(side="right")

    if role.lower().strip() == "admin":

        print("ADMIN BUTTON CREATED")

        

        tk.Button(
                logout_frame,
                text="👥 User Management",
                font=("Arial", 11, "bold"),
                bg="#f59e0b",
                fg="white",
                relief="flat",
                padx=15,
                pady=5,
                command=open_user_management
            ).pack(side="right", padx=10)

    # Header

    global page_title

    page_title = tk.Label(
        dashboard,
        text="🔍 FaceFinder Dashboard",
        font=("Arial", 22, "bold"),
        bg="#f0f4f8",
        fg="#1e3a8a"
    )

    page_title.pack(pady=(20, 5))

    tk.Label(
        dashboard,
        text=f"Welcome, {actual_username}",
        font=("Arial", 12),
        bg="#f0f4f8",
        fg="gray"
    ).pack()

    # Main Card

    card = tk.Frame(
        dashboard,
        bg="white",
        bd=1,
        relief="solid"
    )

    card.pack(
        padx=40,
        pady=30,
        fill="both",
        expand=True
    )

    # Main Layout

    main_frame = tk.Frame(
        card,
        bg="white"
    )

    main_frame.pack(
        fill="both",
        expand=True,
        padx=20,
        pady=20
    )

    # LEFT SIDE

    left_frame = tk.Frame(
        main_frame,
        bg="white"
    )

    left_frame.pack(
        side="left",
        fill="y",
        padx=20,
        pady=20
    )

    # Buttons

    tk.Button(
        left_frame,
        text="📂\nBuild / Update Index",
        font=("Arial", 14, "bold"),
        bg="#2563eb",
        fg="white",
        width=20,
        height=3,
        command=build_index
    ).pack(pady=10)

    tk.Button(
        left_frame,
        text="📸\nSearch My Photos",
        font=("Arial", 14, "bold"),
        bg="#16a34a",
        fg="white",
        width=20,
        height=3,
        command=lambda: search_database(actual_username)
    ).pack(pady=10)
    
    tk.Button(
        left_frame,
        text="⛔\nStop Search",
        font=("Arial", 14, "bold"),
        bg="#dc2626",
        fg="white",
        width=20,
        height=3,
        command=stop_searching
    ).pack(pady=10)

    tk.Button(
        left_frame,
        text="📁\nOpen Results Folder",
        font=("Arial", 14, "bold"),
        width=20,
        height=3,
        command=open_results_folder
    ).pack(pady=10)
    
        
    # RIGHT SIDE

    right_frame = tk.Frame(
            main_frame,
            bg="white"
        )

    right_frame.pack(
            side="left",
            fill="both",
            expand=True,
            padx=20
        )
    
    global result_count_label

    result_count_label = tk.Label(
        right_frame,
        text="📸 Search Results (0)",
        font=("Arial", 14, "bold"),
        bg="white",
        fg="#1e3a8a"
    )
            # 1. Create the button object (and save it to a variable)
    index_button = tk.Button(
    right_frame,
    text="📁\nStart Drive Indexing",
    font=("Arial", 14, "bold"),
    bg="#16a34a",
    fg="white",
    width=18,
    height=2,
    command=start_selected_drive_folder,
    # <-- Starts disabled (greyed out)
    )
        # 2. Position it in the top-right corner
    index_button.pack(side="top", anchor="ne", padx=10, pady=10)        
    
    result_count_label.pack(pady=10)

    results_container = tk.Frame(
        right_frame,
        bg="white"
    )

    results_container.pack(
        fill="both",
        expand=True,
        padx=10,
        pady=10
    )

    results_canvas = tk.Canvas(
        results_container,
        bg="#f8fafc"
    )

    results_scrollbar = tk.Scrollbar(
        results_container,
        orient="vertical",
        command=results_canvas.yview
    )

    results_canvas.configure(
        yscrollcommand=results_scrollbar.set
    )

    results_scrollbar.pack(
        side="right",
        fill="y"
    )

    results_canvas.pack(
        side="left",
        fill="both",
        expand=True
    )

    results_frame = tk.Frame(
        results_canvas,
        bg="#f8fafc"
    )
    global drive_folder_table
    
    canvas_window = results_canvas.create_window(
        (0, 0),
        window=results_frame,
        anchor="nw"
    )

    def resize_frame(event):
        results_canvas.itemconfig(
            canvas_window,
            width=event.width
        )

    results_canvas.bind(
        "<Configure>",
        resize_frame
    )

    results_frame.bind(
        "<Configure>",
        lambda e: results_canvas.configure(
            scrollregion=results_canvas.bbox("all")
        )
    )

    def _on_mousewheel(event):
        results_canvas.yview_scroll(
            int(-1 * (event.delta / 120)),
            "units"
        )

    results_canvas.bind_all(
        "<MouseWheel>",
        _on_mousewheel
    )
    tk.Label(
        results_frame,
        text="No results loaded yet",
        font=("Arial", 12),
        bg="#f8fafc",
        fg="gray"
    ).pack(pady=50)

def preview_image(filepath):

    global current_results
    global current_index

    try:
        current_index = current_results.index(filepath)
    except:
        current_index = 0

    preview = tk.Toplevel()

    preview.title(
        os.path.basename(filepath)
    )

    preview.state("zoomed")

    preview.bind(
        "<Escape>",
        lambda e: preview.destroy()
    )

    image_label = tk.Label(
        preview,
        bg="black"
    )

    image_label.pack(
        expand=True,
        fill="both"
    )

    def show_image(index):

        path = current_results[index]

        img = Image.open(path)

        img = ImageOps.exif_transpose(img)

        screen_w = preview.winfo_screenwidth()
        screen_h = preview.winfo_screenheight()

        img.thumbnail(
            (screen_w - 100, screen_h - 100)
        )

        photo = ImageTk.PhotoImage(img)

        image_label.config(
            image=photo
        )

        image_label.image = photo

        preview.title(
            os.path.basename(path)
        )

    def next_image(event=None):

        global current_index

        if len(current_results) == 0:
            return

        current_index = (
            current_index + 1
        ) % len(current_results)

        show_image(current_index)

    def previous_image(event=None):

        global current_index

        if len(current_results) == 0:
            return

        current_index = (
            current_index - 1
        ) % len(current_results)

        show_image(current_index)

    preview.bind(
        "<Right>",
        next_image
    )

    preview.bind(
        "<Left>",
        previous_image
    )

    show_image(current_index)
    
def add_result_thumbnail(filepath):

    global results_frame
    global result_thumbnails
    global gallery_row
    global gallery_col

    print("results_frame =", results_frame)

    if results_frame:
        print(
            "results_frame children =",
            len(results_frame.winfo_children())
        )

    try:
        ...
        img = Image.open(filepath)
        img = ImageOps.exif_transpose(img)

        img.thumbnail((180, 180))

        photo = ImageTk.PhotoImage(img)

        result_thumbnails.append(photo)

        lbl = tk.Label(
            results_frame,
            image=photo,
            cursor="hand2",
            bg="#f8fafc"
        )
        print("Thumbnail label created")

        lbl.grid(
            row=gallery_row,
            column=gallery_col,
            padx=10,
            pady=10
        )
        lbl.configure(
            bd=3,
            relief="solid"
        )
        print("\n =====Label size:=====",
                lbl.winfo_reqwidth(),
                lbl.winfo_reqheight()
        )
        
        print(
            f"Placed at row={gallery_row}, col={gallery_col}"
        )

        lbl.bind(
            "<Button-1>",
            lambda e: preview_image(filepath)
        )

        gallery_col += 1

        if gallery_col >= 4:

            gallery_col = 0
            gallery_row += 1

        results_frame.update()
        print(
            "Frame size:",
            results_frame.winfo_width(),
            results_frame.winfo_height()
        )

    except Exception as ex:

        print(ex)

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
            img = ImageOps.exif_transpose(img)

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
                    preview_image(p)
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
            (".jpg", ".jpeg", ".png", ".heic")
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

def create_search_progress():

    win = tk.Toplevel()

    win.title("Searching Photos")

    win.geometry("400x150")

    tk.Label(
        win,
        text="Searching Photos...",
        font=("Arial", 12, "bold")
    ).pack(pady=10)

    status = tk.Label(
        win,
        text="0%"
    )

    status.pack()

    progress = ttk.Progressbar(
        win,
        orient="horizontal",
        length=300,
        mode="determinate"
    )

    progress.pack(pady=20)

    return win, status, progress

def stop_searching():

    global stop_search

    stop_search = True
    
def search_database(username):
    
    global stop_search
    stop_search = False    # <-- reset the stop flag
    print("\n===== SEARCH BUTTON CLICKED =====\n")
    import sqlite3
    import pickle
    
    selfie_path = f"selfies/{username}.jpg"
    img = cv2.imread(selfie_path)
    
    if img is None:
        messagebox.showerror(
            "Error",
            f"Cannot read selfie:\n{selfie_path}"
        )
        return
    
    try:
        faces = app_face.get(img)
            
    except Exception as e:
        messagebox.showerror(
            "Search Error",
            f"Face detection failed:\n{e}"
        )
        return

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

    # Clear old results

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

    total_rows = len(rows)

    matches = 0
    
    global gallery_row
    global gallery_col

    gallery_row = 0
    gallery_col = 0

    for widget in results_frame.winfo_children():
        widget.destroy()
    
    global current_results

    current_results = []

    progress_window, status_label, progress_bar = create_search_progress()
    start_time = time.time()
    for index, row in enumerate(rows):
        if stop_search:

            break
        percent = int(
            ((index + 1) / total_rows) * 100
        )

        progress_bar["value"] = percent
        status_label.config(
        text=f"Searching Face Database\n{index + 1} / {total_rows} faces checked"
        )
        

        progress_window.update()

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
        
        print(
        f"{filename} -> Similarity: {similarity:.4f}"
        )

        if similarity > 0.45:
            print(
            f"MATCH FOUND -> {filename} ({similarity:.4f})"
            )
            matches += 1
            
            result_count_label.config(
                text=f"📸 Search Results ({matches})"
            )

            try:

                shutil.copy2(
                    filepath,
                    os.path.join(
                        "results",
                        filename
                    )
                )
                print("ADDING THUMBNAIL:", filepath)
                current_results.append(filepath)
                add_result_thumbnail(filepath)
                print("SEARCH LOOP FINISHED")

            except:
                pass
            

    conn.close()
    print("DB CLOSED")

    progress_window.destroy()
    print("PROGRESS WINDOW CLOSED")

    photos, faces = get_dashboard_stats()
    print("STATS LOADED")
  
    if stop_search:
        print("\n========== STOPPED CLICKED ==========")
        print(
            f"Search completed in {time.time() - start_time:.2f} seconds"
        )

        messagebox.showinfo(
            "Search Stopped",
            f"Search stopped by user.\n\nMatches Found: {matches}"
        )

        stop_search = False      # <-- Reset for next search

    else:
        search_time = round(time.time() - start_time, 2)
        messagebox.showinfo(
        "Search Complete",
        f"""
        Matching Photos : {matches}

        Indexed Photos : {photos}
        Indexed Faces : {faces}
        Search Time : {search_time} sec
        """
        )
      
# Login User
def login():
    print("LOGIN FUNCTION STARTED")
    username = user_entry.get()
    password = pass_entry.get()

    try:

        response = requests.post(
            f"{API_URL}/login",
            json={
                "username": username,
                "password": password
            }
        )

        data = response.json()

    except Exception as e:

        messagebox.showerror(
            "Server Error",
            f"Cannot connect to server.\n\n{e}"
        )
        return

    if not data["success"]:

        messagebox.showerror(
            "Error",
            data["message"]
        )
        return

    actual_username = data["username"]
    selfie_taken = data["selfie_taken"]
    role = data["role"]

    print("LOGIN ROLE =", role)

    if selfie_taken == 0:

        messagebox.showinfo(
            "First Login",
            "Please capture your selfie"
        )

        capture_selfie(actual_username)

        # We'll move this update to the server in the next step
    requests.post(
    f"{API_URL}/selfie-complete",
    json={
        "username": actual_username
    }
    )

    root.withdraw()
    open_dashboard(actual_username, role)
    

# UI
# ---------------------------
# MODERN LOGIN SCREEN
# ---------------------------

root = tk.Tk()

root.title("FaceFinder AI")
root.state("zoomed")
root.configure(bg="#f0f4f8")

# Title

tk.Label(
    root,
    text="🔍 FaceFinder",
    font=("Arial", 24, "bold"),
    bg="#f0f4f8",
    fg="#1e3a8a"
).pack(pady=(30, 5))

tk.Label(
    root,
    text="Find Yourself Instantly",
    font=("Arial", 11),
    bg="#f0f4f8",
    fg="gray"
).pack(pady=(0, 20))

# Login Card

card = tk.Frame(
    root,
    bg="white",
    bd=1,
    relief="solid"
)

card.pack(
    padx=40,
    pady=10,
    fill="both",
    expand=False
)

# Username

tk.Label(
    card,
    text="Username",
    font=("Arial", 11),
    bg="white"
).pack(
    anchor="w",
    padx=20,
    pady=(20, 5)
)

user_entry = tk.Entry(
    card,
    font=("Arial", 12),
    width=30
)

user_entry.pack(
    padx=20,
    pady=(0, 15)
)

# Password

tk.Label(
    card,
    text="Password",
    font=("Arial", 11),
    bg="white"
).pack(
    anchor="w",
    padx=20,
    pady=(0, 5)
)

pass_entry = tk.Entry(
    card,
    font=("Arial", 12),
    width=30,
    show="*"
)

pass_entry.pack(
    padx=20,
    pady=(0, 20)
)

# Login Button

tk.Button(
    card,
    text="LOGIN",
    command=login,
    font=("Arial", 11, "bold"),
    bg="#2563eb",
    fg="white",
    width=20,
    height=2
).pack(pady=(0, 10))

# Register Button

tk.Button(
    card,
    text="REGISTER",
    command=register,
    font=("Arial", 10),
    bg="#e5e7eb",
    width=20
).pack(pady=(0, 20))

# Footer

tk.Label(
    root,
    text="FaceFinder AI • Powered by RD Creation",
    font=("Arial", 10),
    bg="#f0f4f8",
    fg="gray"
).pack(pady=20)

test_server()
root.mainloop()
