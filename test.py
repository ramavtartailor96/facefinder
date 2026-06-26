import os
import sys
import time
import shutil
import pickle
import threading
import sqlite3
import numpy as np
import cv2
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageOps
from insightface.app import FaceAnalysis

# --- Global Configurations & States ---
stop_search = False
current_results = []
current_index = 0
result_thumbnails = []
gallery_row = 0
gallery_col = 0
results_frame = None
result_count_label = None

# Ensure required local directories exist relative to execution path
BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
SELFIES_DIR = os.path.join(BASE_DIR, "selfies")
RESULTS_DIR = os.path.join(BASE_DIR, "results")

os.makedirs(SELFIES_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

# Initialize AI Model
try:
    app_face = FaceAnalysis()
    app_face.prepare(ctx_id=-1)  # Force CPU usage (-1) for generic compatibility across client PCs
except Exception as e:
    print(f"Model initialization error: {e}")

# Initialize User Database
USERS_DB = os.path.join(BASE_DIR, "users.db")
conn = sqlite3.connect(USERS_DB, check_same_thread=False)
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

INDEX_DB = os.path.join(BASE_DIR, "face_index.db")

# --- Authentication Core ---
def register():
    username = user_entry.get().strip()
    password = pass_entry.get().strip()

    if not username or not password:
        messagebox.showerror("Error", "Enter username and password")
        return

    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        messagebox.showinfo("Success", "User Registered Successfully")
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "User already exists")

def login():
    username = user_entry.get().strip()
    password = pass_entry.get().strip()

    cursor.execute("SELECT * FROM users WHERE LOWER(username)=LOWER(?) AND password=?", (username, password))
    user = cursor.fetchone()

    if user:
        actual_username = user[1]
        selfie_taken = user[3]

        if selfie_taken == 0:
            messagebox.showinfo("First Login", "Please capture your selfie")
            if capture_selfie(actual_username):
                cursor.execute("UPDATE users SET selfie_taken=1 WHERE username=?", (actual_username,))
                conn.commit()
                root.withdraw()
                open_dashboard(actual_username)
        else:
            root.withdraw()
            open_dashboard(actual_username)
    else:
        messagebox.showerror("Error", "Invalid username or password")

def capture_selfie(username):
    cam = cv2.VideoCapture(0)
    captured = False
    
    if not cam.isOpened():
        messagebox.showerror("Error", "Could not access system camera.")
        return False

    while True:
        ret, frame = cam.read()
        if not ret:
            break

        cv2.imshow("Press SPACE to Capture / ESC to Close", frame)
        key = cv2.waitKey(1)

        if key == 27:  # ESC
            break
        elif key == 32:  # SPACE
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

            if len(faces) != 1:
                messagebox.showerror("Error", f"Expected exactly 1 face, found {len(faces)}. Try again.")
                continue

            filename = os.path.join(SELFIES_DIR, f"{username}.jpg")
            cv2.imwrite(filename, frame)
            captured = True
            break

    cam.release()
    cv2.destroyAllWindows()
    if captured:
        messagebox.showinfo("Success", "Selfie Saved Successfully")
    return captured

# --- Indexing Operations ---
def create_progress_window(title_text, dynamic_text):
    win = tk.Toplevel()
    win.title(title_text)
    win.geometry("450x180")
    win.resizable(False, False)
    win.grab_set()  # Modal Window
    
    tk.Label(win, text=dynamic_text, font=("Arial", 12, "bold")).pack(pady=10)
    status_label = tk.Label(win, text="Starting...")
    status_label.pack()

    progress_bar = ttk.Progressbar(win, orient="horizontal", length=350, mode="determinate")
    progress_bar.pack(pady=15)

    percent_label = tk.Label(win, text="0%")
    percent_label.pack()

    return win, status_label, progress_bar, percent_label

def build_index_thread():
    folder = filedialog.askdirectory()
    if not folder:
        return
    # Run the heavy indexing process inside a background thread
    threading.Thread(target=_execute_indexing, args=(folder,), daemon=True).start()

