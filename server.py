import bcrypt
from fastapi import FastAPI
from pydantic import BaseModel
import sqlite3

app = FastAPI()

# Create database and users table if they don't exist
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    selfie_taken INTEGER DEFAULT 0,
    role TEXT DEFAULT 'user'
)
""")

conn.commit()
conn.close()


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


@app.get("/")
def home():
    return {"message": "FaceFinder API Running"}


@app.post("/login")
def login(data: LoginRequest):

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute(
    """
    SELECT id, username, password, selfie_taken, role
    FROM users
    WHERE LOWER(username)=LOWER(?)
    """,
    (data.username,)
    )

    user = cursor.fetchone()

    conn.close()

    if user is None:
        return {
            "success": False,
            "message": "Invalid username or password"
        }

    stored_password = user[2]

    if not bcrypt.checkpw(
        data.password.encode(),
        stored_password.encode()
    ):
        return {
            "success": False,
            "message": "Invalid username or password"
        }

    return {
        "success": True,
        "username": user[1],
        "selfie_taken": user[3],
        "role": user[4]
    }
class SelfieUpdate(BaseModel):
    username: str
@app.post("/selfie-complete")
def selfie_complete(data: SelfieUpdate):

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE users
        SET selfie_taken=1
        WHERE username=?
        """,
        (data.username,)
    )

    conn.commit()
    conn.close()

    return {
        "success": True
    }
    

class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str
    
@app.post("/register")
def register_user(data: RegisterRequest):

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    try:

        hashed_password = bcrypt.hashpw(
            data.password.encode(),
            bcrypt.gensalt()
        ).decode()

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
                data.username,
                hashed_password,
                0,
                data.role,
            )
        )

        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": "User Registered Successfully"
        }

    except:

        conn.close()

        return {
            "success": False,
            "message": "User already exists"
        }
        
class UsernameRequest(BaseModel):
    username: str


class ResetPasswordRequest(BaseModel):
    username: str
    password: str
    
@app.get("/users")
def get_users():

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT username, role
        FROM users
        ORDER BY username
        """
    )

    rows = cursor.fetchall()

    conn.close()

    return rows

@app.post("/delete-user")
def delete_user_api(data: UsernameRequest):

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM users
        WHERE username=?
        """,
        (data.username,)
    )

    conn.commit()
    conn.close()

    return {"success": True}

@app.post("/reset-password")
def reset_password_api(data: ResetPasswordRequest):

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    hashed_password = bcrypt.hashpw(
        data.password.encode(),
        bcrypt.gensalt()
    ).decode()

    cursor.execute(
        """
        UPDATE users
        SET password=?
        WHERE username=?
        """,
        (
            hashed_password,
            data.username
        )
    )

    conn.commit()
    conn.close()

    return {"success": True}

@app.post("/migrate-passwords")
def migrate_passwords():

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT username, password
        FROM users
        """
    )

    users = cursor.fetchall()

    updated = 0

    for username, password in users:

        # Skip if already hashed
        if password.startswith("$2b$"):
            continue

        hashed = bcrypt.hashpw(
            password.encode(),
            bcrypt.gensalt()
        ).decode()

        cursor.execute(
            """
            UPDATE users
            SET password=?
            WHERE username=?
            """,
            (
                hashed,
                username
            )
        )

        updated += 1

    conn.commit()
    conn.close()

    return {
        "updated_users": updated
    }