def _execute_indexing(folder):
    idx_conn = sqlite3.connect(INDEX_DB)
    idx_cursor = idx_conn.cursor()
    idx_cursor.execute("""
    CREATE TABLE IF NOT EXISTS faces (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT,
        filepath TEXT UNIQUE,
        embedding BLOB
    )
    """)
    idx_conn.commit()

    valid_exts = (".jpg", ".jpeg", ".png")
    all_files = os.listdir(folder)
    photo_files = [f for f in all_files if f.lower().endswith(valid_exts)]
    total_photos = len(photo_files)

    if total_photos == 0:
        messagebox.showinfo("Empty", "No images found in the selected folder.")
        idx_conn.close()
        return

    photo_count = 0
    skipped_count = 0

    win, status_lbl, p_bar, pct_lbl = create_progress_window("Building Face Index", "Indexing Folder Assets...")

    for processed, filename in enumerate(photo_files, 1):
        percent = int((processed / total_photos) * 100)
        
        # Safe thread update using root.after or direct win.update for quick GUI refreshes
        win.after(0, lambda p=percent, pr=processed: [
            p_bar.config(value=p),
            pct_lbl.config(text=f"{p}%"),
            status_lbl.config(text=f"Processing {pr} / {total_photos}")
        ])

        filepath = os.path.normpath(os.path.join(folder, filename))
        idx_cursor.execute("SELECT filepath FROM faces WHERE filepath=?", (filepath,))
        if idx_cursor.fetchone():
            skipped_count += 1
            continue

        image = cv2.imread(filepath)
        if image is None:
            continue

        height, width = image.shape[:2]
        if width > 1200:
            scale = 1200 / width
            image = cv2.resize(image, None, fx=scale, fy=scale)

        try:
            faces = app_face.get(image)
            for face in faces:
                embedding = pickle.dumps(face.embedding)
                idx_cursor.execute(
                    "INSERT OR IGNORE INTO faces (filename, filepath, embedding) VALUES (?, ?, ?)",
                    (filename, filepath, embedding)
                )
            idx_conn.commit()
            photo_count += 1
        except Exception as ex:
            print(f"Error extracting metadata from {filename}: {ex}")

    idx_conn.close()
    win.after(0, win.destroy)
    messagebox.showinfo("Index Complete", f"New photos indexed: {photo_count}\nAlready indexed: {skipped_count}")

# --- Search Logic Implementation ---
def stop_searching():
    global stop_search
    stop_search = True

def search_database_thread(username):
    global stop_search
    stop_search = False
    threading.Thread(target=_execute_search, args=(username,), daemon=True).start()

def _execute_search(username):
    global gallery_row, gallery_col, current_results, result_thumbnails
    
    selfie_path = os.path.normpath(os.path.join(SELFIES_DIR, f"{username}.jpg"))
    if not os.path.exists(selfie_path):
        messagebox.showerror("Error", "Your base identifier selfie file is missing.")
        return

    img = cv2.imread(selfie_path)
    faces = app_face.get(img)
    if len(faces) == 0:
        messagebox.showerror("Error", "No clean anchor face detected in your configuration profile selfie.")
        return

    selfie_embedding = faces[0].embedding

    # Flush old structural items
    for file in os.listdir(RESULTS_DIR):
        try:
            os.remove(os.path.join(RESULTS_DIR, file))
        except:
            pass

    idx_conn = sqlite3.connect(INDEX_DB)
    idx_cursor = idx_conn.cursor()
    try:
        idx_cursor.execute("SELECT filename, filepath, embedding FROM faces")
        rows = idx_cursor.fetchall()
    except sqlite3.OperationalError:
        messagebox.showerror("Error", "The Face Database index does not exist yet. Please build it first.")
        idx_conn.close()
        return

    total_rows = len(rows)
    if total_rows == 0:
        messagebox.showinfo("Info", "No structured profile elements indexed inside your main database context.")
        idx_conn.close()
        return

    gallery_row = 0
    gallery_col = 0
    current_results = []
    result_thumbnails.clear()

    for widget in results_frame.winfo_children():
        widget.destroy()

    win, status_lbl, p_bar, pct_lbl = create_progress_window("Searching Pipeline", "Comparing Matrix Alignments...")
    matches = 0
    start_time = time.time()

    for index, row in enumerate(rows):
        if stop_search:
            break

        percent = int(((index + 1) / total_rows) * 100)
        win.after(0, lambda p=percent, i=index: [
            p_bar.config(value=p),
            pct_lbl.config(text=f"{p}%"),
            status_lbl.config(text=f"Checked {i+1} / {total_rows} elements")
        ])

        filename, filepath, raw_embedding = row
        embedding = pickle.loads(raw_embedding)

        similarity = np.dot(selfie_embedding, embedding) / (
            np.linalg.norm(selfie_embedding) * np.linalg.norm(embedding)
        )

        if similarity > 0.45:
            matches += 1
            result_count_label.config(text=f"📸 Search Results ({matches})")
            
            try:
                shutil.copy2(filepath, os.path.join(RESULTS_DIR, filename))
                current_results.append(filepath)
                # Safeguard running graphic allocation additions via thread-safe injection
                results_frame.after(0, lambda path=filepath: add_result_thumbnail(path))
            except Exception as e:
                print(f"Error copying match: {e}")

    idx_conn.close()
    win.after(0, win.destroy)

    search_time = round(time.time() - start_time, 2)
    if stop_search:
        messagebox.showinfo("Search Interrupted", f"Halted operations.\n\nMatches Contextualized: {matches}")
    else:
        # Get quick statistics count values 
        photos, faces_count = 0, 0
        try:
            c = sqlite3.connect(INDEX_DB).cursor()
            photos = c.execute("SELECT COUNT(DISTINCT filepath) FROM faces").fetchone()[0]
            faces_count = c.execute("SELECT COUNT(*) FROM faces").fetchone()[0]
        except:
            pass
        
        messagebox.showinfo("Search Complete", f"Matches Matched: {matches}\nTotal Cataloged: {photos}\nProcess Duration: {search_time} sec")

# --- UI Render Components & Subroutines ---
def add_result_thumbnail(filepath):
    global gallery_row, gallery_col
    try:
        img = Image.open(filepath)
        img = ImageOps.exif_transpose(img)
        img.thumbnail((160, 160))
        photo = ImageTk.PhotoImage(img)

        result_thumbnails.append(photo)
        lbl = tk.Label(results_frame, image=photo, cursor="hand2", bg="#f8fafc")
        lbl.grid(row=gallery_row, column=gallery_col, padx=10, pady=10)
        lbl.bind("<Button-1>", lambda e, p=filepath: preview_image(p))

        gallery_col += 1
        if gallery_col >= 4:
            gallery_col = 0
            gallery_row += 1
    except Exception as ex:
        print(f"Thumbnail load crash: {ex}")

def preview_image(filepath):
    global current_results, current_index
    try:
        current_index = current_results.index(filepath)
    except:
        current_index = 0

    preview = tk.Toplevel()
    preview.title(os.path.basename(filepath))
    preview.state("zoomed")
    preview.configure(bg="black")

    image_label = tk.Label(preview, bg="black")
    image_label.pack(expand=True, fill="both")

    def show_image(index):
        path = current_results[index]
        img = Image.open(path)
        img = ImageOps.exif_transpose(img)
        
        screen_w = preview.winfo_screenwidth()
        screen_h = preview.winfo_screenheight()
        img.thumbnail((screen_w - 100, screen_h - 100))

        photo = ImageTk.PhotoImage(img)
        image_label.config(image=photo)
        image_label.image = photo
        preview.title(os.path.basename(path))

    preview.bind("<Right>", lambda e: [change_index(1), show_image(current_index)])
    preview.bind("<Left>", lambda e: [change_index(-1), show_image(current_index)])
    preview.bind("<Escape>", lambda e: preview.destroy())

    def change_index(step):
        global current_index
        if current_results:
            current_index = (current_index + step) % len(current_results)

    show_image(current_index)

def open_results_folder():
    os.startfile(RESULTS_DIR)

def logout(dashboard):
    dashboard.destroy()
    root.deiconify()
    root.state("zoomed")

def open_dashboard(actual_username):
    global results_frame, result_count_label
    dashboard = tk.Toplevel()
    dashboard.title("FaceFinder Dashboard")
    dashboard.state("zoomed")
    dashboard.configure(bg="#f0f4f8")

    logout_frame = tk.Frame(dashboard, bg="#f0f4f8")
    logout_frame.pack(fill="x", pady=10, padx=20)

    tk.Button(logout_frame, text="Logout", font=("Arial", 11, "bold"), bg="#dc2626", fg="white",
              relief="flat", padx=15, pady=5, command=lambda: logout(dashboard)).pack(side="right")

    tk.Label(dashboard, text="🔍 FaceFinder Dashboard", font=("Arial", 22, "bold"), bg="#f0f4f8", fg="#1e3a8a").pack(pady=(20, 5))
    tk.Label(dashboard, text=f"Welcome, {actual_username}", font=("Arial", 12), bg="#f0f4f8", fg="gray").pack()

    card = tk.Frame(dashboard, bg="white", bd=1, relief="solid")
    card.pack(padx=40, pady=30, fill="both", expand=True)

    main_frame = tk.Frame(card, bg="white")
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)

    left_frame = tk.Frame(main_frame, bg="white")
    left_frame.pack(side="left", fill="y", padx=20, pady=20)

    tk.Button(left_frame, text="📂\nBuild / Update Index", font=("Arial", 14, "bold"), bg="#2563eb", fg="white", width=20, height=3, command=build_index_thread).pack(pady=10)
    tk.Button(left_frame, text="📸\nSearch My Photos", font=("Arial", 14, "bold"), bg="#16a34a", fg="white", width=20, height=3, command=lambda: search_database_thread(actual_username)).pack(pady=10)
    tk.Button(left_frame, text="⛔\nStop Search", font=("Arial", 14, "bold"), bg="#dc2626", fg="white", width=20, height=3, command=stop_searching).pack(pady=10)
    tk.Button(left_frame, text="📁\nOpen Results Folder", font=("Arial", 14, "bold"), width=20, height=3, command=open_results_folder).pack(pady=10)

    right_frame = tk.Frame(main_frame, bg="white")
    right_frame.pack(side="left", fill="both", expand=True, padx=20)
    
    result_count_label = tk.Label(right_frame, text="📸 Search Results (0)", font=("Arial", 18, "bold"), bg="white", fg="#1e3a8a")
    result_count_label.pack(pady=10)

    results_container = tk.Frame(right_frame, bg="white")
    results_container.pack(fill="both", expand=True, padx=10, pady=10)

    results_canvas = tk.Canvas(results_container, bg="#f8fafc")
    results_scrollbar = tk.Scrollbar(results_container, orient="vertical", command=results_canvas.yview)
    results_canvas.configure(yscrollcommand=results_scrollbar.set)

    results_scrollbar.pack(side="right", fill="y")
    results_canvas.pack(side="left", fill="both", expand=True)

    results_frame = tk.Frame(results_canvas, bg="#f8fafc")
    results_canvas.create_window((0, 0), window=results_frame, anchor="nw")
    results_frame.bind("<Configure>", lambda e: results_canvas.configure(scrollregion=results_canvas.bbox("all")))

    results_canvas.bind_all("<MouseWheel>", lambda event: results_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units"))
    tk.Label(results_frame, text="No results loaded yet", font=("Arial", 12), bg="#f8fafc", fg="gray").pack(pady=50)

# --- Primary Login Interface Configuration Layout ---
root = tk.Tk()
root.title("FaceFinder AI")
root.state("zoomed")
root.configure(bg="#f0f4f8")

tk.Label(root, text="🔍 FaceFinder", font=("Arial", 24, "bold"), bg="#f0f4f8", fg="#1e3a8a").pack(pady=(30, 5))
tk.Label(root, text="Find Yourself Instantly", font=("Arial", 11), bg="#f0f4f8", fg="gray").pack(pady=(0, 20))

card = tk.Frame(root, bg="white", bd=1, relief="solid")
card.pack(padx=40, pady=10, fill="both", expand=False)

tk.Label(card, text="Username", font=("Arial", 11), bg="white").pack(anchor="w", padx=20, pady=(20, 5))
user_entry = tk.Entry(card, font=("Arial", 12), width=30)
user_entry.pack(padx=20, pady=(0, 15))

tk.Label(card, text="Password", font=("Arial", 11), bg="white").pack(anchor="w", padx=20, pady=(0, 5))
pass_entry = tk.Entry(card, font=("Arial", 12), width=30, show="*")
pass_entry.pack(padx=20, pady=(0, 20))

tk.Button(card, text="LOGIN", command=login, font=("Arial", 11, "bold"), bg="#2563eb", fg="white", width=20, height=2).pack(pady=(0, 10))
tk.Button(card, text="REGISTER", command=register, font=("Arial", 10), bg="#e5e7eb", width=20).pack(pady=(0, 20))

tk.Label(root, text="FaceFinder AI • Powered by RD Creation", font=("Arial", 9), bg="#f0f4f8", fg="gray").pack(pady=20)

root.mainloop()